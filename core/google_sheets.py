import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd


def _get_gsheet_client():
    """
    Create an authenticated gspread client using the service account
    stored in Streamlit secrets under [gcp_service_account].
    """
    creds_info = st.secrets["gcp_service_account"]

    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client = gspread.authorize(creds)
    return client


def append_interaction_row(row):
    """
    Append a single interaction row to the 'interactions' worksheet.
    """
    sheet_id = st.secrets["sheets"]["sheet_id"]
    client = _get_gsheet_client()
    ws = client.open_by_key(sheet_id).worksheet("interactions")
    ws.append_row(row, value_input_option="RAW")


def load_interactions_df() -> pd.DataFrame:
    """
    Load all interaction rows from Google Sheets into a pandas DataFrame.
    """
    sheet_id = st.secrets["sheets"]["sheet_id"]
    client = _get_gsheet_client()
    ws = client.open_by_key(sheet_id).worksheet("interactions")
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)
