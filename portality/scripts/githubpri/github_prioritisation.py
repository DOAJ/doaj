import logging
import os
import sys

import pandas as pd
from gspread.utils import ValueInputOption

from portality.lib import gsheet
from portality.scripts.githubpri import pri_data_serv, gdrive_sheet_serv
from portality.scripts.githubpri.gdrive_sheet_serv import create_or_load_worksheet
from collections import OrderedDict

log = logging.getLogger(__name__)


def to_ordered_df_by_user_pri_map(user_pri_map):
    user_pri_map = user_pri_map.copy()
    claimable_df = user_pri_map.pop(pri_data_serv.DEFAULT_USER, None)
    user_pri_map = OrderedDict(sorted(user_pri_map.items(), key=lambda x: x[0]))
    if claimable_df is not None:
        user_pri_map[pri_data_serv.DEFAULT_USER] = claimable_df
    return pd.concat(user_pri_map, axis=1)


def priorities(priorities_file,
               gdrive_key_path=None,
               outfile=None,
               gdrive_filename=None,
               github_username=None,
               github_password_key=None, ):
    sender = pri_data_serv.GithubReqSender(username=github_username, password_key=github_password_key)
    user_pri_map = pri_data_serv.create_priorities_excel_data(priorities_file, sender)

    if outfile is not None:
        to_ordered_df_by_user_pri_map(user_pri_map).to_csv(outfile)

    if gdrive_filename is None:
        print('gdrive filename is not provided, skip updating google sheet')
        sys.exit(0)
    elif gdrive_key_path is None:
        log.warning('gdrive json key path is not provided, skip updating google sheet')
        sys.exit(1)

    print(f'[Start] update google sheet [{gdrive_filename}]')

    display_df = to_ordered_df_by_user_pri_map({
        user: pri_df.drop('issue_url', axis=1)
        for user, pri_df in user_pri_map.items()
    })
    client = gsheet.load_client(gdrive_key_path)
    sh = client.open(gdrive_filename)

    worksheet = create_or_load_worksheet(sh)

    gsheet.update_sheet_by_df(worksheet, display_df)

    # assign title to issue_url's hyperlink
    for col_idx, (column_keys, titles) in enumerate(display_df.items()):
        if 'title' not in column_keys:
            continue
        username, *_ = column_keys
        titles = titles.dropna().apply(lambda x: x.replace('"', '""'))
        cells = worksheet.range(3, col_idx + 1, len(titles) + 3, col_idx + 1)
        for (row_idx, title), cell in zip(titles.items(), cells):
            link = user_pri_map[username].loc[row_idx, 'issue_url']
            cell.value = f'=HYPERLINK("{link}", "{title}")'
        worksheet.update_cells(cells, ValueInputOption.user_entered)

    gdrive_sheet_serv.apply_prilist_styles(worksheet, display_df)
    print(f'[End] update google sheet [{gdrive_filename}]')


def main():
    """
    check README.md for usage

    :return:
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username",
                        help="github username")
    parser.add_argument("-p", "--password",
                        help="github password or api key")
    parser.add_argument("-r", "--rules",
                        help="file path of rules excel", required=True)
    parser.add_argument("-o", "--out",
                        help="file path of local output excel")
    parser.add_argument("-g", "--gdrive-name",
                        help="excel name in google drive")

    args = parser.parse_args()

    priorities(args.rules,
               outfile=args.out,
               gdrive_filename=args.gdrive_name,
               gdrive_key_path=os.environ.get('DOAJ_PRILIST_KEY_PATH'),
               github_username=args.username,
               github_password_key=args.password or os.environ.get('DOAJ_GITHUB_KEY'),
               )


if __name__ == "__main__":
    main()