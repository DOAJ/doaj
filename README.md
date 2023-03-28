# The Directory of Open Access Journals (DOAJ)
<!-- ~~DOAJ:Documentation~~ -->

This repository provides the software which drives the DOAJ website and the DOAJ 
directory.

## Reporting issues

Please feel free to use the issue tracker on https://github.com/DOAJ/doaj/issues for any bug 
reports and feature requests. If you're reporting an error, please leave as much information
as you can, e.g. whether you were on mobile or desktop, which browser, what you were trying 
to accomplish, whether you saw an error code, and the time it occurred.

If you'd like to contribute and enhancement or bugfix to the DOAJ, you're more than welcome
to open a pull request!

## Documentation

<!-- ~~->Install:Documentation~~ -->
* [Install](docs/system/INSTALL.md)

<!-- ~~->AuthNZ:Documentation~~ -->
* [Authorisation and Authentication](docs/system/AUTHNZ.md)

<!-- ~~->AWS:Documentation~~ -->
* [AWS Configurations](docs/system/AWS.md)

<!-- ~~->S3:Documentation~~ -->
* [S3 Specific documentation](docs/system/S3.md)

<!-- ~~->OpenURL:Documentation~~ -->
* [OpenURL](docs/system/OPENURL.md)

<!-- ~~->DocSite:Documentation~~ -->
* [DOAJ Auto-generated docs](https://doaj.github.io/doaj-docs/) - here you will find 
data models, test coverage reports, form documentation and a map of the software
  


## How to run testcase with docker
Developer can run selenium testcases with docker OR local chrome.

### [Option 1] prepare selenium with docker
```shell
docker-compose -f $DOAJ_CODE_HOME/docker/docker-compose.yml up
```

### [Option 2] prepare selenium with local chrome
* download chromedriver of you version from https://sites.google.com/chromium.org/driver/
* set environment variable in dev.cfg
```shell
SELENIUM_CHROME_DRIVER_PATH = '<YOUR_CHROMEDIRVER_PATH>/chromedriver'
```

### after your selenium setup is ready, run selenium testcases
* run your elastic search server
* run following command to run selenium testcases
```shell
$DOAJ_VENV/bin/pytest --color=yes --code-highlight=yes $DOAJ_CODE_HOME/doajtest/seleniumtest 
```


