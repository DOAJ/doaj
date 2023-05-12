import os
import pandas as pd
import argparse

"""
This script is the second step of generating csv file with the details validity of the urls in the journal.
First step is to execute 'journal_urls' script.
Execute this by passing required input files to generate a report of the urls along with journals information.
"""


def write_results(results):
    df_all_results = pd.concat(results)

    # Sort the results by the original index
    df_all_results_sorted = df_all_results.sort_index()

    df_all_results_sorted.to_csv('multi_result.csv', index=False)

    print("Result CSV file has been written.")


def fetch_matching_rows(journals_csv_file, report_values, results=[]):
    df = pd.read_csv(journals_csv_file)

    # Search for the text in the entire csv file
    mask = df.applymap(lambda x: report_values["url"] in str(x))

    # Get the rows where the text is found
    df_result = df[mask.any(axis=1)]

    if not df_result.empty:
        columns = ['Journal title', 'Added on Date', 'Last updated Date']

        # Select the desired columns from the DataFrame
        df_result_selected_columns = df_result[columns]

        # Add more columns to the DataFrame
        df_result_selected_columns['Url'] = report_values["url"]
        df_result_selected_columns['BrokenCheck'] = report_values["broken_check"]
        df_result_selected_columns['RedirectUrl'] = report_values["redirect_url"]
        df_result_selected_columns['RedirectType'] = report_values["redirect_type"]

        results.append(df_result_selected_columns)


def check_links(csv_file, journal_csv_file):
    df = pd.read_csv(csv_file)
    results = []

    # Iterate through the rows of the DataFrame
    for index, row in df.iterrows():

        values = {
            'url': row["Url"],
            'broken_check': row["BrokenCheck"],
            'redirect_url': row["RedirectUrl"],
            'redirect_type': row["RedirectType"]
        }

        fetch_matching_rows(journal_csv_file, values, results)

    write_results(results)


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument('--file', help='Specify csv file location')
    parser.add_argument('--journal_csv_file', help='Specify the journal csv file location')

    # Parse command-line arguments
    args = parser.parse_args()

    check_links(args.file, args.journal_csv_file)
