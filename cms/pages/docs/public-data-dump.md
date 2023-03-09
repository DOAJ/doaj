---
layout: sidenav
title: Public data dump
section: Docs
toc: true
sticky_sidenav: true
featuremap: 
  - ~~PublicDataDump:Fragment->JournalDataDump:WebRoute~~
  - ~~->ArticleDataDump:WebRoute~~

---

We are committed to providing a data dump service for the community but, in order to ensure that DOAJ's data is used for the benefit of the entire community and under the terms of the licenses that accompany the data, access to the dumps is granted on a case-by-case basis. If you would like access, please [email our Help Desk](mailto:helpdesk@doaj.org) stating the following information:
 - your name
 - the group, organisation or company you represent or that wants to use the metadata
 - your group/organisation/company address, including country 
 - whether you want access to the journal or article metadata, or both
 - what you want to use the metadata for. Include as much information as possible.

An [exportable version of the journal metadata](/csv) is also available (CSV format).

[//]: # ()
[//]: # (Full data-dumps of the entire journal and article metadata are generated weekly. The files are in JSON format and are in the same form as those retrieved via the API.)

[//]: # ()
[//]: # ([Download the journal metadata]&#40;/public-data-dump/journal&#41; &#40;4.4Mb, licensed under a [Creative Commons Attribution-ShareAlike 4.0 International &#40;CC BY-SA 4.0&#41; license]&#40;https://creativecommons.org/licenses/by-sa/4.0/&#41;&#41;)

[//]: # ()
[//]: # ([Download the article metadata]&#40;/public-data-dump/article&#41; &#40;5.5Gb, copyrights and related rights for article metadata waived via [CC0 1.0 Universal &#40;CC0&#41; Public Domain Dedication]&#40;https://creativecommons.org/publicdomain/zero/1.0/&#41;&#41;)

[//]: # ()
[//]: # (Each file is a `tar.gz`.)

## Structure

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
