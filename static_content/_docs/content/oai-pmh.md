## Journal feed

{:.tabular-list}
- `Identify`
  - Access the [base Identify endpoint](/oai?verb=Identify).
- `ListSets`
  - DOAJ provides all its subject classifications as OAI-PMH sets, so you can harvest just those you are interested in. Access the [full list of the sets](/oai?verb=ListSets).
- `ListMetadataFormats`
  - DOAJ currently supports only `oai_dc`; access [the metadata formats](/oai?verb=ListMetadataFormats).

The metadata held by DOAJ is mapped to Dublin Core in the OAI-PMH feed, with the following interpretations for each Journal field:

| Dublin Core   | Meaning within DOAJ                                                                                                                                                                                                                                                                                      |
|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `title`       | The title of the journal                                                                                                                                                                                                                                                                                 |
| `identifier`  | The ISSNs of the journal \(both print and electronic\) or a link back to the DOAJ record for this journal                                                                                                                                                                                                |
| `subject`     | Free\-text keywords or formal subject classifications\. Formal classifications are prefixed by their scheme \(e\.g\. CLASSIFICATION:Science\), except in the case of Library of Congress Classification\. LCC subjects are denoted by an additional attribute on this element, xsi:type="dcterms:LCSH"\. |
| `language`    | The languages that can appear in this journal                                                                                                                                                                                                                                                            |
| `relation`    | Links to related resources (if present): the journal home page, open access statement, author instructions, aims, and waiver pages                                                                                                                                                                                                     |
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

| Date changes were made live | Changes                                                                                                                                                                                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 20 April 2015               | `subject` elements which represent a Library of Congress Classification \(LCC\) topic will now be marked with an additional OAI DC\-compliant attribute to denote this: `xsi:type="dcterms:LCSH"`\. LCC subjects will no longer be prefixed by `LCC:`\. |
| 13 December 2013            | Initial release                                                                                                                                                                                                                                         |

---

## Article feed

