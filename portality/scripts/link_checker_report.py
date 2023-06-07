import pandas as pd
import argparse
from portality import models
from portality.crosswalks.journal_form import JournalFormXWalk
from datetime import datetime
import os

"""
This script is the second step of generating csv file with the details validity of the urls in the journal.
First step is to execute 'journal_urls' script.
Execute this by passing required input files to generate a report of the urls along with journals information.

Steps to generate the report csv file:

1. Run journal_urls.py -> python portality/scripts/journal_urls.py
2. The above scripts will generate doaj_journals_links.csv file at the location mention in the config for 
   'STORE_LOCAL_DIR'. Example location 'local_store/main/doaj_journals_links.csv'
3. This script also generates the HTML files at the location from where the script is executed
4. Input the html files to link checker tool (https://www.drlinkcheck.com/)  by copying the html files to the server and mention the location to the 
   link checker tool
5. Run the link check on the tool and export the csv file to a local location
6. Run link_checker_report.py by passing the file locations as parameters.
   ex: python portality/scripts/link_checker_report.py --file <links-doaj-link-check-test-2023-05-11_13-31-59.csv>
    --journal_csv_file <local_store/main/doaj_journals_links.csv>
    Provide the absolute paths for the files
7. Once the above script is run, final report csv file will be generated 
"""


def log(msg):
    print("[{x}] {y}".format(x=datetime.utcnow().strftime("%y-%m-%dT%H:%M:%SZ"), y=msg))


def write_results(df, filename='multi_result.csv'):
    """
    Write results to a csv file
    :param df: DataFrame object of the csv file
    :param filename: Output file name
    :return:
    """
    # Sort the results by the original index
    df_sorted = df.sort_values(by='Journal title')

    df_sorted.to_csv(filename, index=False)

    print("Result CSV file has been written.")


def _get_link_type(link, journal):
    form = JournalFormXWalk.obj2form(journal)

    locations = []
    subs = []
    for k, v in form.items():
        if v is None:
            continue
        if isinstance(v, list):
            if link in v:
                locations.append(k)
            else:
                for e in v:
                    if isinstance(e, dict):
                        for sk, sv in e.items():
                            if not isinstance(sv, str):
                                continue
                            if link == sv:
                                locations.append(sk)
                            elif sv.startswith(link):
                                subs.append(sk)
                    else:
                        if e.startswith(link):
                            subs.append(k)
                            break
        else:
            if not isinstance(v, str):
                continue
            if v == link:
                locations.append(k)
            elif v.startswith(link):
                subs.append(k)

    return locations + subs


def fetch_matching_rows(journal_url_index, report_values):
    """Check with journals dataframe and retrieve matching rows with url.
       :param df: DataFrame
       :param report_values: url to match
       :return: DataFrame with matching rows
    """
    # Search for the text in the entire csv file
    #mask = df.applymap(lambda x: report_values["url"] in str(x))

    # Get the rows where the text is found
    #df_result = df[mask.any(axis=1)]
    journal_data = journal_url_index.get(report_values["url"])

    # if not df_result.empty:
    if journal_data is not None:
        # columns = ['Journal title', 'Added on Date', 'Last updated Date', "Journal ID"]

        # Select the desired columns from the DataFrame
        # df_result_selected_columns = df_result[columns].copy()  # create a copy to avoid SettingWithCopyWarning
        df_result_selected_columns = pd.DataFrame(
            data=[list(journal_data)],
            columns=['Journal title', 'Added on Date', 'Last updated Date', "Journal ID"]
        )

        jid = df_result_selected_columns["Journal ID"].values[0]
        journal = models.Journal.pull(jid)
        primary_type = ""
        question_link = ""
        types = []

        if journal is not None:
            types = _get_link_type(report_values["url"], journal)
            if len(types) > 0:
                primary_type = types[0]
                question_link = "https://doaj.org/admin/journal/" + jid + "#question-" + primary_type

        # Add more columns to the DataFrame
        df_result_selected_columns["DOAJ Form"] = "https://doaj.org/admin/journal/" + jid
        df_result_selected_columns["Form Field"] = question_link
        df_result_selected_columns['Url'] = report_values["url"]
        df_result_selected_columns['Type'] = primary_type
        df_result_selected_columns["Also present in"] = ", ".join(types)
        df_result_selected_columns['BrokenCheck'] = report_values["broken_check"]
        df_result_selected_columns['RedirectUrl'] = report_values["redirect_url"]
        df_result_selected_columns['RedirectType'] = report_values["redirect_type"]

        return df_result_selected_columns
    else:
        return pd.DataFrame()


def _index_journals(df):
    jidx = {}
    for index, row in df.iterrows():
        for cell in row:
            # FIXME: assumes each URL only appears once
            if isinstance(cell, str) and cell.startswith("http"):
                jidx[cell] = (row[0], row[50], row[51], row[54])
    return jidx


def check_links(df, journal_url_index):
    """
    Retrieve the URLs from the csv file
    :param df: DataFrame object of the csv file which is exported from link checker tool
    :param journal_df: DataFrame object of the journals csv file generated by journal_urls.py script
    :return: DataFrame object of the results
    """
    results = []

    # Iterate through the rows of the DataFrame
    size = len(df)
    for index, row in df.iterrows():
        if row["BrokenCheck"] == "OK" and not isinstance(row["RedirectUrl"], str):
            continue

        if isinstance(row["RedirectUrl"], str) and row["RedirectUrl"].startswith("https://doaj.org"):
            continue

        log("checking row {x}/{y}: {a} {b}".format(x=index, y=size, a=row["BrokenCheck"], b=row["RedirectUrl"]))
        values = {
            'url': row["Url"],
            'broken_check': row["BrokenCheck"],
            'redirect_url': row["RedirectUrl"],
            'redirect_type': row["RedirectType"]
        }


        result = fetch_matching_rows(journal_url_index, values)
        if not result.empty:
            results.append(result)

    return pd.concat(results) if results else pd.DataFrame()


def generate_report(csv_files, journal_csv_file):
    """
    Generate a report in a format that is useful to analyze from the csv file exported from link checker tool
    :param csv_file: csv file exported from link checker tool
    :param journal_csv_file: journal csv file generated by the journal_urls.py script
    :return:
    """

    journal_df = pd.read_csv(journal_csv_file)
    log("Read journal file")
    journal_url_index = _index_journals(journal_df)
    log("Indexed journal urls")

    master_df = pd.DataFrame(columns=['Journal title', 'Added on Date', 'Last updated Date', "Journal ID"])
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        log("Checking file {x}".format(x=csv_file))
        df = check_links(df, journal_url_index)
        master_df = pd.concat([master_df, df])

    log("All links checked")
    write_results(master_df)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument('--file', help='Specify csv file location downloaded from link checker tool.')
    parser.add_argument("--dir", help="Directory where dr link checker report files are found")
    parser.add_argument("--prefix", help="Dr Link Checker file prefixes, if specifying the --dir option")
    parser.add_argument('--journal_csv_file', help='Specify the journal csv file location generated by journal_urls.py'
                                                   ' script')

    # Parse command-line arguments
    args = parser.parse_args()

    log("start")

    files = []
    if args.dir and args.prefix:
        options = os.listdir(args.dir)
        for o in options:
            if o.startswith(args.prefix):
                files.append(os.path.join(args.dir, o))
    else:
        files.append(args.file)

    log("Checking files: {x}".format(x=", ".join(files)))
    generate_report(files, args.journal_csv_file)

    log("end")
