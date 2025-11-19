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


def _open_spreadsheet(client):
    """
    Open the spreadsheet using either a plain ID or a full URL,
    depending on what the user put in secrets.
    """
    sheet_cfg = st.secrets["sheets"]["sheet_id"]

    # Small debug help (you can remove later if you want)
    # st.write("Debug sheet_id from secrets:", sheet_cfg)

    if "https://docs.google.com" in sheet_cfg:
        # User pasted full URL
        sh = client.open_by_url(sheet_cfg)
    else:
        # User pasted just the key
        sh = client.open_by_key(sheet_cfg)

    return sh


def append_interaction_row(row):
    """
    Append a single interaction row to the 'interactions' worksheet.
    """
    client = _get_gsheet_client()
    sh = _open_spreadsheet(client)
    ws = sh.worksheet("interactions")
    ws.append_row(row, value_input_option="RAW")


def load_interactions_df() -> pd.DataFrame:
    """
    Load all interaction rows from Google Sheets into a pandas DataFrame.
    """
    client = _get_gsheet_client()
    sh = _open_spreadsheet(client)
    ws = sh.worksheet("interactions")
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)
