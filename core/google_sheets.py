import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd


def _get_gsheet_client():
    """Create an authenticated gspread client using the service account."""
    creds_info = st.secrets["gcp_service_account"]

    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client = gspread.authorize(creds)
    return client


def _extract_sheet_key(raw: str) -> str:
    """
    Accepts either:
    - a full Google Sheets URL
    - a partial URL containing '/d/<KEY>/'
    - or just the raw <KEY>

    Returns just the <KEY> that gspread.open_by_key needs.
    """
    raw = raw.strip()

    if "/d/" in raw:
        # e.g. https://docs.google.com/spreadsheets/d/<KEY>/edit?gid=0#gid=0
        part = raw.split("/d/")[1]
        key = part.split("/")[0]
        return key

    # Otherwise assume it's already just the key
    return raw


def _open_spreadsheet(client):
    """Open the spreadsheet using the parsed key."""
    raw = st.secrets["sheets"]["sheet_id"]
    key = _extract_sheet_key(raw)
    # Optional: uncomment while debugging
    # st.write("DEBUG parsed sheet key:", key)
    return client.open_by_key(key)


def append_interaction_row(row):
    """Append a single interaction row to the 'interactions' worksheet."""
    client = _get_gsheet_client()
    sh = _open_spreadsheet(client)
    ws = sh.worksheet("interactions")
    ws.append_row(row, value_input_option="RAW")


def load_interactions_df() -> pd.DataFrame:
    """Load all interaction rows into a pandas DataFrame."""
    client = _get_gsheet_client()
    sh = _open_spreadsheet(client)
    ws = sh.worksheet("interactions")
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)
