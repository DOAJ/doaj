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
- **OJS plugin available?** Yes. Refer to [PKP documentation](https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin).
- **OJS support**: for help, refer to [the OJS Technical Forum](https://forum.pkp.sfu.ca/c/questions/5)
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
- **OJS plugin available?** Yes. Refer to [PKP documentation](https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin).
- **OJS support**: for help, refer to [the OJS Technical Forum](https://forum.pkp.sfu.ca/c/questions/5)
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

Our XML format only supports one language for 'Article Title' and 'Abstract'. We are researching a solution that allows multiple languages to be uploaded to us and displayed.

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

## Using a spreadsheet to update your journal metadata

If you received a spreadsheet from us, please complete it as soon as possible. The file sent to you contains a cover sheet with instructions, and more help is below. Once you have validated your file, you may email it back to us.

Before you send us the file, you must do two things:

1. Convert the spreadsheet to a CSV. To do this, you will need to first delete the instructions tab and then Save as CSV.
2. [Validate it](/publisher/journal-csv).

Here are some tips on how to ensure that your CSV file will pass validation:

- don't change an ISSN or Title of a journal. To do this, contact [Help Desk](mailto:helpdesk@doaj.org).
- don't add a new journal to the file. To do this, [submit a new application](/apply/).
- don't change the title of a column
- don't include anything in the column other than what is asked for on the instructions tab
- ensure no spaces are accidentally added before or after the information in each cell. This can cause the validation to fail.

Deleting a journal from the file will mean no update happens; it will not remove a journal from your account. To do this, contact [Help Desk](mailto:helpdesk@doaj.org).

### Validating your file

Before emailing the CSV to us, you must validate it. Do this in your Publisher Dashboard on the 'Validate your CSV' tab. If you do not see the tab, contact [Help Desk](mailto:helpdesk@doaj.org).

The following warnings may be seen after validating your CSV:

| Warning                                                                                                                | Explanation                                                                                                                                                                                                                         |
|------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| _Column name_ has mismatching case to expected header                                                                  | During editing, the case used in the column name has been changed. This is just a warning and does not need to be corrected for us to process the CSV correctly.                                                                    |
| _Column name_ is not a valid column header. Please revert it to match what was sent to you in the original file.       | During editing, the column name has been changed. The name must match exactly the column name in the spreadsheet sent to you.                                                                                                       |
| _Column name_ is a required column missing from this upload. Please refer to the original file and restore the column. | During editing, the column has been deleted. Please refer to the original spreadsheet and restore the column.                                                                                                                       |
| There is no journal record in DOAJ for ISSN(s) _issns_.  The record may not exist, or it may be withdrawn.             | The ISSN doesn't match a journal in DOAJ. Check it against the spreadsheet sent to you. You cannot add ISSNs to journals. If you think an ISSN is missing, contact Help Desk.                                                       | 
| Your account _account ID_ doesn't own the journal with ISSN(s) {issns}. You may not update it.                         | The journal may have transferred to another owner since you received your spreadsheet or you have accidentally changed the ISSN, which matches another journal in DOAJ. Refer to the spreadsheet sent to you and correct the ISSN.  |
| The data you supplied didn't change anything in the journal record.                                                    | You can ignore this message if you haven't updated anything for this journal.                                                                                                                                                       |
| You may not change _question_. Please revert it to match what was sent to you in the spreadsheet.                      | During editing, the question has been changed. The question must be exactly as it is in the spreadsheet sent to you. Please change it.                                                                                              |
| We couldn't understand the information in _question_ |                                                                 | The information in the cell doesn't match the formatting requirements. Check the Instructions tab in the spreadsheet sent to you.                                                                                                   |

From time to time, other validation errors might be seen if one of the cells contains completely incorrect information. For example, the cell should contain a URL but it contains text. These error messages are self-explanatory,, but contact Help Desk if you require help.
