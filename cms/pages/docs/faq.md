---
layout: sidenav
title: Metadata help
section: About
toc: true
sticky_sidenav: true
featuremap: ~~FAQ:Fragment~~

---

After your journal is indexed in DOAJ and you start to upload article metadata to us, we generate journal and article metadata. We make these publicly and freely available via different methods:

- Our [Atom feed](https://staticdoaj.cottagelabs.com/feed)
- Our [OAI-PMH service](https://staticdoaj.cottagelabs.com/docs/oai-pmh/)
- [A journal CSV](https://staticdoaj.cottagelabs.com/csv) file (updates every 60 minutes)
- Our [API](https://staticdoaj.cottagelabs.com/docs/api/)
- On our website

Our metadata is collected and incorporated into commercial discovery systems, library discovery portals and search engines around the world. Here are some of them:
- OCLC
- EBSCO products
- Clarivate's Proquest and Ex Libris products
- Clarivate's Web of Science
- SCOPUS
- Google Scholar
- Google
- Dimensions
- CONSER's MARC records

## Uploading article metadata

We are one of the most trusted and reliable providers of metadata about open access journals and articles. When publishers upload their article metadata to us, it increases the visibility of the journal and the articles.

Choose how you want to upload article metadata to us.

### API

- **Speed and efficiency**: high
- **Level**: difficult
- **Formats accepted**: JSON
- **Maximum upload limit**: 50MB
- **Requirements**:
  - An API that will connect to ours
  - The API key from [your DOAJ account](/account/login)
- **Help available?** Yes, via one of our API groups; search for 'Google Group DOAJ API' in your browser.
- **Testing available**: on a case-by-case basis and only for [publisher supporters](/support/publisher-supporters/)
- **Documentation** [Yes](/docs/api/)
- **FAQS** [Yes](/api/v3/docs#api-faq)
- **OJS plugin available?** Yes. Refer to [PKP documentation](https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin)https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin.
- **OJS support**: for help, refer to [the OJS Technical Forum](https://forum.pkp.sfu.ca/c/questions/5)https://forum.pkp.sfu.ca/c/questions/5
- **Troubleshooting uploads**: please [submit a bug report](https://github.com/DOAJ/doaj/issues/new/choose) (via GitHub) or [contact us](mailto:helpdesk@doaj.org) with the following details:
  - The time of the file upload. (If you saw the error more than 12 hours ago, please try the upload again before you contact us.)
  - Whether the error happened once or repeatedly
  - The exact error message that appeared during the upload. Include a screenshot.
  - The DOAJ account ID that you are logged in with. You will find this under 'Settings' in the Dashboard dropdown menu.
  - The file(s) you had problems with
  - The ISSN(s) of the journal

### XML

- **Speed and efficiency**: medium
- **Level**: medium
- **Formats accepted**: DOAJ and Crossref XML
- **Maximum upload limit**: 50MB
- **Requirements**:
  - A way to generate structured XML and validate it against the required XSD file.
  - The XSD files: [DOAJ](/static/doaj/doajArticles.xsd), [Crossref 5.3.1](/static/crossref/crossref5.3.1.xsd), [Crossref 4.4.2](/static/crossref/crossref4.4.2.xsd)
- **Testing available**: on a case-by-case basis and only for [publisher supporters](/support/publisher-supporters/)
- **Documentation** [DOAJ XML](/docs/xml/), [Crossref 5.3.1 XML](https://www.crossref.org/documentation/schema-library/metadata-deposit-schema-5-3-1/), [Crossref 4.4.2 XML](https://www.crossref.org/documentation/schema-library/resource-only-deposit-schema-4-4-2/)
- **FAQS** No
- **OJS plugin available?** Yes. Refer to [PKP documentation](https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin)https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin.
- **OJS support**: for help, refer to [the OJS Technical Forum](https://forum.pkp.sfu.ca/c/questions/5)https://forum.pkp.sfu.ca/c/questions/5
- **Help available?** Yes
  - For creating XML, see our [DOAJ XML](/docs/xml/) documentation
  - For explanations of [specific error messages when uploading XML](/publisher/help#explanations)
  - For help with Crossref XML, contact [Crossref support](mailto:support@crossref.org)
- **Troubleshooting uploads**: if our [error message definitions](/publisher/help#explanations) don't help you, please [submit a bug report](https://github.com/DOAJ/doaj/issues/new/choose) (via GitHub) or [contact us](mailto:helpdesk@doaj.org) with the following details:
  - The time of the file upload. (If you saw the error more than 12 hours ago, please try the upload again before you contact us.)
  - Whether the error happened once or repeatedly
  - Whether you are uploading DOAJ or Crossref XML
  - Whether you are uploading a file or uploading from a link
  - The exact error message shown in the 'Notes' column of the [History of uploads section](/publisher/uploadfile), including the detail under the 'show error details' link.
  - A screenshot of the error message with the 'show error details' link expanded.
  - The DOAJ account ID that you are logged in with
  - The file(s) you had problems with 

### Enter article metadata manually

- **Speed and efficiency**: low
- **Level**: easy
- **Formats accepted**: text, entered via [our webform](/publisher/metadata)
- **Maximum upload limit**: N/A
- **Requirements**:
  - Plain text only
  - No email addresses
  - The abstract metadata for the article: title, full-text URL, DOI (if applicable), author names, ORCiD (if applicable), affiliations, publication date, ISSN(s), Volume/Issue/Page (if applicable), abstract 
- **Help available?** Yes. [Contact our Help Desk](mailto:helpdesk@doaj.org).
- **Testing available**: on a case-by-case basis and only for [publisher supporters](/support/publisher-supporters/)
- **Documentation** No
- **Troubleshooting**: you must be careful to enter the Print ISSN and Electronic ISSN in the right field.

## Help with metadata uploads

### My authors have multiple affiliations

We are currently unable to display more than one affiliation per author. We are investigating how we can change this. More information will be posted on our blog.

### My article abstracts are in more than one language

Our XML format only supports one language for Article Title and Abstract. We are working on a solution that will allow multiple languages to be uploaded to us and displayed.

Metadata containing multiple languages can still be uploaded to us. However, you cannot choose which language is displayed. Please only send us one language to avoid your articles being displayed in a mixture of languages.

### I am seeing a 403 forbidden error

You may see the 403 forbidden error for different reasons. These apply to both the API and uploading XML.

- ISSNs
  - You may be sending us an extra ISSN that we don’t have in your journal record.
  - You may be sending only one ISSN, but we have two in the journal record.
  - We may have the journal's ISSNs in an old version of your journal record.
- Wrong account
  - You may be sending us an ISSN that belongs to a journal attached to a different account.
- You are trying to update an article's Full Text URL (FTUs) or DOI
  - Two articles with the same FTU or DOI are not allowed.
  - Please contact us if you want to update the URLs or DOIs of your articles. We need to delete the old versions first.

### I am seeing a timeout or a 'blocked' error

If you see a timeout error, please try splitting your upload into smaller files, even if your file is under our 50MB limit. Many may be uploading content to us, and the server is taking longer than usual to collect your file.

If you see a screen from Cloudflare that says you have been blocked, please [contact us](mailto:helpdesk@doaj.org). Include a screenshot that shows the Ray ID at the very bottom of the page. We need this to troubleshoot the problem.

## Downloading your metadata

You can download our metadata about your journal by [downloading our CSV](https://doaj.org/csv).

You can download your article metadata by [using our API](https://doaj.org/docs/api/) or by using our [public data dump service](/docs/public-data-dump/).

## Using a CSV file to update your journal metadata

If you received a CSV file from us, please complete it as soon as possible. The file sent to you contains a cover sheet with instructions. 

Before you send us the file, you will need to [validate it](/publisher/journal-csv) first. Some changes will cause the validation to fail:

- don't save the file in any format other than CSV
- don't change an ISSN or the Title of a journal. To do this, contact [Help Desk](mailto:helpdesk@doaj.org).
- don't add a new journal to the file. To do this, [submit a new application](/apply/).
- don't change the title of a column
- don't include anything in the column other than what is required

Deleting a journal from the file will mean no update happens; it will not remove a journal from your account. To do this, contact [Help Desk](mailto:helpdesk@doaj.org).

### Validating your file

Before emailing your file to us, you will need to validate it. Do this in your Publisher Dashboard on the 'Validate your CSV' tab. If you do not see the tab, contact [Help Desk](mailto:helpdesk@doaj.org).

As well as the five points above, here are some tips to help you produce a valid CSV file:

- be careful not to add spaces before or after the information you put into the spreadsheet. This can cause the validation to fail.
