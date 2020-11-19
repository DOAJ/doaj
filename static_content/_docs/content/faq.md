## Contribute

### How can I contribute to DOAJ?

1. [Support us](/support/) with a financial contribution
  + Contributions help keep the DOAJ service running and allow us to develop it further.
2. If you have evidence that a journal in DOAJ might be questionable, [contact us](/contact/).
  + All information shared with DOAJ is done so in confidence and is never published.
  + Include the ISSN of the journal when you email us.
3. If you find a broken link or something that is out of date or incomplete, [contact us](/contact/).
  + We are always grateful when our users are our eyes and ears.
  + For broken links in articles, include the journal's ISSN, title and the title of the article.
4. Become a volunteer
  + From time to time, we put out a call for volunteers. Follow us on [Twitter](https://twitter.com/doajplus) or [our blog](https://blog.doaj.org/) to find out when the next call is published.

### I know a journal which should be in DOAJ but isn’t. What should I do?

  Contact the journal and ask them to submit an application. You can also send us the details of the journal—title and ISSN—and we will contact them.

### The journal I am looking for isn't in DOAJ. Why?

  Maybe the journal hasn't applied to us or its application is still in progress. Maybe the journal was [removed from DOAJ](https://docs.google.com/spreadsheets/d/183mRBRqs2jOyP0qZWXN8dUd02D4vL0Mov_kgYF8HORM/edit#gid=1650882189&range=A1).

### How do I report a bug or ask for technical help?

  If you are a registered GitHub user, or you don't mind becoming one, you can [log a GitHub issue](https://github.com/DOAJ/doaj/issues/new) directly in our repository. Alternatively, you can send the information we ask for below to [our helpdesk](mailto:feedback@doaj.org).
  
 <a id="How to report a bug"></a>When you report a bug, please include the following information. (You may not be able to provide every detail but fill in as many as you can.)

1. The contact details for the person reporting the bug (or a proxy for them) so that we can request more detail if needed.
  + That might be you or someone working on your behalf.
2. The user account you are logged in to when the problem occurred.
3. Tell us which area of the system this happened in. Generally: in the UI/API/OAI; and ideally specifically:
  + which URL were you on when it happened, or
  + which URL were you trying to access.
4. At what date and time the incident occurred.
  + If it happened several times, then all dates/times that were recorded, or a range.
5. What were you trying to do? As much detail and context as possible.
  + Send a screenshot of the entire screen. An image always helps.
6. What happened? What error message was received?
  + Provide the exact error message; don't paraphrase
  + Send a screenshot
  + What did you expect to happen?
  + Was the problem repeatable?
  + Did you try several times with the same result?
7. What environment are you in?
  + Specifically which browser or,
  + If not in the browser, any useful information about your API client such as the user agent.
8. Send copies of any data you sent to the system.
  + For example, article XML files uploaded, or payloads sent to the API.

Don’t send us your passwords or API keys.

---
## Metadata

### Failed XML uploads explained

This section describes the possible error messages that you may see when you upload an article XML file to DOAJ. Depending on the message in the "Notes" column of your [History of uploads](/publisher/uploadfile) table, some corrective actions may be available to you.

In cases where there is no action to be taken, or the suggested actions have not successfully resolved the issues, please [contact us](/contact/) with the following details:

*   The time of the file upload
*   The exact error message as it appears in the "Notes" column
*   Your publisher account username
*   A copy of the file you had problems with
*   A screenshot of your File upload area

#### <a id="some_articles_failed"></a>X articles imported (Y new, Z updated); N articles failed

**Reason**: From within the provided file, there were some successful article imports (X), but one or more failed article imports (N)

**Resolution**: Individual articles can fail for a number of reasons. See the section [Reasons for individual article import failures](#Reasons for individual article import failures) below

#### <a id="All articles in file failed to import"></a>All articles in file failed to import

**Reason**: From within the uploaded file, there were no successful article imports and one or more failed article imports

**Resolution**: Individual articles can fail for a number of reasons. See the section [Reasons for individual article import failures](#Reasons for individual article import failures) below

#### <a id="Error occurred ingesting the records in the document"></a>Error occurred ingesting the records in the document

**Reason**: An unexpected software exception occurred - you may have found a bug!

**Resolution**: Please [contact us](/contact/) immediately with the relevant details.

#### <a id="Unanticipated error when importing articles"></a>Unanticipated error when importing articles

**Reason**: Something unexpected happened when we tried to import your articles - you may have found a bug!

**Resolution**: Please [contact us](/contact/) immediately with the details:

1. The contact details for the person reporting the bug (or a proxy for them) so that we can request more detail if needed.
    + That might be you or someone working on your behalf.
  2. The user account you are logged in to when the problem occurred.
  3. Tell us which area of the system this happened in. Generally: in the UI/API/OAI; and ideally specifically:
    + which URL were you on when it happened, or
    + which URL were you trying to access.
  4. At what date and time the incident occurred.
    + If it happened several times, then all dates/times that were recorded, or a range.
  5. What were you trying to do? As much detail and context as possible.
    + Send a screenshot of the entire screen. An image always helps.
  6. What happened? What error message was received?
    + Provide the exact error message; don't paraphrase
    + Send a screenshot
    + What did you expect to happen?
    + Was the problem repeatable?
    + Did you try several times with the same result?
  7. What environment are you in?
    + Specifically which browser or,
    + If not in the browser, any useful information about your API client such as the user agent.
  8. Send copies of any data you sent to the system.
    + For example, article XML files uploaded, or payloads sent to the API.

Don’t send us your passwords or API keys.

#### <a id="The file at the URL was too large"></a>The file at the URL was too large

**Reason**: A URL (either HTTP or FTP) you provided to the form field "Provide a URL where we can download the XML" led to a file which was larger than 250Mb

**Resolution**: Please provide a smaller file in either case. You can split the articles across two or more schema valid documents, and make them available to us separately.

#### <a id="The URL could not be accessed"></a>The URL could not be accessed

**Reason 1**: The HTTP URL you provided could not be resolved to a resource on the web (e.g. your web server responded with a 404 Not Found)

**Resolution 1**: Check the following regarding the URL your provided to the form field "Provide a URL where we can download the XML":

*   That the URL is the correct URL
*   That there are no access restrictions on the URL. For example, authentication is required, or the URL is IP restricted to within your organisation.

**Reason 2**: The download from an HTTP URL you provided failed part way through for an unspecified reason

**Resolution 2**: Re-try the upload, as this may be an intermittent network issue.

If you are still unable to get the upload to work after a several attempts, please [contact us](/contact/) with the relevant details.

#### <a id="Unable to parse file"></a>Unable to parse file

**Reason**: The XML file you provided (either downloaded from a URL or uploaded via the web form) could not be read as an XML file

**Resolution**: Check that the file really is valid XML.

In some cases this will be easy - you may have uploaded/provided the wrong file, so double-check that it is the correct one. You'd get this error, for example, if you have uploaded a Word document or a PDF by mistake.

In other cases files can look very much like XML, but still be invalid. They should be run through an XML validator to ensure they have the correct structure and that there are no illegal characters.

Sometimes, special characters - especially those in scientific articles - are submitted in the wrong format. XML does not support many special characters as-is but those that it does can be [found on Wikipedia](https://en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references#Predefined_entities_in_XML).

You can use one of these validators to check your XML:

*   [W3C Validator](http://www.utilities-online.info/xsdvalidation/) - paste the contents of the XML into the left-hand box on this page
*   [W3Schools](https://www.w3schools.com/xml/xml_validator.asp) - paste the contents of the XML into one of the boxes on this page
*   [xmlvalidation.com](https://www.xmlvalidation.com/) - paste the contents of the XML into one of the boxes on this page, or upload the file

#### <a id="Unable to parse XML file"></a>Unable to parse XML file

See ["Unable to parse file"](#Unable to parse file)

#### <a id="Unable to validate document with identified schema"></a>Unable to validate document with identified schema

**Reason**: No XML schema could be found which would read the provided XML document (in particular, the DOAJ standard schema)

**Resolution**: Check that the file conforms to the DOAJ schema, using a validator.

Often the problem arises because the XML is missing a required tag. If you try to upload XML to DOAJ that is missing a specific tag, such as <publicationDate> then the schema validation will fail. You can see exactly [which tags are required here](/docs/xml/).

If you are trying to upload a file that was automatically generated by the OJS DOAJ plugin, then you should first contact OJS for help.

The DOAJ schema is on our site, here: [http://doaj.org/static/doaj/doajArticles.xsd](http://doaj.org/static/doaj/doajArticles.xsd)

To validate the provided XML against the schema, you can use one of these services:

*   [W3C Validator](http://www.utilities-online.info/xsdvalidation) - paste the contents of the XML into the left-hand box on this page, and the contents of the schema (XSD) into the right-hand box.
*   [freeformatter.com](https://www.freeformatter.com/xml-validator-xsd.html) - paste the contents of the XML into the top box, and the contents of the schema (XSD) into the bottom box. Or, instead, provide a URL to either of them (you can use the URL [http://doaj.org/static/doaj/doajArticles.xsd](http://doaj.org/static/doaj/doajArticles.xsd) for the DOAJ schema)

If both of these services regard the provided XML as schema valid, please [contact us](/contact/) with the relevant details.

#### <a id="Reasons for individual article import failures"></a>Reasons for individual article import failures

**Reason**: Article belongs to a journal that does not belong to your user account

You can only upload XML for the journals that are IN DOAJ and that appear in the list under 'Your Journals' in the publisher area. If you have more than one account and you would like to merge them, please contact us.

The Article's stated ISSNs must match to a journal that is owned by the user account from which you are providing the XML file. If the ISSNs do not match any journals or match a journal that is owned by a different account, the import of that article will fail.

Note that it is also possible that if an article has more than one ISSN (i.e. an E-ISSN and a P-ISSN), that those ISSNs could match more than one Journal (one ISSN matching one journal, the other ISSN matching another). If both matched journals are owned by your account, this will not stop the article from being imported, but if one of the matched journals is owned by a different account this will cause the import of the article to fail.

A journal may have two ISSNs: an ISSN for the print version and an ISSN for the electronic version. Sometimes the ISSNs of the journal have changed. If you need to have the ISSNs of your DOAJ record updated, please [contact us](/contact/) and we will check that the ISSNs are registered at [the ISSN Portal](https://portal.issn.org/) and will then update the record accordingly.

**Resolution**: Check that all the Article ISSNs in the file are correct

If you believe all the ISSNs for the articles are correct, please [contact us](/contact/) with the relevant details.

#### <a id="One or more articles in this batch have duplicate identifiers"></a>One or more articles in this batch have duplicate identifiers

**Reason**: At least two of the articles in the uploaded file contain the same DOI and/or the same fulltext url

**Resolution**: Ensure that there are no duplicated articles in the file. Ensure that you are using the correct DOIs and URLs for all the articles.

#### <a id="One or more articles in this batch matched multiple articles as duplicates; entire batch ingest halted"></a>One or more articles in this batch matched multiple articles as duplicates; entire batch ingest halted

**Reason**: At least one of your articles matched two or more other articles already in DOAJ, and as a result we don't know which one to update.

**Resolution**: Ensure that all your articles have the correct DOI and Fulltext links. If you still don't have any luck, please [contact us](/contact/) with the details; we may need to clean up your existing articles manually.
