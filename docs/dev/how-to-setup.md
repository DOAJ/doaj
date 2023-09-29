Setup google API key for google sheet
------------------------------------------
### create project an enable api
* go to https://console.cloud.google.com/
* create and select a project on the top left
* searching for "Google Drive API" and enable it, url should be some thing like (https://console.cloud.google.com/marketplace/product/google/drive.googleapis.com)
* searching for "Google Sheets API" and enable it

### create key
* click `create credentials` button
* select `Google Drive API` and `Web server` and `Application data`
* select `No, I'm not using them`
* click `Next`
* filling `Service account name` and `Service account description`
* click `Done`
* select `CREDENTIALS` and your new service
* click `KEYS`, `ADD KEY`
* select `JSON` and click create


### share google sheet to service account
* go to google drive
* right click the sheet you want to share
* click `Share`
* paste the service account email to `People` field
* click `Done`
