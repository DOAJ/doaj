import datetime
import re

import gspread
import gspread.exceptions
import gspread_formatting as gspfmt
from gspread.utils import rowcol_to_a1
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials

from portality.lib import dates


def load_client(gdrive_key_path):
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(gdrive_key_path, scope)
    client = gspread.authorize(creds)
    return client


def update_sheet_by_df(worksheet, df):
    worksheet.clear()
    set_with_dataframe(worksheet, df)


def apply_prilist_styles(worksheet, display_df):
    # change style of the cells
    n_col = len(display_df.columns)
    n_row = len(display_df)

    # set header row bold
    gspfmt.format_cell_range(worksheet,
                             range_idx_to_a1(1, 1, 2, n_col),
                             cell_format=gspfmt.CellFormat(textFormat=gspfmt.TextFormat(bold=True)))
    # set user col borders
    latest_username = None
    for col_idx, (column_keys, titles) in enumerate(display_df.items()):
        username, *_ = column_keys
        if latest_username == username:
            continue

        latest_username = username
        gs_col_idx = col_idx + 1
        cells = worksheet.range(3, gs_col_idx, len(titles) + 3, gs_col_idx)
        gspfmt.format_cell_range(worksheet,
                                 range_idx_to_a1(1, gs_col_idx, n_row + 2, gs_col_idx),
                                 cell_format=gspfmt.CellFormat(
                                     borders=gspfmt.Borders(left=gspfmt.Border('SOLID_MEDIUM'))))
    # set header row borders
    gspfmt.format_cell_range(worksheet,
                             range_idx_to_a1(2, 1, 2, n_col),
                             cell_format=gspfmt.CellFormat(
                                 borders=gspfmt.Borders(bottom=gspfmt.Border('SOLID_MEDIUM'))))
    # set col width
    col_width_map = {
        'rule_id': 50,
        'issue_number': 50,
        'title': 400,
        'status': 80,
    }
    for col_idx, (column_keys, titles) in enumerate(display_df.items()):
        username, col_name = column_keys
        if col_name not in col_width_map:
            continue
        gspfmt.set_column_width(worksheet, idx_to_column_letter(col_idx + 1), col_width_map[col_name])


def range_idx_to_a1(start_row, start_col, end_row, end_col):
    return f'{rowcol_to_a1(start_row, start_col)}:{rowcol_to_a1(end_row, end_col)}'


def idx_to_column_letter(col_idx):
    return re.sub(r'\d+', '', rowcol_to_a1(1, col_idx))


def create_or_load_worksheet(sh, n_row=50, n_col=30):
    def _create_worksheet(name):
        return sh.add_worksheet(
            title=name,
            rows=n_row + 5, cols=n_col + 5,
        )

    worksheet_name = f'priority list -- {datetime.datetime.now().strftime(dates.FMT_DATE_STD)}'
    try:
        worksheet = _create_worksheet(worksheet_name)
    except gspread.exceptions.APIError as e:
        if 'already exists' in str(e):
            print(f'Worksheet {worksheet_name} already exists, updating it')
            worksheet = sh.worksheet(worksheet_name)
        else:
            raise e
    return worksheet
