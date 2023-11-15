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
- **Help available?** Yes
  - For creating XML, see our [DOAJ XML](/docs/xml/) documentation
  - For help with [error messages when uploading XML](/publisher/help#explanations)
  - For help with Crossref XML, contact [Crossref support](mailto:support@crossref.org)
- **Testing available**: on a case-by-case basis and only for [publisher supporters](/support/publisher-supporters/)
- **Documentation** [DOAJ XML](/docs/xml/), [Crossref 5.3.1 XML](https://www.crossref.org/documentation/schema-library/metadata-deposit-schema-5-3-1/), [Crossref 4.4.2 XML](https://www.crossref.org/documentation/schema-library/resource-only-deposit-schema-4-4-2/)
- **FAQS** No
- **OJS plugin available?** Yes. Refer to [PKP documentation](https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin)https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin.
- **OJS support**: for help, refer to [the OJS Technical Forum](https://forum.pkp.sfu.ca/c/questions/5)https://forum.pkp.sfu.ca/c/questions/5
- **Troubleshooting uploads**: please [submit a bug report](https://github.com/DOAJ/doaj/issues/new/choose) (via GitHub) or [contact us](mailto:helpdesk@doaj.org) with the following details:
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

## FAQs for metadata uploads

When you upload article XML to us, we will let you know if there are problems with the file
