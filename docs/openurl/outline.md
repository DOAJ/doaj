![cl logo](http://cottagelabs.com/media/cropped-Cottage-on-hill-bubble-smoke.jpg)
<br><br>
# OpenURL for the DOAJ

This work will extend the DOAJ application to accept incoming OpenURL requests and provide their target, via an ElasticSearch query. This will require a new endpoint to accept the requests, a parser to construct the queries, plus a way to show the results.

### OpenURL 1.0 and OpenURL 0.1
OpenURL is a specification used to build links to resources. The OpenURL generalised Version 1.0 specification can be found [here][niso_standard] (pdf). It was based upon a previous version used specifically for scholarly articles, now named 0.1. This earlier version is still in use by some services and institutions, so this system will understand both, while recommending the newer syntax in documentation and by returning [HTTP code 301](http://en.wikipedia.org/wiki/HTTP_301) when the old syntax is used to indicate a permanent redirect.

OpenURL 1.0 requires the specification of a schema, specifies the format for keys used in the request. These can be found [here][oclc_reg].

*Unless otherwise specified, examples in this document are using the 1.0 standard.*

#### OpenURL use



## appendix

### useful resources
1. [OpenURL 1.0 Specification][niso_standard]
2. [OpenURL Repository][oclc_reg]

[niso_standard]: http://www.niso.org/apps/group_public/download.php/6640/The%20OpenURL%20Framework%20for%20Context-Sensitive%20Services.pdf "ANSI/NISO Z39.88-2004"
[oclc_reg]: http://alcme.oclc.org/openurl/ "Registry for the OpenURL Framework"
[exlibris]: http://www.exlibrisgroup.com/category/sfxopenurl "ExLibris SFX Link Resolver"


<!--
A superscript citation:
[<sup>\[1\]</sup>][exlibris]
-->
