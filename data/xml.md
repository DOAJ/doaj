---
layout: sidenav
title: XML
toc: true
highlight: false
---

##Uploading an XML file

+ First convert your article metadata into an accepted XML format: DOAJ or Crossref.
  + It is important that it is structured correctly.
  + Its format must follow a set of rules laid out in the DOAJ XML schema file that we supply, or the rules laid out in Crossref’s schema file.
+ If you are creating DOAJ XML manually, try formatting and validating the file before you upload it to us. 
+ If you are exporting XML from an OJS plugin, you can upload the file immediately.

##List of DOAJ XML elements

Here is a table of each possible element in the DOAJ XML file. It shows you whether or not the element is required by the DOAJ schema. Providing as much information in the metadata as possible ensures a more complete record in our database and allows the record to be distributed more easily to other services.

| Element            | Requirement                                                               |
|--------------------|---------------------------------------------------------------------------|
| Language, ISO code | Optional, max 1.                                                          |
| Publisher          | Optional, max 1.                                                          |
| Journal title      | Required, only 1.                                                         |
| ISSN               | Optional, max. 1. Either the ISSN or the EISSN must be present, or both.  |
| EISSN              | Optional, max. 1.  Either the ISSN or the EISSN must be present, or both. |
| Publication Date   | Required, only 1.                                                         |
| Volume number      | Optional, max. 1                                                          |
| Issue number       | Optional, max. 1                                                          |
| Start page         | Optional, max. 1                                                          |
| End page           | Optional, max. 1                                                          |
| DOI                | Optional, max. 1                                                          |
| Document type      | Optional, max. 1                                                          |
| Title              | Required, 1 or more.                                                      |
| Authors            | Optional                                                                  |
| Affiliations       | Optional                                                                  |
| Abstracts          | Optional                                                                  |
| Full-text URL      | Required, only 1                                                          |
| Keywords           | Optional                                                                  |

There are [European Union restrictions](https://ec.europa.eu/info/law/law-topic/data-protection/reform/what-personal-data_en) on how you distribute personal data, such as email addresses. DOAJ doesn’t have any need for or display author email addresses so please don’t send them to us in the XML.

##Example DOAJ XML File

The example file below contains only one record. 

ADD SAMPLE HERE

##The doajArticles.xsd schema file

The [doajArticles.xsd](http://www.doaj.org/static/doaj/doajArticles.xsd) file specifies what may or may not be uploaded to the database.

