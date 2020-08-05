# Article XML Upload - DOAJ Staff Troubleshooting Guide

This document describes the possible error messages that a publisher may see when they upload an article XML file
to DOAJ.

On the page [https://doaj.org/publisher/uploadfile](https://doaj.org/publisher/uploadfile) the publisher will have a table of previously uploaded files formatted as follows:


| Upload Date | Filename | Format | Upload Status | Notes |
| ----------- | -------- | ------ | ------------- | ----- |
| 09 Mar 2014 19:54:21 UTC | 15938cafb1934d799d7eae0ff06e6bd8.xml | DOAJ Native XML | processing failed | All articles in file failed to import |

In the "Notes" column, an error message may appear (as it does in the above example).  Depending on the error message, some corrective action may be possible
to resolve the issue.  The sections below describe the possible error messages, reasons for receiving them, and actions to be taken
either by the user or the DOAJ staff.

In cases where no solution can be found between the user and the DOAJ staff, issues may be raised either to the DOAJ sysadmin team (responsible for operating the live service)
or the DOAJ developers (responsible for developing the application features).

## X articles imported (Y new, Z updated); N articles failed

**Reason**: From within the provided file, there were some successful article imports (X), but one or more failed article imports (N)

**Resolution**: Individual articles can fail for a number of reasons.  See the section **Reasons for individual article import failures** below

## All articles in file failed to import

**Reason**: From within the uploaded file, there were no successful article imports and one or more failed article imports

**Resolution**: Individual articles can fail for a number of reasons.  See the section **Reasons for individual article import failures** below

## Error occurred ingesting the records in the document

**Reason**: An unexpected software exception occurred.  

This could be for many different reasons, all of them moderately serious, including: failure to connect to storage layer, previously unknown code bug, or misconfigured live server

**Resolution**: Pass to DOAJ sysadmins and developers as soon as possible.


## File system error when reading file

**Reason**: The file got corrupted on disk, or couldn't be read for some other reason

**Resolution**: This is an unexpected system error, so should be referred to the DOAJ developers as soon as possible

## The file at the URL was too large

**Reason 1**: An HTTP URL provided by the user to the form field "Provide a URL where we can download the XML" led to a file which was larger than the configured MAX_REMOTE_SIZE (currently 250Mb)

**Reason 2**: An FTP URL provided by the user to the form field "Provide a URL where we can download the XML" led to a file which was larger than the configured MAX_REMOTE_SIZE (currently 250Mb)

**Resolution in both cases**: User to provide a smaller file in either case - they can split the articles across two or more schema valid documents, and upload them separately.


## The URL could not be accessed

**Reason 1**: An HTTP URL could not be resolved to a resource on the web (e.g. their web server responded with a 404 Not Found)

**Resolution 1**: The user should check the following regarding the URL they provided to the form field "Provide a URL where we can download the XML":

* That the URL is the correct URL
* That there are no access restrictions on the URL.  For example, authentication is required, or the URL is IP restricted to within their organisation.

If neither of these checks resolves the issue, this should be passed to the DOAJ development team.


**Reason 2**: The download from an HTTP URL failed part way through for an unspecified reason

**Resolution 2**: User to re-try the upload, as this may be an intermittent network issue.

If the user is still unable to get the upload to work after a several attempts, this should be raised with the DOAJ sysadmin team.


## Unable to parse file

**Reason**: The XML file (either downloaded from a URL or uploaded via the web form) could not be read as an XML file

**Resolution**: User to check that the file really is XML.  

In some cases this will be easy - they may have uploaded/provided an incorrect file, so they should check that it is the correct one.  You'd get this error, for example, if they 
have uploaded a Word document or a PDF by mistake.

In other cases files can look very much like XML, but still be invalid.  They should be run through an XML validator to ensure they have the correct structure and that there are no illegal characters (this is common!).

Some XML validator options:

* [W3C Validator](http://www.utilities-online.info/xsdvalidation) - paste the contents of the XML into the left-hand box on this page
* [W3Schools](http://www.w3schools.com/xml/xml_validator.asp) - paste the contents of the XML into one of the boxes on this page
* [xmlvalidation.com](http://www.xmlvalidation.com/) - paste the contents of the XML into one of the boxes on this page, or upload the file

## Unable to parse XML file

See "Unable to parse file"

## Unable to validate document with any available ingesters

**Reason**: No XML schema could be found which would read the provided XML document (in particular, the DOAJ standard schema)

**Resolution**: User to check that the file conforms to the DOAJ schema, using a validator.

The DOAJ schema is on the site, here: [http://doaj.org/static/doaj/doajArticles.xsd](http://doaj.org/static/doaj/doajArticles.xsd)

To validate the provided XML against the schema, you can use one of these services:

* [W3C Validator](http://www.utilities-online.info/xsdvalidation) - paste the contents of the XML into the left-hand box on this page, and the contents of the schema (XSD) into the right-hand box.
* [freeformatter.com](http://www.freeformatter.com/xml-validator-xsd.html) - paste the contents of the XML into the top box, and the contents of the schema (XSD) into the bottom box.  Or, instead, provide a URL to either of them (you can use the URL http://doaj.org/static/doaj/doajArticles.xsd for the DOAJ schema)

If both of these services regard the provided XML as schema valid, it may indicate an issue with the schema availability on the DOAJ site, so this should be passed to the DOAJ sysadmins.



## Reasons for individual article import failures

There are 2 ways that an individual article could fail to import:

**Reason 1**: Article belongs to a journal that does not belong to the publisher's user account

The Article's stated ISSNs must match to a journal that is owned by the same publisher account that is providing the XML file.  
If the ISSNs do not match any journals or match a journal that is owned by a different publisher account, the import of that
article will fail.

Note that it is also possible that if an article has more than one ISSN (i.e. An E-ISSN and a P-ISSN), that those ISSNs could match more than one
Journal (one ISSN matching one journal, the other ISSN matching another).  If both matched journals are owned by the same 
publisher account, this will not stop the article from being imported, but if one of the matched journals is owned by a different publisher account 
this will cause the import of the article to fail.

**Resolution 1**: In order, the following checks should be carried out:

* User to check that all the Article ISSNs in the file are correct
* DOAJ to check that the expected Journal owners are correct
* DOAJ to check that the expected Journal(s) ISSNs are correct


**Reason 2**: Article belongs to a journal that does not have an owner

As above, the ISSNs in the article must match a journal owned by the same publisher account as is providing the XML file.  
If the matched journal does not have an owner, the import for this article will fail

**Resolution 2**: DOAJ to add an owner for the expected Journal