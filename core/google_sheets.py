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
    Open the spreadsheet using the full URL stored in [sheets].sheet_id.
    """
    url = st.secrets["sheets"]["sheet_id"].strip()
    # url must be like "https://docs.google.com/spreadsheets/d/<ID>/edit#gid=0"
    return client.open_by_url(url)


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
