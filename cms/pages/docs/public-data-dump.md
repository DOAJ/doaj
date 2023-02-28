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

We were obliged to take down the public data dump service on Friday 26th January. This is because, due to a sudden spike, the number of data downloads was so large that it was incurring unforeseen costs. We are committed, however, to providing a data dump service but need some time to investigate a more sustainable way of delivering this data. If you have questions, please email Dominic Mitchell, Operations Manager: [dominic@doaj.org](mailto:dominic@doaj.org).

An [exportable version of the journal metadata]&#40;/csv&#41; is available as a CSV file.

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
