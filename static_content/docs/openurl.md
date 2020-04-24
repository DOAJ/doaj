---
layout: sidenav
title: OpenURL
section: Documentation
toc: true
highlight: false
---

[OpenURL is for retrieving a resource using a structured URL format.](http://alcme.oclc.org/openurl/servlet/OAIHandler?verb=ListSets)

On DOAJ, the parameters included in the request are passed to our search interface, which provides the top result. This means that using OpenURL isn't guaranteed to find your result 100% of the time, even if it exists.

## Improving results

There are a few things you can try if you keep seeing the _Not Found_ page or getting the wrong result:

{:.numbered-table .numbered-table--labels}
|   | Troubleshooting tip                 | Details                                                                                               |
|---|-------------------------------------|-------------------------------------------------------------------------------------------------------|
|   | Use a trustworthy field             | Identifiers like `issn` are more reliable than free text like `title`.                                |
|   | Make sure each parameter is correct | Ensure there are no typos or strange formatting and that the parameter labels are correct.            |
|   | Reduce constraints                  | Remove some parameters, like specific volume and issue because these may not be present in our index. |
|   | Use OpenURL 1.0                     | This will remove the rewriting step from the process (see below).                                     |

## Supported OpenURL version

DOAJ prefers to receive OpenURL 1.0 requests. However, if the old "0.1" syntax is used, the DOAJ will rewrite it to the new syntax and try again. You will see a redirect to an OpenURL 1.0 URL, then the result.
