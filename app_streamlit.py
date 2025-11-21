import base64
from datetime import datetime

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

from core.retrieval import load_services, retrieve_services
from core.handout_generator import generate_pdf
from core.logger import log_interaction
from core.pdf_generator import generate_pdf


# ---------- Load data ----------
SERVICES_DF = load_services()

# ---------- Page config ----------
st.set_page_config(
    page_title="DISSA – Digital Inclusion System of Services Available",
    layout="wide",
)

# ---------- Session state ----------
if "step" not in st.session_state:
    st.session_state["step"] = "form"   # "form" or "handout"

defaults = {
    "visitor_context": None,        # final context for handout
    "visitor_context_form": None,   # context when generating services
    "kept_services": [],
    "removed_ids": [],
    "handout_text": "",
    "services_for_review": [],
    "review_ready": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- Sidebar: mode + instructions ----------
with st.sidebar:
    mode = st.radio(
        "Mode",
        ["Front desk tool", "Analytics dashboard"],
        index=0,
    )

    if mode == "Front desk tool":
        st.markdown("### How to use")
        if st.session_state["step"] == "form":
            st.markdown(
                """
                1. Select the visitor's basic context.
                2. Click the tiles that match their main needs.
                3. Click **Generate service list**.
                4. Review services and uncheck any that are not appropriate.
                5. Click **Confirm & generate handout** to move to the next page.
                """
            )
        else:
            st.markdown(
                """
                - Review the handout text.
                - Print or copy it for the visitor.
                - Click **Start new visitor** to return to the first screen.
                """
            )
    else:
        st.markdown("### Analytics dashboard")
        st.caption(
            "View anonymous aggregates of DISSA usage: top needs, top services, "
            "and visitor context patterns over time."
        )

# ---------- Light custom styling ----------
st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .big-title {
        font-size: 2.3rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        color: #555;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .section-title {
        margin-top: 1.5rem;
        margin-bottom: 0.4rem;
    }
    .dissa-footer {
        text-align: center;
        font-size: 0.8rem;
        color: #777777;
        margin-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Common header ----------
st.markdown(
    '<div class="big-title">DISSA – Digital Inclusion System of Services Available</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Support tool for NFCM front desk staff. Helps match visitors to local services and print a clear handout.</div>',
    unsafe_allow_html=True,
)


# =====================================================================
# HELPER: load interactions from Google Sheets
# =====================================================================
def load_interactions_from_sheets() -> pd.DataFrame:
    """Return interactions log as a DataFrame, using service-account auth."""
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client = gspread.authorize(creds)

    raw = st.secrets["sheets"]["sheet_id"].strip()
    if "/d/" in raw:
        key = raw.split("/d/")[1].split("/")[0]
    else:
        key = raw

    sh = client.open_by_key(key)
    ws = sh.worksheet("interactions")
    records = ws.get_all_records()
    return pd.DataFrame(records)


# =====================================================================
# MODE 1: FRONT DESK TOOL
# =====================================================================
if mode == "Front desk tool":

    # STEP 1: FORM + SERVICE REVIEW
    if st.session_state["step"] == "form":

        # ----- Visitor context -----
        st.markdown('<h4 class="section-title">Visitor Context</h4>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            age_group = st.selectbox(
                "Age group",
                ["Under 18", "18-29", "30-54", "55+"],
                index=1,
            )

        with col2:
            language = st.selectbox(
                "Preferred language (for now, display language)",
                ["Cree", "Inuktitut", "English", "French", "Other"],
                index=0,
            )

        housing_status = st.selectbox(
            "Housing situation (optional)",
            ["Not specified", "Homeless / unstably housed", "Stably housed", "Shelter"],
            index=0,
        )

        # ----- Key needs as tiles -----
        st.markdown('<h4 class="section-title">Key needs</h4>', unsafe_allow_html=True)
        st.caption(
            "Click the tiles that match what the visitor is looking for. "
            "You can select more than one."
        )

        NEED_OPTIONS = [
            {"label": "Food",                 "value": "food",           "emoji": "🍽️"},
            {"label": "Health & Wellness",    "value": "health",         "emoji": "🩺"},
            {"label": "Mental Health",        "value": "mental_health",  "emoji": "🧠"},
            {"label": "Housing & Shelter",    "value": "housing",        "emoji": "🏠"},
            {"label": "Clothes & Hygiene",    "value": "clothing",       "emoji": "🧥"},
            {"label": "Work / Employment",    "value": "employment",     "emoji": "💼"},
            {"label": "Family & Children",    "value": "family_support", "emoji": "👨‍👩‍👧"},
            {"label": "Culture / Community",  "value": "culture",        "emoji": "🌿"},
        ]

        selected_needs = []
        cols_per_row = 3
        for i in range(0, len(NEED_OPTIONS), cols_per_row):
            row = NEED_OPTIONS[i : i + cols_per_row]
            cols = st.columns(len(row))
            for col, opt in zip(cols, row):
                with col:
                    default_selected = opt["value"] in ["food"]  # pre-select food
                    checked = st.checkbox(
                        f"{opt['emoji']}  {opt['label']}",
                        key=f"need_{opt['value']}",
                        value=default_selected,
                    )
                    if checked:
                        selected_needs.append(opt["value"])

        st.write("")
        generate_clicked = st.button("Generate service list")

        if generate_clicked:
            if not selected_needs:
                st.warning("Please select at least one need by clicking the tiles above.")
            else:
                visitor_context = {
                    "age_group": age_group,
                    "language": language,
                    "housing_status": housing_status,
                    "needs": selected_needs,
                }

                services = retrieve_services(
                    SERVICES_DF, selected_needs, language, age_group
                )

                if not services:
                    st.error("No matching services found. Try changing needs or language.")
                    st.session_state["review_ready"] = False
                    st.session_state["services_for_review"] = []
                else:
                    st.session_state["review_ready"] = True
                    st.session_state["services_for_review"] = services
                    st.session_state["visitor_context_form"] = visitor_context

        # ---- Review section ----
        if st.session_state["review_ready"] and st.session_state["services_for_review"]:
            services = st.session_state["services_for_review"]
            visitor_context = st.session_state["visitor_context_form"]

            st.success(f"Found {len(services)} matching services. Review below.")
            st.markdown("### Review services")
            st.write(
                "Uncheck any services that do not fit this visitor before generating the handout."
            )

            kept_services = []
            removed_ids = []

            for svc in services:
                label = (
                    f"**{svc['name']}** – {svc['description']}  \n"
                    f"Hours: {svc['hours_today']} · Address: {svc['address']}"
                )
                keep = st.checkbox(label, value=True, key=f"svc_{svc['id']}")
                if keep:
                    kept_services.append(svc)
                else:
                    removed_ids.append(svc["id"])

            confirm_clicked = st.button("Confirm & generate handout")

            if confirm_clicked:
                if not kept_services:
                    st.warning("At least one service should be selected.")
                else:
                    handout_text = generate_handout(visitor_context, kept_services)
                    log_interaction(visitor_context, kept_services, removed_ids)

                    st.session_state["visitor_context"] = visitor_context
                    st.session_state["kept_services"] = kept_services
                    st.session_state["removed_ids"] = removed_ids
                    st.session_state["handout_text"] = handout_text

                    st.session_state["review_ready"] = False
                    st.session_state["services_for_review"] = []
                    st.session_state["step"] = "handout"

                    st.rerun()

    # STEP 2: HANDOUT PAGE
    else:  # st.session_state["step"] == "handout"
        vc = st.session_state["visitor_context"]
        handout_text = st.session_state["handout_text"]

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        st.markdown("### Handout ready")
        st.caption(f"Generated on: **{now_str}**")

        if vc:
            with st.expander("Visitor context summary", expanded=True):
                st.write(
                    f"- Age group: **{vc['age_group']}**  \n"
                    f"- Language (display): **{vc['language']}**  \n"
                    f"- Housing: **{vc['housing_status']}**  \n"
                    f"- Key needs: **{', '.join(vc['needs'])}**"
                )

        st.markdown("### Handout text (formatted)")
        st.markdown(handout_text)

        # PDF generation + download
        # pdf_bytes = generate_pdf(handout_text, vc)
        pdf_bytes = generate_pdf(
        handout_text,
        vc,
        st.session_state.get("kept_services", []),
        )

        st.download_button(
            label="📄 Download PDF",
            data=pdf_bytes,
            file_name="NFCM_handout.pdf",
            mime="application/pdf",
        )

        # Inline preview (best-effort)
        try:
            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
            pdf_iframe = f"""
                <iframe
                    src="data:application/pdf;base64,{b64_pdf}"
                    width="100%"
                    height="600px"
                    style="border: none;"
                    type="application/pdf"
                ></iframe>
            """
            st.markdown("### Preview & print")
            st.markdown(pdf_iframe, unsafe_allow_html=True)
        except Exception:
            st.caption(
                "Preview could not be rendered in the browser. "
                "Use the **Download PDF** button and print from your PDF viewer."
            )

        st.markdown("### Plain text (for copy/paste)")
        st.text_area(
            "You can copy this text into a Word / Google Doc or print directly:",
            value=handout_text,
            height=260,
        )

        st.write("")
        if st.button("Start new visitor"):
            st.session_state.clear()
            st.session_state["step"] = "form"
            st.rerun()


# =====================================================================
# MODE 2: ANALYTICS DASHBOARD
# =====================================================================
else:
    st.subheader("Analytics dashboard – anonymous usage trends")

    try:
        df = load_interactions_from_sheets()
    except Exception as e:
        st.error("Could not load analytics data from Google Sheets.")
        st.caption(str(e))
    else:
        if df.empty:
            st.info(
                "No interactions have been logged yet. "
                "As front desk staff generate handouts, data will appear here."
            )
        else:
            # ---------- Timestamp + time filter ----------
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

                st.markdown("#### Time filter")
                period = st.selectbox(
                    "Show data for:",
                    ["All time", "Last 7 days", "Last 30 days", "Last 90 days"],
                    index=2,
                )

                if period == "All time":
                    filtered_df = df.copy()
                else:
                    days_lookup = {
                        "Last 7 days": 7,
                        "Last 30 days": 30,
                        "Last 90 days": 90,
                    }
                    days = days_lookup[period]
                    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
                    filtered_df = df[df["timestamp"] >= cutoff].copy()
            else:
                filtered_df = df.copy()

            if filtered_df.empty:
                st.info(
                    "No interactions match the selected time period. "
                    "Try a wider range or 'All time'."
                )
            else:
                # Top-level KPIs (using filtered data)
                total_interactions = len(filtered_df)
                if "timestamp" in filtered_df.columns:
                    date_min = filtered_df["timestamp"].min()
                    date_max = filtered_df["timestamp"].max()
                else:
                    date_min = date_max = None

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total handouts generated", total_interactions)
                with col2:
                    st.metric(
                        "First interaction in view",
                        date_min.strftime("%Y-%m-%d") if date_min is not None else "N/A",
                    )
                with col3:
                    st.metric(
                        "Most recent in view",
                        date_max.strftime("%Y-%m-%d") if date_max is not None else "N/A",
                    )

                # Download filtered CSV
                csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download filtered data (CSV)",
                    data=csv_bytes,
                    file_name="dissa_interactions_filtered.csv",
                    mime="text/csv",
                )

                st.markdown("---")

                # --- Top needs ---
                st.markdown("### Top needs selected")

                if "needs" in filtered_df.columns:
                    needs_df = filtered_df.copy()
                    needs_df["needs_list"] = (
                        needs_df["needs"].fillna("").astype(str).str.split(";")
                    )
                    needs_exploded = needs_df.explode("needs_list")
                    needs_exploded = needs_exploded[
                        needs_exploded["needs_list"] != ""
                    ]

                    if needs_exploded.empty:
                        st.caption("No needs data recorded yet.")
                    else:
                        needs_counts = (
                            needs_exploded["needs_list"].value_counts().head(10)
                        )

                        col_left, col_right = st.columns([2, 1])
                        with col_left:
                            st.bar_chart(needs_counts)
                        with col_right:
                            st.write("Top needs (by count):")
                            st.table(needs_counts.to_frame("count"))
                else:
                    st.caption("Column 'needs' not found in sheet.")

                st.markdown("---")

                # --- Top services used ---
                st.markdown("### Top services included in handouts")

                if "service_ids_kept" in filtered_df.columns:
                    svc_df = filtered_df.copy()
                    svc_df["service_ids_kept_list"] = (
                        svc_df["service_ids_kept"].fillna("").astype(str).str.split(";")
                    )
                    svc_exploded = svc_df.explode("service_ids_kept_list")
                    svc_exploded = svc_exploded[
                        svc_exploded["service_ids_kept_list"] != ""
                    ]

                    if svc_exploded.empty:
                        st.caption("No services have been logged yet.")
                    else:
                        svc_exploded["service_ids_kept_list"] = pd.to_numeric(
                            svc_exploded["service_ids_kept_list"], errors="coerce"
                        )
                        svc_exploded = svc_exploded.dropna(
                            subset=["service_ids_kept_list"]
                        )

                        id_to_name = {
                            int(row["id"]): row["name"]
                            for _, row in SERVICES_DF.iterrows()
                        }

                        svc_exploded["service_name"] = svc_exploded[
                            "service_ids_kept_list"
                        ].map(id_to_name)
                        svc_exploded = svc_exploded.dropna(subset=["service_name"])

                        svc_counts = (
                            svc_exploded["service_name"].value_counts().head(10)
                        )

                        col_left2, col_right2 = st.columns([2, 1])
                        with col_left2:
                            st.bar_chart(svc_counts)
                        with col_right2:
                            st.write("Top services (by count):")
                            st.table(svc_counts.to_frame("count"))
                else:
                    st.caption("Column 'service_ids_kept' not found in sheet.")

                st.markdown("---")

                # --- Context breakdown ---
                st.markdown("### Context breakdown")

                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    if "housing_status" in filtered_df.columns:
                        st.markdown("**By housing situation**")
                        housing_counts = filtered_df["housing_status"].value_counts()
                        st.bar_chart(housing_counts)
                    else:
                        st.caption("Column 'housing_status' not found.")

                with col_h2:
                    if "age_group" in filtered_df.columns:
                        st.markdown("**By age group**")
                        age_counts = filtered_df["age_group"].value_counts()
                        st.bar_chart(age_counts)
                    else:
                        st.caption("Column 'age_group' not found.")

                st.markdown("#### Raw log preview (first 20 rows)")
                st.dataframe(filtered_df.head(20))


# ---------- Footer ----------
st.markdown("---")
st.markdown(
    '<div class="dissa-footer">'
    'Prototype for the Native Friendship Centre of Montreal (NFCM), '
    'in collaboration with Centraide of Greater Montreal – DISSA MVP.'
    '</div>',
    unsafe_allow_html=True,
)
