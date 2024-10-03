---
layout: sidenav
title: OpenURL
section: Docs
toc: true
sticky_sidenav: true
featuremap: ~~OpenURL:Fragment~~

---

An OpenURL is similar to a web address, but instead of referring to a physical website, it refers to an article, book, patent, or other resource within a website. OpenURLs are similar to permalinks because they are permanently connected to a resource, regardless of which website the resource is located at. (Retrieved from [Wikipedia](https://en.wikipedia.org/wiki/OpenURL).)

The resource is retrieved using [a structured URL format.](http://hdl.handle.net/11213/19012)

On DOAJ, the parameters included in the request are passed to our search interface, which provides the top result. This means that using OpenURL isn't guaranteed to find your result 100% of the time, even if it exists.

## Parameter mapping

Here is the mapping between OpenURL parameters and our Elasticsearch database fields.

### Journal

| Parameter | DOAJ record field               |
|-----------|---------------------------------|
| jtitle    | index.title.exact               |
| stitle    | bibjson.alternative_title.exact |
| issn      | index.issn.exact                |
| eissn     | index.issn.exact                |
| isbn      | index.title.exact               |

### Article

| Parameter | DOAJ record field                |
|-----------|----------------------------------|
| aulast    | bibjson.author.name.exact        |
| aucorp    | bibjson.author.affiliation.exact |
| atitle    | bibjson.title.exact              |
| jtitle    | bibjson.journal.title.exact      |
| date      | bibjson.year.exact               |
| volume    | bibjson.journal.volume.exact     |
| issue     | bibjson.journal.number.exact     |
| spage     | bibjson.start_page.exact         |
| epage     | bibjson.end_page.exact           |
| issn      | index.issn.exact                 |
| eissn     | index.issn.exact                 |
| isbn      | index.title.exact                |
| doi       | index.doi.exact                  |

## Improving results

There are a few things you can try if you keep seeing the _Not Found_ page or getting the wrong result:

{:.numbered-table .numbered-table--labels}
|   | Troubleshooting tip                                      | Details                                                                                          |
|---|----------------------------------------------------------|--------------------------------------------------------------------------------------------------|
|   | Use a trustworthy field                                  | Identifiers like `issn` are more reliable than free text like `jtitle`.                          |
|   | Make sure each parameter is correct                      | Ensure there are no typos or strange formatting and that the parameter labels are correct.       |
|   | Reduce constraints for article searches                  | Remove some parameters, like 'volume' or 'issue', because these may not be present in our index. |
|   | Improve article search accuracy by using `genre=article` | URLs without this parameter will be directed to the journal page.                                |
|   | Use OpenURL 1.0                                          | This will remove the rewriting step from the process (see below).                                |

## Supported OpenURL version

DOAJ prefers to receive OpenURL 1.0 requests. However, if the old "0.1" syntax is used, the DOAJ will rewrite it to the new syntax and try again. You will see a redirect to an OpenURL 1.0 URL and then the result.
