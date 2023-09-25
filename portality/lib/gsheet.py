import re

import gspread
from gspread.utils import rowcol_to_a1
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials


def load_client(gdrive_key_path):
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(gdrive_key_path, scope)
    client = gspread.authorize(creds)
    return client


def update_sheet_by_df(worksheet, df):
    worksheet.clear()
    set_with_dataframe(worksheet, df)


def range_idx_to_a1(start_row, start_col, end_row, end_col):
    return f'{rowcol_to_a1(start_row, start_col)}:{rowcol_to_a1(end_row, end_col)}'


def idx_to_column_letter(col_idx):
    return re.sub(r'\d+', '', rowcol_to_a1(1, col_idx))
