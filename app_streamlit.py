import streamlit as st
from datetime import datetime
import base64
import streamlit.components.v1 as components  # ok if unused
import pandas as pd
import os
from core.google_sheets import load_interactions_df


from core.retrieval import load_services, retrieve_services
from core.handout_generator import generate_handout
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

# for passing data between actions
defaults = {
    "visitor_context": None,        # final context for handout
    "visitor_context_form": None,   # context used when generating services
    "kept_services": [],
    "removed_ids": [],
    "handout_text": "",
    "services_for_review": [],
    "review_ready": False,          # did we already generate the service list?
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
# MODE 1: FRONT DESK TOOL (your existing flow)
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
            "Click the tiles that match what the visitor is looking for. You can select more than one."
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

        # ---- When "Generate service list" is clicked, compute & store to session ----
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

                services = retrieve_services(SERVICES_DF, selected_needs, language, age_group)

                if not services:
                    st.error("No matching services found. Try changing needs or language.")
                    st.session_state["review_ready"] = False
                    st.session_state["services_for_review"] = []
                else:
                    # store for later runs
                    st.session_state["review_ready"] = True
                    st.session_state["services_for_review"] = services
                    st.session_state["visitor_context_form"] = visitor_context

        # ---- Show review section whenever we have services stored ----
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
                    # Debug: see how many services go into the handout
                    st.write(f"Generating handout for {len(kept_services)} services...")

                    handout_text = generate_handout(visitor_context, kept_services)
                    log_interaction(visitor_context, kept_services, removed_ids)

                    # store for step 2
                    st.session_state["visitor_context"] = visitor_context
                    st.session_state["kept_services"] = kept_services
                    st.session_state["removed_ids"] = removed_ids
                    st.session_state["handout_text"] = handout_text

                    # reset review flag and move to handout step
                    st.session_state["review_ready"] = False
                    st.session_state["services_for_review"] = []
                    st.session_state["step"] = "handout"

                    st.rerun()

    # STEP 2: HANDOUT PAGE
    else:  # st.session_state["step"] == "handout"
        vc = st.session_state["visitor_context"]
        handout_text = st.session_state["handout_text"]

        # current date/time (local)
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

        # ----- PDF generation -----
        pdf_bytes = generate_pdf(handout_text, vc)

        # Debug so we know this ran
        st.write(f"PDF generated with size: **{len(pdf_bytes)} bytes**")

        # Download button (always reliable)
        st.download_button(
            label="📄 Download PDF",
            data=pdf_bytes,
            file_name="NFCM_handout.pdf",
            mime="application/pdf",
        )

        # Best-effort inline preview
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

            st.markdown("### Preview & print (may be hidden by some browser settings)")
            st.markdown(pdf_iframe, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Preview could not be rendered (download still works). Error: {e}")

        st.caption(
            "If you don't see a preview above, use the **Download PDF** button and print "
            "the file from your PDF viewer."
        )

        st.markdown("### Plain text (for copy/paste)")
        st.text_area(
            "You can copy this text into a Word / Google Doc or print directly:",
            value=handout_text,
            height=260,
        )

        st.info(
            "Tip: You can always rely on the **Download PDF** button. "
            "Inline preview may be blocked by some browsers or Streamlit settings."
        )

        st.write("")
        if st.button("Start new visitor"):
            # Reset everything and go back to step 1
            st.session_state.clear()
            st.session_state["step"] = "form"
            st.rerun()


# =====================================================================
# MODE 2: ANALYTICS DASHBOARD (from Google Sheets)
# =====================================================================
else:
    st.subheader("Analytics dashboard – anonymous usage trends")
    
        # --- DEBUG: Show what secrets are being read ---
    try:
        st.write("Debug service account email:", st.secrets["gcp_service_account"]["client_email"])
        st.write("Debug sheet_id:", st.secrets["sheets"]["sheet_id"])
    except Exception as e:
        st.error("Secrets read error:")
        st.code(repr(e))
    # ------------------------------------------------
    
    try:
        df = load_interactions_df()
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
            # Parse timestamps if present
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

            # Top-level KPIs
            total_interactions = len(df)
            date_min = df["timestamp"].min() if "timestamp" in df.columns else None
            date_max = df["timestamp"].max() if "timestamp" in df.columns else None

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total handouts generated", total_interactions)
            with col2:
                st.metric(
                    "First interaction",
                    date_min.strftime("%Y-%m-%d") if date_min is not None else "N/A",
                )
            with col3:
                st.metric(
                    "Most recent",
                    date_max.strftime("%Y-%m-%d") if date_max is not None else "N/A",
                )

            st.markdown("---")

            # --- Top needs ---
            st.markdown("### Top needs selected")

            if "needs" in df.columns:
                needs_df = df.copy()
                needs_df["needs_list"] = needs_df["needs"].fillna("").astype(str).str.split(";")
                needs_exploded = needs_df.explode("needs_list")
                needs_exploded = needs_exploded[needs_exploded["needs_list"] != ""]

                if needs_exploded.empty:
                    st.caption("No needs data recorded yet.")
                else:
                    needs_counts = needs_exploded["needs_list"].value_counts().head(10)

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

            if "service_ids_kept" in df.columns:
                svc_df = df.copy()
                svc_df["service_ids_kept_list"] = (
                    svc_df["service_ids_kept"].fillna("").astype(str).str.split(";")
                )
                svc_exploded = svc_df.explode("service_ids_kept_list")
                svc_exploded = svc_exploded[svc_exploded["service_ids_kept_list"] != ""]

                if svc_exploded.empty:
                    st.caption("No services have been logged yet.")
                else:
                    svc_exploded["service_ids_kept_list"] = pd.to_numeric(
                        svc_exploded["service_ids_kept_list"], errors="coerce"
                    )
                    svc_exploded = svc_exploded.dropna(subset=["service_ids_kept_list"])

                    # Map ID -> name using SERVICES_DF
                    id_to_name = {
                        int(row["id"]): row["name"]
                        for _, row in SERVICES_DF.iterrows()
                    }

                    svc_exploded["service_name"] = svc_exploded[
                        "service_ids_kept_list"
                    ].map(id_to_name)
                    svc_exploded = svc_exploded.dropna(subset=["service_name"])

                    svc_counts = svc_exploded["service_name"].value_counts().head(10)

                    col_left2, col_right2 = st.columns([2, 1])
                    with col_left2:
                        st.bar_chart(svc_counts)
                    with col_right2:
                        st.write("Top services (by count):")
                        st.table(svc_counts.to_frame("count"))
            else:
                st.caption("Column 'service_ids_kept' not found in sheet.")

            st.markdown("---")

            # --- Breakdown by housing or age ---
            st.markdown("### Context breakdown")

            col_h1, col_h2 = st.columns(2)
            with col_h1:
                if "housing_status" in df.columns:
                    st.markdown("**By housing situation**")
                    housing_counts = df["housing_status"].value_counts()
                    st.bar_chart(housing_counts)
                else:
                    st.caption("Column 'housing_status' not found.")
            with col_h2:
                if "age_group" in df.columns:
                    st.markdown("**By age group**")
                    age_counts = df["age_group"].value_counts()
                    st.bar_chart(age_counts)
                else:
                    st.caption("Column 'age_group' not found.")

            # Optional: quick raw preview for debugging
            st.markdown("#### Raw log preview (first 20 rows)")
            st.dataframe(df.head(20))

# ---------- Footer on all pages ----------
st.markdown("---")
st.markdown(
    '<div class="dissa-footer">'
    'Prototype for the Native Friendship Centre of Montreal (NFCM), '
    'in collaboration with Centraide of Greater Montreal – DISSA MVP.'
    '</div>',
    unsafe_allow_html=True,
)
