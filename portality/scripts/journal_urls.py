import os
import pandas as pd
from portality.core import app
from portality.bll.doaj import DOAJ
from portality.lib import dates
from portality.lib.dates import FMT_DATETIME_SHORT

"""
This script is the first step of generating csv file with the details validity of the urls in the journal
This script is used to generate html page with the urls for all journals.
Once the html page is generated, upload the page to the server to access the html from web url.
Add the Url to link checker tool(ex https://www.drlinkcheck.com/) and run the link check and generate the report as csv
Input the csv report to 'link_checker_report' script and generate a csv report of the urls along journal information 
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
url_for_journals_aims_and_scope = 'URL for journal\'s aims \& scope',
url_for_journals_instructions_for_authors = 'URL for journal\'s instructions for authors',
url_for_license_terms = 'URL for license terms',
URL_to_an_example_page_with_embedded_licensing_information = 'URL to an example page with embedded licensing ' \
                                                             'information',


def get_csv_file_name():
    # ~~->FileStoreTemp:Feature~~
    filename = 'journalcsv__doaj_' + dates.now_str(FMT_DATETIME_SHORT) + '_utf8.csv'
    return filename


def extra_columns(j):
    return [('Journal ID', j.id)]


def generate_journals_csv(csv_file):
    journal_service = DOAJ.journalService()
    extra_cols = [extra_columns]
    with open(csv_file, 'w', encoding='utf-8') as csvfile:
        journal_service._make_journals_csv(csvfile, extra_cols)

# Read the CSV file
# csv_file = '/Users/rama/CottageLabs/DOAJ/miscellaneous-work/journal_info.csv'
# df = pd.read_csv(csv_file)


# Function to add links for URLs
def add_link(url):
    if pd.notna(url):
        return f'<a href="{url}">{url}</a>'
    return ""


def generate_html_from_csv(csv_file):
    df = pd.read_csv(csv_file)

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
        df[columns[count]] = df[columns[count]].apply(add_link)
        count += 1

    # Select the desired columns from the DataFrame
    df_selected_columns = df[columns]

    # Convert the DataFrame to an HTML table
    html_table = df_selected_columns.to_html(escape=False, index=False)

    file_name = os.path.splitext(os.path.basename(csv_file))[0] + '_'

    counter = 1

    html_file_name = file_name + str(counter) + '.html'

    html_file_path = os.path.join(local_dir, html_file_name)

    # Save the HTML table to a file
    with open(html_file_path, 'w') as f:
        f.write(html_table)

    print("HTML file has been generated.")


def generate_urls():
    # csv_file_name = get_csv_file_name()
    # csv_file_path = os.path.join(local_dir, csv_file_name)
    # generate_journals_csv(csv_file_path)
    generate_html_from_csv('/Users/rama/CottageLabs/DOAJ/code/doaj/local_store/main/journalcsv__doaj_20230511_0528_utf8.csv')


if __name__ == "__main__":
    generate_urls()
