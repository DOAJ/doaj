![cl logo](http://cottagelabs.com/media/cropped-Cottage-on-hill-bubble-smoke.jpg)
<br><br>
# OpenURL for the DOAJ

This work will extend the DOAJ application to accept incoming OpenURL requests and provide their target, via an ElasticSearch query. This will require a new endpoint to accept the requests, a parser to construct the queries, plus a method of showing the results.

### OpenURL 1.0 and OpenURL 0.1
OpenURL is a specification used to build links to resources. The OpenURL generalised Version 1.0 specification can be found [here][niso_standard] (pdf). It was based upon a previous version used specifically for scholarly works, now referred to as [0.1][.1_proposal] (pdf). This earlier version is still in use by some services and institutions, so this system will understand both, while recommending the newer syntax in documentation and by returning [HTTP code 301](http://en.wikipedia.org/wiki/HTTP_301) when the old syntax is used to indicate a permanent redirect.

OpenURL 1.0 requires the specification of a schema, specifies the format for keys used in the request. These can be found in the [NISO registry for OpenURL][oclc_reg].

#### Prior use in DOAJ
Some examples of incoming requests were captured by the DOAJ; the three shown here demonstrate the 0.1 syntax:

```
/doaj?func=openurl&genre=article&issn=13334395&date=2006&volume=5&issue=2&spage=165
/doaj?volume=1&date=2010&spage=151&issn=22157840&func=openurl&issue=2&genre=article
/openurl?genre=journal&issn=2158-2440&volume=4&issue=2&date=2014
```

Through discussion with EBSCO who use OpenURL, we caught a glimpse of how their link resolver stores information about a collection. A link template is stored, and filled out with known information such as ISSNs at query time. This means the DOAJ can choose and advertise the OpenURL version it uses, and the resolvers will be configured to access the right part of the site with the correct syntax.

The logged incoming requests will be used for testing in the project.

#### Endpoint location
The new endpoint to accept OpenURL requests will be created at ```/openurl``` (i.e. ```www.doag.org/openurl/```) and will accept queries only (no page to display). It will re-route the incoming query to the result landing page; the table of contents for journals, and a new page for articles (related to Public View of the Data project).

#### Choice of schema
For ease of use, and for improved readability, the schema used will use key-value pairs (key-encoded-values, kev) rather than XML. There is a schema already defined for journals (and articles) [available][reg_journal] in the OpenURL repository. Below is the last example request from the section above re-written using OpenURL 1.0 using the ```info:ofi/fmt:kev:mtx:journal``` schema:

```
/openurl?url_ver=Z39.88-2004&url_ctx_fmt=info:ofi/fmt:kev:mtx:ctx&rft_val_fmt=info:ofi/fmt:kev:mtx:journal&rft.genre=journal&rft.issn=2158-2440&rft.volume=4&rft.issue=2&rft.date=2014
```
Here, everything up to the ```&rft.genre``` tag is fixed - the OpenURL version used, the format for the ContextObject, and the journal metadata format. These are fixed because this system is *only* designed to parse these formats, along with the legacy OpenURL 0.1 syntax.

### Model for incoming OpenURL requests

OpenURL queries will be handled by building an object which can hold the incoming information, plus methods required to crosswalk to an ElasticSearch query. The data model is defined from the schema above and covers all valid keys in the chosen ```journal``` schema. The fields in the model all correspond to the schema key, which makes accessing them in the object for a known request more convenient. Although not all fields can be directly mapped to the DOAJ's models for journals or articles and may be ignored, these are included in our class for the sake of completeness w.r.t. the schema.

```python
# Attribute based on ContextObject
{
    info:doi : "Digital Object Identifier"
}

# Attributes in OpenURL requests object from Journal schema
{
    aulast : "First author's family name, may be more than one word",
    aufirst : "First author's given name or names or initials",
    auinit : "First author's first and middle initials",
    auinit1 : "First author's first initial",
    auinitm : "First author's middle initial",
    ausuffix : "First author's name suffix. e.g. 'Jr.', 'III'",
    au : "full name of a single author",
    aucorp : "Organisation or corporation that is the author or creator of the document",
    atitle : "Article title",
    jtitle : "Journal title", # 0.1 used 'title' so will be mapped to this in parse (see schema)
    stitle : "Abbreviated or short journal title",
    date : "Date of publication",
    chron : "Non-normalised enumeration / chronology, e.g. '1st quarter'",
    ssn : "Season (chronology). spring|summer|fall|autumn|winter",
    quarter : "Quarter (chronology). 1|2|3|4",
    volume : "Volume designation. e.g. '124', or 'VI'",
    part : "Subdivision of a volume or highest level division of the journal. e.g. 'B', 'Supplement'",
    issue : "Journal issue",
    spage : "Starting page",
    epage : "Ending page",
    pages : "Page range e.g. '53-58', 'C4-9'",
    artnum : "Article number",
    issn : "Journal ISSN",
    eissn : "ISSN for electronic version of the journal",
    isbn : "Journal ISBN",
    coden : "CODEN",
    sici : "Serial Item and Contribution Identifier (SICI)",
    genre : "journal|issue|article|proceeding|conference|preprint|unknown"
}

```
Each of these attributes in the model is read-only; only needing getters, since they are populated when the object is created from the parsed OpenURL. So to get the issn of the parsed incoming OpenURL request, one would use ```parsed_req.issn```.

To parse the query and build the object, the OpenURL is split into its keys (delimited by ```&```), with the values passed into the object attributes, with some minor validation if required.

### Mapping to ElasticSearch query

```python
# How attributes map to the ES models. Denoted (Journal, Article)
{
    info:doi : (, Article.bibjson.identifier) # type: doi
}

{
aulast : (, Article.author.name),
aufirst : (, Article.author.name),
auinit : (, Article.author.name),
auinit1 : (, Article.author.name),
auinitm : (, Article.author.name),
ausuffix : (, Article.author.name),
au : (, Article.author.name),
aucorp : (, Article.author.affiliation),
atitle : (, Article.bibjson.title),
jtitle : (Journal.bibjson.title, Article.bibjson.journal.title),
stitle : (Journal.bibjson.alternative_title),
date : (, Article.index.date),
chron : (), # No mapping for this
ssn : (), # No mapping for this
quarter : (), # No mapping for this
volume : (,Article.bibjson.journal.volume),
part : (), # No mapping for this
issue : (,Article.bibjson.journal.number),
spage : (,Article.bibjson.start_page),
epage : (,Article.bibjson.end_page),
pages : # use fields above,
artnum : () # No mapping for this,
issn : (Journal.bibjson.identifier, Article.bibjson.identifier) # type: pissn,
eissn : (Journal.bibjson.identifier, Article.bibjson.identifier) # type: eissn,
isbn : (Journal.bibjson.identifier, Article.bibjson.identifier),
coden : () # No mapping for this,
sici : () # No mapping for this,
genre : "journal|issue|article|proceeding|conference|preprint|unknown" # journal or article supported
}

```

## appendix
### useful resources
1. [OpenURL 1.0 Specification][niso_standard]
1. [OpenURL 0.1 Document][.1_proposal]
1. [OpenURL Repository][oclc_reg]
1. [Journal Schema][reg_journal]
1. The so-called [Idiot's guide to OpenURL][idiots]

### DOAJ Data Models
1. [DOAJ Article Data Model](../system/DATA_MODELS.md)
1. [DOAJ Journal Data Model](../system/Journal.md)
1. [DOAJ Application Data Model](../system/Suggestion.md)

[niso_standard]: http://www.niso.org/apps/group_public/download.php/6640/The%20OpenURL%20Framework%20for%20Context-Sensitive%20Services.pdf "ANSI/NISO Z39.88-2004"
[.1_proposal]: http://alcme.oclc.org/openurl/docs/pdf/openurl-01.pdf
[oclc_reg]: http://alcme.oclc.org/openurl/ "Registry for the OpenURL Framework"
[reg_journal]: http://alcme.oclc.org/openurl/servlet/OAIHandler/extension?verb=GetMetadata&metadataPrefix=mtx&identifier=info:ofi/fmt:kev:mtx:journal "Matrix defining the KEV Format to represent a journal publication"
[exlibris]: http://www.exlibrisgroup.com/category/sfxopenurl "ExLibris SFX Link Resolver"
[idiots]: http://nj.oclc.org/1cate/ig.html "OCLC Idiot's guide to Implementing OpenURL 1.0 for Journal Articles"


<!--
A superscript citation:
[<sup>\[1\]</sup>][exlibris]
-->
