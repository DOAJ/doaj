---
layout: sidenav
title: Public data dump
section: Data
toc: false
sticky_sidenav: false
preface: /public/includes/_pdd-access.html
featuremap: 
  - ~~PublicDataDump:Fragment->JournalDataDump:WebRoute~~
  - ~~->ArticleDataDump:WebRoute~~

---

## All users
For all users, full data-dumps of the journal and article metadata are generated monthly.

## Premium metadata service users
Full data-dumps of the entire journal and article metadata are generated daily for premium metadata service users. To access Premium metadata services, you must be logged into your DOAJ account and have an active Premium metadata services subscription. 

If you would like access to more up-to-date metadata and to know more about our Premium Metadata Services, please see the [Premium Metadata Services](https://github.com/DOAJ/doaj/blob/feature/4008_premium/docs/premium) page.

## About the files

The files are in JSON format and are in the same form as those retrieved via [the API](/docs/api/).

The data dumps are structured as follows:

1. When you unzip/untar the file, you will have a single directory of the form `doaj_zx[type]_data_[date generated]`.
2. Inside that directory, you will find a list of files with names of the form `[type]_batch_[number].json`.
  - For example, `journal_batch_3.json` or `article_batch_27.json`.
3. Each file contains up to 100,000 records and is UTF-8 encoded. All files should contain the same number of records, apart from the last one, which may have fewer.
4. The structure of each file is as a JSON list:
  ```
    [
        { ... first record ... },
        { ... second record ... },
        { ... third record ...},
        ... etc ...
    ]
  ```
5. Records are not explicitly ordered and the order is not guaranteed to remain consistent across data dumps produced on different days.
