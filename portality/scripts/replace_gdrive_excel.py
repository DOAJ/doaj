import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from gspread_dataframe import set_with_dataframe


def main():
    gdrive_key_json_path = '/home/kk/tmp/testdriveapi-393913-d2089ec4ef12.json'
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(gdrive_key_json_path, scope)
    client = gspread.authorize(creds)

    # Fetch the file
    spreadsheet = client.open("testexcel")
    worksheet = spreadsheet.get_worksheet(0)  # We'll only work with the first worksheet

    # Get the data and convert it to dataframe
    data = worksheet.get_all_values()
    # df = pd.DataFrame(data[1:], columns=data[0])
    df = pd.DataFrame(data)
    print(df)
    # return

    # Modify the data
    # Replace 'A' with the column name that you want to edit
    df[0] = df[0].apply(lambda x: x + '_modified')

    # Clear the worksheet before loading new data
    worksheet.clear()

    # Load the modified data
    set_with_dataframe(worksheet, df)


if __name__ == '__main__':
    main()
