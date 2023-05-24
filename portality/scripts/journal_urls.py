import os
import pandas as pd
from portality.core import app
from portality.bll.doaj import DOAJ

"""
This script is the first step of generating csv file with the details validity of the urls in the journal
This script is used to generate html page with the urls for all journals.
Once the html page is generated, upload the page to the server to access the html from web url.
Add the Url to link checker tool(ex https://www.drlinkcheck.com/) and run the link check and generate the report as csv
Input the csv report to 'link_checker_report' script and generate a csv report of the urls along journal information

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

local_dir = app.config.get("STORE_LOCAL_DIR")

journal_url = 'Journal URL'
url_in_doaj = 'URL in DOAJ'
apc_information_url = 'APC information URL'
copyright_information_url = 'Copyright information URL'
url_for_deposit_policy = 'URL for deposit policy',
url_for_the_editorial_board_page = 'URL for the Editorial Board page',
review_process_information_url = 'Review process information URL',
other_fees_information_url = 'Other fees information URL',
plagiarism_information_url = 'Plagiarism information URL',
preservation_information_url = 'Preservation information URL',
url_for_journals_aims_and_scope = "URL for journal's aims & scope",
url_for_journals_instructions_for_authors = "URL for journal's instructions for authors",
url_for_license_terms = 'URL for license terms',
URL_to_an_example_page_with_embedded_licensing_information = 'URL to an example page with embedded licensing ' \
                                                             'information',


def get_csv_file_name():
    return 'doaj_journals_links.csv'


def extra_columns(j):
    """Add extra columns"""
    return [('Journal ID', j.id)]


def generate_journals_csv(csv_file):
    """Generate the csv file for all journals"""
    journal_service = DOAJ.journalService()
    extra_cols = [extra_columns]
    with open(csv_file, 'w', encoding='utf-8') as csvfile:
        journal_service._make_journals_csv(csvfile, extra_cols)


def add_link(df, url_column):
    df[url_column] = df[url_column].apply(lambda x: f'<a href="{x}">{x}</a>' if pd.notna(x) else "")
    return df


def select_columns(df, columns):
    return df[columns]


def read_csv(csv_file):
    df = pd.read_csv(csv_file)
    return df


def generate_html_files(df, file_name, rows_count=1150):
    """
    Generates HTML file from the CSV file
    :param df: DataFrame object of the csv file
    :param file_name: File name of the HTML output file
    :param rows_count: Rows for each HTML file
    :return:
    """
    for i in range(0, len(df), rows_count):
        html_file = file_name + f'{i // rows_count + 1}.html'
        chunk = df.iloc[i:i + rows_count]
        chunk.to_html(html_file, index=False)


def generate_html_from_csv(csv_file):
    """
    Generates HTML files from csv files
    :param csv_file: csv file input
    """
    df = read_csv(csv_file)

    # Specify the columns you want to include in the HTML table
    columns = ["Journal ID", "Journal URL", "URL in DOAJ", "APC information URL", "Copyright information URL",
               "URL for deposit policy", "URL for the Editorial Board page", "Review process information URL",
               "Other fees information URL", "Plagiarism information URL",
               "Preservation information URL", "URL for journal's aims & scope",
               "URL for journal's instructions for authors", "URL for license terms",
               "URL to an example page with embedded licensing information",
               "URL for journal's Open Access statement", "Waiver policy information URL"]

    count = 1

    while count < len(columns):
        add_link(df, columns[count])
        count += 1

    # Select the desired columns from the DataFrame
    df_selected_columns = select_columns(df, columns)

    file_name = os.path.splitext(os.path.basename(csv_file))[0] + '_'

    generate_html_files(df_selected_columns, file_name)

    print("HTML file(s) generated.")


def generate_urls():
    """
    Generated HTML file with journal urls
    """
    csv_file_name = get_csv_file_name()
    csv_file_path = os.path.join(local_dir, csv_file_name)
    generate_journals_csv(csv_file_path)
    generate_html_from_csv(csv_file_path)


if __name__ == "__main__":
    generate_urls()
