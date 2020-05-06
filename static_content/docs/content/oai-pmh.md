## Journal feed

{:.tabular-list}
- `Identify`
  - Access the [base Identify endpoint](http://www.doaj.org/oai?verb=Identify).
- `ListSets`
  - DOAJ provides all its subject classifications as OAI-PMH sets, so you can harvest just those you are interested in. Access the [full list of the sets](http://www.doaj.org/oai?verb=ListSets).
- `ListMetadataFormats`
  - DOAJ currently supports only `oai_dc`; access [the metadata formats](http://www.doaj.org/oai?verb=ListMetadataFormats).

The metadata held by DOAJ is mapped to Dublin Core in the OAI-PMH feed, with the following interpretations for each Journal field:

| Dublin Core   | Meaning within DOAJ                                                                                                                                                                                                                                                                                      |
|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `title`       | The title of the journal                                                                                                                                                                                                                                                                                 |
| `identifier`  | The ISSNs of the journal \(both print and electronic\) or a link back to the DOAJ record for this journal                                                                                                                                                                                                |
| `subject`     | Free\-text keywords or formal subject classifications\. Formal classifications are prefixed by their scheme \(e\.g\. CLASSIFICATION:Science\), except in the case of Library of Congress Classification\. LCC subjects are denoted by an additional attribute on this element, xsi:type="dcterms:LCSH"\. |
| `language`    | The languages that can appear in this journal                                                                                                                                                                                                                                                            |
| `relation`    | Links to related resources: the journal home page and the journal author\-pays link if relevant                                                                                                                                                                                                          |
| `rights`      | The journal's content re\-use policy\. Will be one of the Creative Commons licences                                                                                                                                                                                                                      |
| `publisher`   | The publisher/provider of the journal                                                                                                                                                                                                                                                                    |
| `type`        | The type of the object; always contains "journal"                                                                                                                                                                                                                                                        |

### Example of a record

```xml
<record>
  <header xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <identifier>
      oai:doaj.org/journal:9dfe4879964541069dff9bb6d15b65a2
    </identifier>
    <datestamp>2013-12-10T00:23:25Z</datestamp>
    <setSpec>TENDOkVjb25vbWljIHRoZW9yeS4gRGVtb2dyYXBoeQ~~</setSpec>
    <setSpec>TENDOlNvY2lhbCBTY2llbmNlcw~~</setSpec>
    <setSpec>RE9BSjpFY29ub21pY3M~</setSpec>
    <setSpec>RE9BSjpCdXNpbmVzcyBhbmQgRWNvbm9taWNz</setSpec>
  </header>
  <metadata xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <oai_dc:dc xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
      <dc:title>Croatian Economic Survey</dc:title>
      <dc:identifier>1330-4860</dc:identifier>
      <dc:identifier>1846-3878</dc:identifier>
      <dc:identifier>
        http://doaj.org/search?source=%7B%22query%22%3A%7B%22bool%22%3A%7B%22must%22%3A%5B%7B%22term%22%3A%7B%22id%22%3A%229dfe4879964541069dff9bb6d15b65a2%22%7D%7D%5D%7D%7D%7D
      </dc:identifier>
      <dc:subject>economics</dc:subject>
      <dc:subject>post-socialist Europe</dc:subject>
      <dc:subject>comparative economics</dc:subject>
      <dc:subject>policy formulation</dc:subject>
      <dc:language>English</dc:language>
      <dc:relation>
        http://www.eizg.hr/en-US/Croatian-Economic-Survey-26.aspx
      </dc:relation>
      <dc:publisher>The Institute of Economics, Zagreb</dc:publisher>
      <dc:relation>
        http://www.eizg.hr/en-US/Croatian-Economic-Survey-26.aspx
      </dc:relation>
      <dc:publisher>The Institute of Economics, Zagreb</dc:publisher>
      <dc:date>2013-11-06T15:18:52Z</dc:date>
      <dc:type>journal</dc:type>
      <dc:subject xsi:type="dcterms:LCSH">Diseases of the musculoskeletal system</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">RC925-935</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">Specialties of internal medicine</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">RC581-951</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">Internal medicine</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">RC31-1245</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">Medicine</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">R</dc:subject>
      <dc:subject>SOME_NONLCC_FORMAL_CLASSIFICATION:term</dc:subject>
      <dc:subject>DOAJ:Economics</dc:subject>
      <dc:subject>DOAJ:Business and Economics</dc:subject>
    </oai_dc:dc>
  </metadata>
</record>
```

### Revision history

| Date changes were made live | Changes                                                                                                                                                                                                                                           |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 20 April 2015               | Subject elements which represent a Library of Congress Classification \(LCC\) topic will now be marked with an additional OAI DC\-compliant attribute to denote this: `xsi:type="dcterms:LCSH"`\. LCC subjects will no longer be prefixed by LCC:\. |
| 13 December 2013            | Initial release                                                                                                                                                                                                                                   |

---

## Article feed

... 
