![cl logo](http://cottagelabs.com/media/cropped-Cottage-on-hill-bubble-smoke.jpg)
<br><br>
# OpenURL for the DOAJ

This work will extend the DOAJ application to accept incoming OpenURL requests and provide their target, via an ElasticSearch query. This will require a new endpoint to accept the requests, a parser to construct the queries, plus a way to show the results.

### OpenURL 1.0 and OpenURL 0.1
OpenURL is a specification used to build links to resources. The OpenURL generalised Version 1.0 specification can be found [here][niso_standard] (pdf). It was based upon a previous version used specifically for scholarly articles, now referred to as 0.1. This earlier version is still in use by some services and institutions, so this system will understand both, while recommending the newer syntax in documentation and by returning [HTTP code 301](http://en.wikipedia.org/wiki/HTTP_301) when the old syntax is used to indicate a permanent redirect.

OpenURL 1.0 requires the specification of a schema, specifies the format for keys used in the request. These can be found [here][oclc_reg].

*Unless otherwise specified, examples in this document are using the 1.0 standard.*

#### Prior use in DOAJ
Some examples of incoming requests were captured by the DOAJ, demonstrating the 0.1 syntax:

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


### Mapping to ElasticSearch query

## appendix
### useful resources
1. [OpenURL 1.0 Specification][niso_standard]
2. [OpenURL Repository][oclc_reg]
3. [Journal Schema][reg_journal]

[niso_standard]: http://www.niso.org/apps/group_public/download.php/6640/The%20OpenURL%20Framework%20for%20Context-Sensitive%20Services.pdf "ANSI/NISO Z39.88-2004"
[oclc_reg]: http://alcme.oclc.org/openurl/ "Registry for the OpenURL Framework"
[reg_journal]: http://alcme.oclc.org/openurl/servlet/OAIHandler/extension?verb=GetMetadata&metadataPrefix=mtx&identifier=info:ofi/fmt:kev:mtx:journal "Matrix defining the KEV Format to represent a journal publication"
[exlibris]: http://www.exlibrisgroup.com/category/sfxopenurl "ExLibris SFX Link Resolver"


<!--
A superscript citation:
[<sup>\[1\]</sup>][exlibris]
-->