{:.tabular-list}
- `Identify`
  - Access the [base Identify endpoint](http://www.doaj.org/oai.article?verb=Identify).
- `ListSets`
  - DOAJ provides all its subject classifications as OAI-PMH sets, so you can harvest just those you are interested in. Access the [full list of the sets](http://www.doaj.org/oai.article?verb=ListSets).
- `ListMetadataFormats`
  - DOAJ currently supports the `oai_dc` and `oai_doaj` formats; access [the metadata formats](http://www.doaj.org/oai.article?verb=ListMetadataFormats).

### Dublin Core OAI Article format (`OAI_DC`)

The metadata held by DOAJ is mapped to Dublin Core in the OAI-PMH feed, with the following interpretations for each Article field:

| Dublin Core   | Meaning within DOAJ                                                                                                                                                                                                                                                                                           |
|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `title`       | The title of the article\.                                                                                                                                                                                                                                                                                    |
| `identifier`  | The ISSNs of the journal the article appears in \(both print and electronic\), the DOI of the article, or a link back to the DOAJ record for this article\.                                                                                                                                                   |
| `subject`     | Free\-text keywords or formal subject classifications\. Formal classifications are prefixed by their scheme \(e\.g\. `CLASSIFICATION:Science`\), except in the case of Library of Congress Classification\. LCC subjects are denoted by an additional attribute on this element, `xsi:type="dcterms:LCSH"`\. |
| `language`    | The languages that the journal publishing this article publishes in\. Does not necessarily strictly denote the language of this article, and there may be multiple language fields provided\.                                                                                                                 |
| `relation`    | Links to related resources: the full\-text url                                                                                                                                                                                                                                                                |
| `provenance`  | Includes information about the journal's content re\-use policy\. Will be one of the Creative Commons licences\. This does not necessarily indicate the article's re\-use policy\.                                                                                                                            |
| `publisher`   | The publisher/provider of the journal this article appears in\.                                                                                                                                                                                                                                               |
| `type`        | The type of the object; always contains "article"                                                                                                                                                                                                                                                             |
| `date`        | The approximate date of publication\.                                                                                                                                                                                                                                                                         |
| `description` | The article's abstract\.                                                                                                                                                                                                                                                                                      |
| `creator`     | The article's authors, may contain an optional attribute id for ORCID iD\.                                                                                                                                                                                                                                    |

#### Example of a record

```xml
<record>
  <header xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <identifier>
      oai:doaj.org/article:2f032c66cd6047bdadaf0eddd7ab3341
    </identifier>
    <datestamp>2013-12-10T02:01:04Z</datestamp>
    <setSpec>TENDOlB1YmxpYyBhc3BlY3RzIG9mIG1lZGljaW5l</setSpec>
    <setSpec>TENDOk1lZGljaW5l</setSpec>
    <setSpec>RE9BSjpQdWJsaWMgSGVhbHRo</setSpec>
    <setSpec>RE9BSjpIZWFsdGggU2NpZW5jZXM~</setSpec>
  </header>
  <metadata xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <oai_dc:dc xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
      <dc:title>
        Prevalência e fatores associados ao consumo de cigarros entre estudantes de escolas estaduais do ensino médio de Santa Maria, Rio Grande do Sul, Brasil, 2002
      </dc:title>
      <dc:identifier>0102-311X</dc:identifier>
      <dc:identifier>1678-4464</dc:identifier>
      <dc:identifier>
        http://doaj.org/search?source=%7B%22query%22%3A%7B%22bool%22%3A%7B%22must%22%3A%5B%7B%22term%22%3A%7B%22id%22%3A%222f032c66cd6047bdadaf0eddd7ab3341%22%7D%7D%5D%7D%7D%7D
      </dc:identifier>
      <dc:date>2006-01-01T00:00:00Z</dc:date>
      <dc:relation>
        http://www.scielo.br/scielo.php?script=sci_arttext&pid=S0102-311X2006000800010
      </dc:relation>
      <dc:description>
        O tabagismo é a segunda principal causa mundial de morte, sendo responsável pela morte de um a cada dez adultos (5 milhões por ano). Se os padrões atuais se mantiverem, em 2020 o tabagismo será a causa de 10 milhões de óbitos anuais, segundo a Organização Mundial da Saúde. Realizou-se um estudo transversal, em 2002, no qual foram entrevistados 459 estudantes de oito escolas do ensino médio estadual em Santa Maria, Rio Grande do Sul, Brasil, para determinar a prevalência e os fatores associados ao tabagismo, obtendo-se um modelo logístico multivariável descrevendo como as chances de ser fumante estão relacionadas com as variáveis investigadas. A prevalência encontrada para o tabagismo foi de 18% (IC95%: 14,6-21,7), sendo que os estudantes começam a fumar, em média, aos 14 anos. Os resultados permitem concluir que os estudantes das escolas estaduais de Santa Maria começam a fumar precocemente, sendo influenciados pelos amigos fumantes (OR = 4,37; p = 0,000), pela renda familiar mensal (OR = 2,04; p = 0,013) e idade (OR = 1,86; p = 0,031), destacando-se a necessidade de se trabalhar, preventivamente, no grupo de risco observado.
      </dc:description>
      <dc:creator>Zanini Roselaine Ruviaro</dc:creator>
      <dc:creator id="https://orcid.org/0000-0001-1234-1234">Moraes Anaelena Bragança de</dc:creator>
      <dc:creator>Trindade Ana Cláudia Antunes</dc:creator>
      <dc:creator id="https://orcid.org/0000-0001-1111-2222">Riboldi João</dc:creator>
      <dc:creator>Medeiros Lídia Rosi de</dc:creator>
      <dc:publisher>
        Escola Nacional de Saúde Pública, Fundação Oswaldo Cruz
      </dc:publisher>
      <dc:subject>Tabagismo</dc:subject>
      <dc:subject>Estudantes</dc:subject>
      <dc:subject>Estudos Transversais</dc:subject>
      <dc:type>article</dc:type>
      <dc:subject>DOAJ:Public Health</dc:subject>
      <dc:subject>DOAJ:Health Sciences</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">Diseases of the musculoskeletal system</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">RC925-935</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">Specialties of internal medicine</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">RC581-951</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">Internal medicine</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">RC31-1245</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">Medicine</dc:subject>
      <dc:subject xsi:type="dcterms:LCSH">R</dc:subject>
      <dc:subject>SOME_NONLCC_FORMAL_CLASSIFICATION:term</dc:subject>
      <dc:language>English</dc:language>
      <dc:language>Spanish</dc:language>
      <dc:language>Portuguese</dc:language>
      <dc:rights>CC BY-NC</dc:rights>
    </oai_dc:dc>
  </metadata>
</record>
```

#### Revision history

| Date changes were made live                                                                                                                                                                                                                       | Changes         |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|
| 22 August 2016                                                                                                                                                                                                                                    | The `dc:rights` element was removed, as it was technically inaccurate \- it represented the Journal's overall licence policy, not the specific rights for the article\. This information is now in `dc:provenance`\. |
| 20 April 2015                                                                                                                                                                                                                                     | The `identifier` element will now point to the DOAJ article page rather than the `/search` page\. E\.g\. [`https://doaj.org/article/0000178c89214dc8b82df1a25c0c478e`](https://doaj.org/article/0000178c89214dc8b82df1a25c0c478e) <br/><br/>Up to two new `relation` elements will appear for each article, containing URL\-s to the Table of Contents page for the article's journal\. The page can be reached via both print ISSN and E\-ISSN, so up to two such links might appear\. <br/><br/>`subject` elements which represent a Library of Congress Classification \(LCC\) topic will now be marked with an additional OAI DC\-compliant attribute to denote this: `xsi:type="dcterms:LCSH"`\. LCC subjects will no longer be prefixed by `LCC:`\. |
| 13 December 2013                                                                                                                                                                                                                                  | Initial release |

### DOAJ OAI Article format (`OAI_DOAJ`)

The following fields are available (not every article will have all the information):

| DOAJ OAI field      | Meaning                                                                                                                                                                                                                                                                                       |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `language`          | The languages that the journal publishing this article publishes in\. Does not necessarily strictly denote the language of this article\. Only the first language the journal publishes in is provided, even when multiple are recorded on the journal record\.                               |
| `publisher`         | The publisher/provider of the journal this article appears in\.                                                                                                                                                                                                                               |
| `journalTitle`      | The title of the journal the article appears in\.                                                                                                                                                                                                                                             |
| `issn`              | The print ISSN of the journal the article appears in\.                                                                                                                                                                                                                                        |
| `eissn`             | The E\-ISSN of the journal the article appears in\.                                                                                                                                                                                                                                           |
| `publicationDate`   | The article's date of publication\. In `YYYY-MM-DD` format\.                                                                                                                                                                                                                                  |
| `volume`            | The journal volume the article appears in\.                                                                                                                                                                                                                                                   |
| `issue`             | The journal issue the article appears in\.                                                                                                                                                                                                                                                    |
| `startPage`         | The number of the journal page the article starts on\.                                                                                                                                                                                                                                        |
| `endPage`           | The number of the journal page the article ends on\.                                                                                                                                                                                                                                          |
| `doi`               | The article's Digital Object Identifier\.                                                                                                                                                                                                                                                     |
| `publisherRecordId` | An ID assigned to this article by its publisher and supplied to DOAJ via metadata upload\. Not guaranteed to be unique or otherwise useful in any context, simply a way for the publisher to refer to this article\.                                                                          |
| `documentType`      | Will never be present in a `OAI_DOAJ` article record, even though it's in the XML schema\.                                                                                                                                                                                                     |
| `title`             | The title of the article                                                                                                                                                                                                                                                                      |
| `authors`           | A list of `<author>` elements\. Each <author> element can have a `<name>`, `<email>`, `<affiliationId>` and `<orcid_id>` child elements\. The `affiliationId` refers to one of the affiliations in the `affiliationsList` element described below\.                                                        |


#### Example of a record

```xml
<record>
  <header xmlns:oai_doaj="http://doaj.org/features/oai_doaj/1.0/">
    <identifier>oai:doaj.org/article:2a48ccce13c546ceab0c6bc5b74d433d</identifier>
    <datestamp>2015-03-21T20:28:31Z</datestamp>
    <setSpec>TENDOkRpc2Vhc2VzIG9mIHRoZSBtdXNjdWxvc2tlbGV0YWwgc3lzdGVt</setSpec>
    <setSpec>TENDOlNwZWNpYWx0aWVzIG9mIGludGVybmFsIG1lZGljaW5l</setSpec>
    <setSpec>TENDOkludGVybmFsIG1lZGljaW5l</setSpec>
    <setSpec>TENDOk1lZGljaW5l</setSpec>
    <setSpec>dGVzdDp0ZXJt</setSpec>
  </header>
  <metadata xmlns:oai_doaj="http://doaj.org/features/oai_doaj/1.0/">
    <oai_doaj:doajArticle xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd http://doaj.org/features/oai_doaj/1.0/ https://doaj.org/static/doaj/doajArticles.xsd">
      <oai_doaj:language>ger</oai_doaj:language>
      <oai_doaj:publisher>Verlag Krause und Pachernegg GmbH</oai_doaj:publisher>
      <oai_doaj:journalTitle>Journal f&#xFC;r Mineralstoffwechsel</oai_doaj:journalTitle>
      <oai_doaj:issn>1023-7763</oai_doaj:issn>
      <oai_doaj:eissn>1680-9408</oai_doaj:eissn>
      <oai_doaj:publicationDate>1998-01-01</oai_doaj:publicationDate>
      <oai_doaj:volume>5</oai_doaj:volume>
      <oai_doaj:issue>1</oai_doaj:issue>
      <oai_doaj:startPage>25</oai_doaj:startPage>
      <oai_doaj:endPage>29</oai_doaj:endPage>
      <oai_doaj:publisherRecordId>648</oai_doaj:publisherRecordId>
      <oai_doaj:title>Leitfaden zur medikament&#xF6;sen Standardtherapie in der Osteoporose</oai_doaj:title>
      <authors>
        <author>
          <name>Stevo Popovic</name>
          <affiliationId>0</affiliationId>
          <orcid_id>https://orcid.org/0000-0001-1234-1234</orcid_id>
        </author>
        <author>
          <name>Dusko Bjelica</name>
          <affiliationId>1</affiliationId>
        </author>
        <author>
          <name>Gabriela Doina Tanase</name>
          <affiliationId>2</affiliationId>
          <orcid_id>https://orcid.org/0000-0001-1111-2222</orcid_id>
        </author>
        <author>
          <name>Rajko Mila&#x161;inovi&#x107;</name>
          <affiliationId>3</affiliationId>
        </author>
      </authors>
      <affiliationsList>
        <affiliationName affiliationId="0">University of Montenegro, Faculty for Sport and Physical Education, Nik&#x161;i&#x107;, Montenegro</affiliationName>
        <affiliationName affiliationId="1">University of Montenegro, Faculty for Sport and Physical Education, Nik&#x161;i&#x107;, Montenegro</affiliationName>
        <affiliationName affiliationId="2">University of Montenegro, Faculty for Sport and Physical Education, Nik&#x161;i&#x107;, Montenegro</affiliationName>
        <affiliationName affiliationId="3">University of Novi Sad, ACIMSR, Novi Sad, Serbia</affiliationName>
      </affiliationsList>
      <oai_doaj:fullTextUrl format="pdf">http://www.kup.at/kup/pdf/648.pdf</oai_doaj:fullTextUrl>
      <oai_doaj:keywords>
        <oai_doaj:keyword>Empfehlung</oai_doaj:keyword>
        <oai_doaj:keyword>Mineralstoffwechsel</oai_doaj:keyword>
        <oai_doaj:keyword>Osteoporose</oai_doaj:keyword>
        <oai_doaj:keyword>Richtlinie</oai_doaj:keyword>
        <oai_doaj:keyword>Therapie</oai_doaj:keyword>
      </oai_doaj:keywords>
    </oai_doaj:doajArticle>
  </metadata>
</record>
```

#### Revision history

| Date changes were made live | Changes         |
|-----------------------------|-----------------|
| 20 April 2015               | Initial release |
