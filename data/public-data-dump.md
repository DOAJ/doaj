---
layout: sidenav
title: Public data dump
toc: true
highlight: false
---

Full data-dumps of the entire journal and article metadata are generated weekly. The files are in JSON format and are in the form that they would also be retrieved via the API.

[Download the journal metadata](/public-data-dump/journal) (4.4Mb)

[Download the article metadata](/public-data-dump/article) (3.5Gb)

Each file is a tar.gz.

The data dumps are structured as follows:

1. When you unzip/untar the file, you will have a single directory of the form doaj_zx[type]_data_[date generated].
2. Inside that directory, you will find a list of files with names of the form [type]_batch_[number].json.
  1. For example journal_batch_3.json or article_batch_27.json.
3. Each file contains up to 100,000 records and is UTF-8 encoded. All files should contain the same number of records, apart from the last one, which may have fewer.
4. The structure of each file is as a JSON list:
    [
        { ... first record ... },
        { ... second record ... },
        { ... third record ...},
        ... etc ...
    ]
5. Records are not explicitly ordered and the order is not guaranteed to remain consistent across data dumps produced on different days.
