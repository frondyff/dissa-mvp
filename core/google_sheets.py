import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd


def _get_gsheet_client():
    creds_info = st.secrets["gcp_service_account"]

    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client = gspread.authorize(creds)
    return client


def _open_spreadsheet(client):
    """
    Open the spreadsheet using whatever is in [sheets].sheet_id:
    - full URL
    - a partial URL containing '/d/<ID>/...'
    - or just the raw <ID>
    """
    raw = st.secrets["sheets"]["sheet_id"].strip()

    # If it looks like a full URL, use open_by_url
    if raw.startswith("http://") or raw.startswith("https://"):
        return client.open_by_url(raw)

    # If it contains '/d/', extract the ID between /d/ and the next '/'
    if "/d/" in raw:
        key = raw.split("/d/")[1].split("/")[0]
        return client.open_by_key(key)

    # Otherwise assume it's just the plain key
    return client.open_by_key(raw)


def append_interaction_row(row):
    client = _get_gsheet_client()
    sh = _open_spreadsheet(client)
    ws = sh.worksheet("interactions")
    ws.append_row(row, value_input_option="RAW")


def load_interactions_df() -> pd.DataFrame:
    client = _get_gsheet_client()
    sh = _open_spreadsheet(client)
    ws = sh.worksheet("interactions")
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)
