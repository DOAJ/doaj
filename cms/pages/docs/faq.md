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
- **Maximum upload limit**: 50 MB
- **Requirements**:
  - An API that will connect to ours
  - The API key from [your DOAJ account](/account/login)
- **Help available?** Yes, via one of our API groups; search for 'Google Group DOAJ API' in your browser.
- **Testing available**: on a case-by-case basis and only for [publisher supporters](/support/publisher-supporters/)
- **Documentation** [Yes](/docs/api/)
- **FAQS** [Yes](/api/v3/docs#api-faq)
- **OJS plugin available?** Yes. Refer to [PKP documentation](https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin)https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin.
- **OJS support**: for help, refer to [the OJS Technical Forum](https://forum.pkp.sfu.ca/c/questions/5)https://forum.pkp.sfu.ca/c/questions/5

### XML

- **Speed and efficiency**: medium
- **Level**: medium
- **Formats accepted**: JSON
- **Maximum upload limit**: [DOAJ XML](/docs/xml/), [Crossref 5.3.1 XML](https://www.crossref.org/documentation/schema-library/metadata-deposit-schema-5-3-1/), [Crossref 4.4.2 XML](https://www.crossref.org/documentation/schema-library/resource-only-deposit-schema-4-4-2/)
- **Requirements**:
  - A way to generate structured XML and validate it against the required XSD file.
  - The XSD files: [DOAJ](/static/doaj/doajArticles.xsd), [Crossref 5.3.1](/static/crossref/crossref5.3.1.xsd), [Crossref 4.4.2](/static/crossref/crossref4.4.2.xsd)
- **Help available?**
  - For [DOAJ XML](/docs/xml/)
  - For Crossref XML, contact [Crossref support](mailto:support@crossref.org)
- **Testing available**: on a case-by-case basis and only for [publisher supporters](/support/publisher-supporters/)
- **Documentation** [Yes](/docs/xml/)
- **FAQS** No
- **OJS plugin available?** Yes. Refer to [PKP documentation](https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin)https://docs.pkp.sfu.ca/admin-guide/3.3/en/data-import-and-export#doaj-export-plugin.
- **OJS support**: for help, refer to [the OJS Technical Forum](https://forum.pkp.sfu.ca/c/questions/5)https://forum.pkp.sfu.ca/c/questions/5
