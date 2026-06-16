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
For all users, full public data dumps (PDD) of the journal and article metadata are generated monthly. For access, please send an email to [platform@doaj.org](mailto:platform@doaj.org), with the following details:

- your name
- the group, organisation or company you represent or that wants to use the metadata
- your group/organisation/company address, including country
- whether you want access to the journal or article metadata, or both
- what you want to use the metadata for (include as much information as possible)

## Premium metadata service users
Full public data dumps (PDD) of the entire journal and article metadata are generated daily for Premium Setadata Service users. To access the daily PDD, you must be logged in and have an active Premium metadata services account. 

For access or if you want to know more about our Premium Metadata Services, please see the [Premium Metadata Services](/docs/premium) page.

If you are a Premium Metadata Service user and you require technical support, please send an email to [helpdesk@doaj.org](mailto:helpdesk@doaj.org?subject=Premium%20Metadata%20Service)

## About the files

The files are in JSON format and have the same structure as those retrieved via [the API](/docs/api/).

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
5. Records are not explicitly ordered, and the order is not guaranteed to remain consistent across data dumps produced on different days.
