# The Directory of Open Access Journals (DOAJ)
<!-- ~~DOAJ:Documentation~~ -->

This repository provides the software which drives the DOAJ website and the DOAJ 
directory.

## CI Status

**develop** &nbsp; [![CircleCI](https://dl.circleci.com/status-badge/img/gh/DOAJ/doaj/tree/develop.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/DOAJ/doaj/tree/develop)

**master** &nbsp; [![CircleCI](https://dl.circleci.com/status-badge/img/gh/DOAJ/doaj/tree/master.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/DOAJ/doaj/tree/master)

## GitHub Actions

There are 2 workflows in GitHub Actions:

* `gen_docs.yml` installs the app and generates the documentation in the repo https://github.com/doaj/doaj-docs on push.
* `clean_docs.yml` removes the docs folder for a branch when it is deleted (i.e. feature branches, on merge).

See the Actions tab for individual runs https://github.com/DOAJ/doaj/actions.

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
data models, test coverage reports, form documentation and a map of the software.
Its repo is at https://github.com/doaj/doaj-docs.
