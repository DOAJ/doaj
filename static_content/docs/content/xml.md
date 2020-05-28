When publishers upload article metadata to DOAJ, the data must be in one of two XML formats. 

Article metadata is provided to us on the understanding that it will then be available for free, to be distributed to any third party who wants it.

We do not check metadata quality as we ingest it — this is the publisher's responsibility — so any errors (for example, typos in author names, URLs, or DOI) will not be corrected. Users of our metadata may contact us to ask for metadata to be  corrected.

## Uploading an XML file

+ First convert your article metadata into an accepted XML format: DOAJ or Crossref.
  + It must be structured correctly.
  + Its format must follow a set of rules laid out in the [DOAJ XML schema file](/static/doaj/doajArticles.xsd), or the rules laid out in [Crossref’s schema file](https://support.crossref.org/hc/en-us/articles/214530063-Crossref-XSD-schema-quick-reference).
+ If you are creating DOAJ XML manually, try [formatting](https://jsonformatter.org/xml-formatter) and [validating](https://www.xmlvalidation.com/) the file before you upload it to us.
+ If you are exporting XML from an OJS plugin, you can [upload the file](/publisher/uploadfile) immediately.

## List of DOAJ XML elements

Here is a table of each element in the DOAJ XML file. It shows you whether or not the element is required by the DOAJ schema. Providing as much information in the metadata as possible ensures a more complete record in our database and allows the record to be distributed more easily to other services.

| Element            | Requirement                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| Language, ISO code | Optional, max 1                                                             |
| Publisher          | Optional, max 1                                                             |
| **Journal title**  | Required, only 1                                                            |
| ISSN               | Optional, max. 1 <br>Either the ISSN or the EISSN must be present, or both  |
| EISSN              | Optional, max. 1  <br>Either the ISSN or the EISSN must be present, or both |
| **Publication date** | Required, only 1                                                            |
| Volume number      | Optional, max. 1                                                            |
| Issue number       | Optional, max. 1                                                            |
| Start page         | Optional, max. 1                                                            |
| End page           | Optional, max. 1                                                            |
| DOI                | Optional, max. 1                                                            |
| Document type      | Optional, max. 1                                                            |
| **Title**          | Required, 1 or more                                                         |
| Authors            | Optional                                                                    |
| Affiliations       | Optional                                                                    |
| Abstracts          | Optional                                                                    |
| **Full-text URL**  | Required, only 1                                                            |
| Keywords           | Optional                                                                    |

There are [European Union restrictions](https://ec.europa.eu/info/law/law-topic/data-protection/reform/what-personal-data_en) on distribution of personal data, such as email addresses. DOAJ doesn’t need or display author email addresses so please don’t send them to us in the XML.

## Example DOAJ XML File

The example file below contains only one record.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<records>
  <record>
    <language>eng</language>
    <publisher>Popular Chemistry</publisher>
    <journalTitle>Botanical Magazine</journalTitle>
    <issn>17497221</issn>
    <eissn>17497234</eissn>
    <publicationDate>2002-09-30</publicationDate>
    <volume>98</volume>
    <issue>2</issue>
    <startPage>1234</startPage>
    <endPage>1235</endPage>
    <doi>1234567</doi>
    <publisherRecordId>12345</publisherRecordId>
    <documentType>article</documentType>
    <title language="eng">Roses and Lilies</title>
    <authors>
      <author>
        <name>Fritz Haber</name>
        <affiliationId>1</affiliationId>
        <affiliationId>2</affiliationId>
        <affiliationId>3</affiliationId>
      </author>
    </authors>
    <affiliationsList>
      <affiliationName affiliationId="1">University of A</affiliationName>
      <affiliationName affiliationId="2">University of B</affiliationName>
      <affiliationName affiliationId="3">University of C</affiliationName>
    </affiliationsList>
    <abstract language="eng">The catalytic formation of ammonia from hydrogen and atmospheric nitrogen under conditions of high temperature and high pressure.</abstract>
    <fullTextUrl format="pdf">http://www.science.org/articles/HaberBosch.pdf</fullTextUrl>
    <keywords language="eng">
      <keyword>garden</keyword>
      <keyword>rose</keyword>
    </keywords>
  </record>
  <record>...</record>
  ...
</records>
```

| Element             | Comment                                                                                                                                                                                                               |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `record`            | Represents a single record.                                                                                                                                                                                           |
| `language`          | The language tag content must conform to the ISO 639-2b standard. [Find the correct language code](https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes).                                                            |
| `issn`  <br>`eissn` |                                                                                                                                                                                                                       |
| `title language=""` | If the title occurs in more than one language, then you may include those in your XML. However, we can only display one language. The title tag’s language attribute must be set according to the ISO 639-2b standard. |
| `name`              | The author name should be formatted First Name, Middle Name, Last Name                                                                                                                                                |
| `affiliationId`     | Note that the `affiliationId` numbers denote the affiliations in the `affiliationslist` further down.                                                                                                               |


---

## The doajArticles.xsd schema file

The [doajArticles.xsd](http://www.doaj.org/static/doaj/doajArticles.xsd) file specifies what may or may not be uploaded to the database.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:iso_639-2b="https://doaj.org/schemas/iso_639-2b/1.0">
  <xs:import namespace="https://doaj.org/schemas/iso_639-2b/1.0" schemaLocation="https://doaj.org/static/doaj/iso_639-2b.xsd">
    <xs:annotation>
      <xs:documentation>
        This schema determines allowable xml file formats
        for upload into the DOAJ database.
        The schema uses imported codes for the representation
        of names of languages devised by the International
        Organization for Standardization (ISO) 639-2/B
        (bibliographic codes). Please note that when two
        codes separated by a dash occurs in the iso 639-2
        table then only the first code is used, the
        bibliographic one. The terminology code that comes
        second is omitted.
      </xs:documentation>
    </xs:annotation>
  </xs:import>
  <xs:element name="records">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="record" type="recordType" maxOccurs="unbounded" />
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="recordType">
    <xs:sequence>
      <xs:element name="language" type="iso_639-2b:LanguageCodeType" minOccurs="0" />
      <xs:element name="publisher" type="xs:string" />
      <xs:element name="journalTitle" type="xs:string" />
      <xs:element name="issn" minOccurs="0">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:pattern value="[d0-9]{4}-{0,1}[0-9]{3}[0-9xX]{1}" />
          </xs:restriction>
        </xs:simpleType>
      </xs:element>
      <xs:element name="eissn" minOccurs="0">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:pattern value="[0-9]{4}-{0,1}[0-9]{3}[0-9xX]{1}" />
          </xs:restriction>
        </xs:simpleType>
      </xs:element>
      <xs:element name="publicationDate">
        <xs:simpleType>
          <xs:restriction base="xs:string">
            <xs:pattern value="[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?" />
          </xs:restriction>
        </xs:simpleType>
      </xs:element>
      <xs:element name="volume" type="xs:string" minOccurs="0" />
      <xs:element name="issue" type="xs:string" minOccurs="0" />
      <xs:element name="startPage" type="xs:string" minOccurs="0" />
      <xs:element name="endPage" type="xs:string" minOccurs="0" />
      <xs:element name="doi" type="xs:string" minOccurs="0" />
      <xs:element name="publisherRecordId" type="xs:string" minOccurs="0" />
      <xs:element name="documentType" type="xs:string" minOccurs="0" />
      <xs:element name="title" minOccurs="1" maxOccurs="unbounded">
        <xs:complexType>
          <xs:simpleContent>
            <xs:extension base="xs:string">
              <xs:attribute name="language" type="iso_639-2b:LanguageCodeType" />
            </xs:extension>
          </xs:simpleContent>
        </xs:complexType>
      </xs:element>
      <xs:element name="authors" minOccurs="0" maxOccurs="1">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="author" minOccurs="0" maxOccurs="unbounded">
              <xs:complexType>
                <xs:sequence>
                  <xs:element name="name" type="xs:string" />
                  <xs:element name="email" type="xs:string" minOccurs="0" />
                  <xs:element name="affiliationId" minOccurs="0" maxOccurs="unbounded" />
                </xs:sequence>
              </xs:complexType>
            </xs:element>
          </xs:sequence>
        </xs:complexType>
      </xs:element>
      <xs:element name="affiliationsList" minOccurs="0" maxOccurs="1">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="affiliationName" minOccurs="0" maxOccurs="unbounded">
              <xs:complexType>
                <xs:simpleContent>
                  <xs:extension base="xs:string">
                    <xs:attribute name="affiliationId" type="xs:string" use="required" />
                  </xs:extension>
                </xs:simpleContent>
              </xs:complexType>
            </xs:element>
          </xs:sequence>
        </xs:complexType>
      </xs:element>
      <xs:element name="abstract" minOccurs="0" maxOccurs="unbounded">
        <xs:complexType>
          <xs:simpleContent>
            <xs:extension base="xs:string">
              <xs:attribute name="language" type="iso_639-2b:LanguageCodeType" />
            </xs:extension>
          </xs:simpleContent>
        </xs:complexType>
      </xs:element>
      <xs:element name="fullTextUrl">
        <xs:complexType>
          <xs:simpleContent>
            <xs:extension base="xs:anyURI">
              <xs:attribute name="format" />
            </xs:extension>
          </xs:simpleContent>
        </xs:complexType>
      </xs:element>
      <xs:element name="keywords" minOccurs="0" maxOccurs="unbounded">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="keyword" type="xs:string" minOccurs="0" maxOccurs="unbounded" />
          </xs:sequence>
          <xs:attribute name="language" type="iso_639-2b:LanguageCodeType" use="optional" />
        </xs:complexType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
```
