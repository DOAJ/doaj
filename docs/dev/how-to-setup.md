Setup google API key for google sheet
------------------------------------------

### create project an enable api

* go to https://console.cloud.google.com/
* create and select a project on the top left
* searching for "Google Drive API" and enable it, url should be some thing
  like (https://console.cloud.google.com/marketplace/product/google/drive.googleapis.com)
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

How to setup for `datalog_journal_added_update` task
--------------------------------------------------
following variable need for background job `datalog_journal_added_update`

```
# value should be key file path of json, empty string means disabled
GOOGLE_KEY_PATH = ''

# google sheet filename for datalog ja
DATALOG_JA_FILENAME = 'DOAJ: journals added and withdrawn'

# worksheet name or tab name that datalog will write to
DATALOG_JA_WORKSHEET_NAME = 'Added'
```

How to setup for dev with Plausible
-----------------------------------

* run plausible
    * ref 'https://github.com/plausible/community-edition'
    * update `plausible-conf.env`
    * run docker `docker-compose up`
    * testing configuration by browse `http://localhost:8000` and login admin user
* setup fake domain in /etc/hosts
    * e.g. `127.0.0.1    doaj.dev.local`
* setup dev.cfg
    * `DEBUG = False`
    * `BASE_URL = "https://doaj.dev.local:5004"`
    * `PLAUSIBLE_URL = "http://localhost:8000"`
    * `PLAUSIBLE_JS_URL = PLAUSIBLE_URL + "/js/script.outbound-links.file-downloads.js"`
    * `PLAUSIBLE_API_URL = PLAUSIBLE_URL + "/api/event"`
    * `PLAUSIBLE_SITE_NAME = "doaj.dev.local"`
* update `portality/app.py`, change `fake_https=True` e.g. `run_server(fake_https=True)`
    * you might need `cryptography~=42.0` installed in pip
* run `portality/app.py`
* testing configuration by browse `https://doaj.dev.local:5004`



How to upgrade swagger-ui
-------------------------
* run download_swagger_ui.py to download version of swagger-ui you want
* change url of js and css in api_docs.html
* ref: https://github.com/swagger-api/swagger-ui/blob/master/docs/usage/installation.md

