from lxml import etree
from datetime import datetime
from flask import Blueprint, request, abort, make_response
from portality.core import app
from portality.dao import DomainObject
from portality.models import OAIPMHJournal, OAIPMHArticle

blueprint = Blueprint('oaipmh', __name__)

#####################################################################
## Web API endpoints
#####################################################################

@blueprint.route("/oai")
@blueprint.route("/oai.<specified>")
def oaipmh(specified=None):
    # work out which endpoint we're going to
    dao = None
    if specified is None:
        dao = OAIPMHJournal()
    else:
        dao = OAIPMHArticle()
    
    # work out the verb and associated parameters
    verb = request.values.get("verb")
    
    # call the appropriate protocol operation
    result = None
    
    # Identify
    if verb.lower() == "identify":
        result = identify(dao, request.base_url)
    
    # ListMetadataFormats
    elif verb.lower() == "listmetadataformats":
        params = list_metadata_formats_params(request)
        result = list_metadata_formats(dao, request.base_url, **params)
    
    # GetRecord
    elif verb.lower() == "getrecord":
        params = get_record_params(request)
        if params.get("identifier") is None or params.get("metadata_prefix") is None:
            result = BadArgument(request.base_url)
        else:
            result = get_record(dao, request.base_url, **params)
    
    # ListSets
    elif verb.lower() == "listsets":
        params = list_sets_params(request)
        result = list_sets(dao, request.base_url, **params)
    
    # A verb we didn't understand
    else:
        result = BadVerb(request.base_url)
    
    # serialise and return
    resp = make_response(result.serialise())
    resp.mimetype = "text/xml"
    return resp

#####################################################################
## Utility methods
#####################################################################

def make_oai_identifier(identifier, qualifier):
    return "oai:" + app.config.get("OAIPMH_IDENTIFIER_NAMESPACE") + "/" + qualifier + ":" + identifier
    
def extract_internal_id(oai_identifier):
    return oai_identifier.split(":")[-1]

def get_response_date():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

def normalise_date(date):
    return "T".join(date.split(" ")) + "Z" # fudge the format for the time being

def get_crosswalk(prefix, datatype):
    return CROSSWALKS.get(prefix, {}).get(datatype)()

def list_metadata_formats_params(req):
    identifier = req.values.get("identifier")
    if identifier is not None:
        identifier = extract_internal_id(identifier)
    return {"identifier" : identifier}

def get_record_params(req):
    identifier = req.values.get("identifier")
    metadata_prefix = req.values.get("metadataPrefix")
    if identifier is not None:
        identifier = extract_internal_id(identifier)
    return {"identifier" : identifier, "metadata_prefix" : metadata_prefix}

def list_sets_params(req):
    resumption = req.values.get("resumptionToken")
    return {"resumption_token" : resumption}

#####################################################################
## OAI-PMH protocol operations implemented
#####################################################################

def get_record(dao, base_url, identifier=None, metadata_prefix=None):
    # check that we have both identifier and prefix - they are both required
    if identifier is None or metadata_prefix is None:
        return BadArgument(base_url)
    
    # get the formats and check that we have formats that we can disseminate
    formats = app.config.get("OAIPMH_METADATA_FORMATS")
    if formats is None or len(formats) == 0:
        return CannotDisseminateFormat(base_url)
    
    # look for our record of the format we've been asked for
    for f in formats:
        if f.get("metadataPrefix") == metadata_prefix:
            # obtain the record from the dao
            record = dao.pull(identifier)
            if record is None:
                return IdDoesNotExist(base_url)
            # do the crosswalk
            xwalk = get_crosswalk(f.get("metadataPrefix"), dao.__type__)
            metadata = xwalk.crosswalk(record)
            header = xwalk.header(record)
            # make the response
            oai_id = make_oai_identifier(identifier, dao.__type__)
            gr = GetRecord(base_url, oai_id, metadata_prefix)
            gr.metadata = metadata
            gr.header = header
            return gr
    
    # if we have not returned already, this means we can't disseminate this format
    return CannotDisseminateFormat(base_url)

def identify(dao, base_url):
    idobj = Identify(base_url=base_url)
    idobj.earliest_datestamp = dao.earliest_datestamp()
    return idobj
    
def list_identifiers(metadata_prefix, from_date=None, until_date=None, 
                    oai_set=None, resumption_token=None):
    pass

def list_metadata_formats(dao, base_url, identifier=None):
    # if we are given an identifier, it has to be valid
    if identifier is not None:
        if not dao.identifier_exists(identifier):
            return IdDoesNotExist(base_url)
    
    # get the configured formats - there should always be some, but just in case
    # the service is mis-configured, this will throw the correct error
    formats = app.config.get("OAIPMH_METADATA_FORMATS")
    if formats is None or len(formats) == 0:
        return NoMetadataFormats(base_url)
    
    # create and return the list metadata formats response
    oai_id = make_oai_identifier(identifier, dao.__type__)
    lmf = ListMetadataFormats(base_url=base_url, identifier=oai_id)
    for f in formats:
        lmf.add_format(f.get("metadataPrefix"), f.get("schema"), f.get("metadataNamespace"))
    return lmf

def list_records(metadata_prefix, from_date=None, until_date=None,
                    oai_set=None, resumption_token=None):
    pass
    
def list_sets(dao, base_url, resumption_token=None):
    # This implementation does not support resumption tokens for this operation
    if resumption_token is not None:
        return BadResumptionToken(base_url)
    
    # just ask the DAO to get a list of all the sets for us, then we
    # give the set spec and set name as the same string
    ls = ListSets(base_url)
    sets = dao.list_sets()
    for s in sets:
        ls.add_set(s, s)
    return ls

#####################################################################
## Objects
#####################################################################

class OAI_PMH(object):
    VERSION = "2.0"
    
    PMH_NAMESPACE = "http://www.openarchives.org/OAI/2.0/"
    PMH = "{%s}" % PMH_NAMESPACE
    
    XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    XSI = "{%s}" % XSI_NAMESPACE
    
    NSMAP = {None : PMH_NAMESPACE, "xsi" : XSI_NAMESPACE}
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.verb = None
    
    def _to_xml(self):
        oai = etree.Element(self.PMH + "OAI-PMH", nsmap=self.NSMAP)
        oai.set(self.XSI + "schemaLocation", 
            "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd")
        
        respdate = etree.SubElement(oai, self.PMH + "responseDate")
        respdate.text = get_response_date()
        
        req = etree.SubElement(oai, self.PMH + "request")
        if self.verb is not None:
            req.set("verb", self.verb)
        req.text = self.base_url
        self.add_request_attributes(req)
        
        element = self.get_element()
        oai.append(element)
        
        return oai
    
    def serialise(self):
        xml = self._to_xml()
        return etree.tostring(xml)
        
    def get_element(self):
        raise NotImplementedError()
        
    def add_request_attributes(self, element):
        return

class GetRecord(OAI_PMH):
    def __init__(self, base_url, identifier, metadata_prefix):
        super(GetRecord, self).__init__(base_url)
        self.verb = "GetRecord"
        self.identifier = identifier
        self.metadata_prefix = metadata_prefix
        self.metadata = None
        self.header = None
    
    def get_element(self):
        gr = etree.Element(self.PMH + "GetRecord", nsmap=self.NSMAP)
        record = etree.SubElement(gr, self.PMH + "record")
        
        record.append(self.header)
        record.append(self.metadata)
        
        return gr
        
    def add_request_attributes(self, element):
        if self.identifier is not None:
            element.set("identifier", self.identifier)
        if self.metadata_prefix is not None:
            element.set("metadataPrefix", self.metadata_prefix)

class Identify(OAI_PMH):
    def __init__(self, base_url):
        super(Identify, self).__init__(base_url)
        self.verb = "Identify"
        self.earliest_datestamp = None
    
    def get_element(self):
        identify = etree.Element(self.PMH + "Identify", nsmap=self.NSMAP)
        
        repo_name = etree.SubElement(identify, self.PMH + "repositoryName")
        repo_name.text = app.config.get("SERVICE_NAME")
        
        base = etree.SubElement(identify, self.PMH + "baseURL")
        base.text = self.base_url
        
        protocol = etree.SubElement(identify, self.PMH + "protocolVersion")
        protocol.text = self.VERSION
        
        if self.earliest_datestamp is not None:
            earliest = etree.SubElement(identify, self.PMH + "earliestDatestamp")
            earliest.text = self.earliest_datestamp
        
        deletes = etree.SubElement(identify, self.PMH + "deletedRecord")
        deletes.text = "transient" # keep the door open
        
        granularity = etree.SubElement(identify, self.PMH + "granularity")
        granularity.text = "YYYY-MM-DDThh:mm:ssZ"
        
        if app.config.get("ADMIN_EMAIL") not in ["", None]:
            admin_email = etree.SubElement(identify, self.PMH + "adminEmail")
            admin_email.text = app.config.get("ADMIN_EMAIL")
        
        return identify

class ListIdentifiers(OAI_PMH):
    pass

class ListMetadataFormats(OAI_PMH):
    def __init__(self, base_url, identifier=None):
        super(ListMetadataFormats, self).__init__(base_url)
        self.verb = "ListMetadataFormats"
        self.identifier = identifier
        self.formats = []
    
    def add_format(self, metadata_prefix, schema, metadata_namespace):
        self.formats.append(
            {
                "metadataPrefix" : metadata_prefix,
                "schema" : schema,
                "metadataNamespace" : metadata_namespace
            }
        )
    
    def add_request_attributes(self, element):
        if self.identifier is not None:
            element.set("identifier", self.identifier)
        
    def get_element(self):
        lmf = etree.Element(self.PMH + "ListMetadataFormats", nsmap=self.NSMAP)
        
        for f in self.formats:
            mdf = etree.SubElement(lmf, self.PMH + "metadataFormat")
            
            mdp = etree.SubElement(mdf, self.PMH + "metadataPrefix")
            mdp.text = f.get("metadataPrefix")
            
            sch = etree.SubElement(mdf, self.PMH + "schema")
            sch.text = f.get("schema")
            
            mdn = etree.SubElement(mdf, self.PMH + "metadataNamespace")
            mdn.text = f.get("metadataNamespace")
        
        return lmf

class ListRecords(OAI_PMH):
    pass

class ListSets(OAI_PMH):
    def __init__(self, base_url):
        super(ListSets, self).__init__(base_url)
        self.verb = "ListSets"
        self.sets = []
    
    def add_set(self, spec, name):
        self.sets.append((spec, name))
    
    def get_element(self):
        ls = etree.Element(self.PMH + "ListSets", nsmap=self.NSMAP)
        
        for spec, name in self.sets:
            s = etree.SubElement(ls, self.PMH + "set")
            specel = etree.SubElement(s, self.PMH + "setSpec")
            specel.text = spec
            nameel = etree.SubElement(s, self.PMH + "setName")
            nameel.text = name
        
        return ls
        

#####################################################################
## Error Handling
#####################################################################

class OAIPMHError(OAI_PMH):
    def __init__(self, base_url):
        super(OAIPMHError, self).__init__(base_url)
        self.code = None
        self.description = None
    
    def get_element(self):
        error = etree.Element(self.PMH + "error", nsmap=self.NSMAP)
        
        if self.code is not None:
            error.set("code", self.code)
        
        if self.description is not None:
            error.text = self.description
        
        return error

class BadArgument(OAIPMHError):
    def __init__(self, base_url):
        super(BadArgument, self).__init__(base_url)
        self.code = "badArgument"
        self.description = "The request includes illegal arguments, is missing required arguments, includes a repeated argument, or values for arguments have an illegal syntax."

class BadResumptionToken(OAIPMHError):
    def __init__(self, base_url):
        super(BadResumptionToken, self).__init__(base_url)
        self.code = "badResumptionToken"
        self.description = "The value of the resumptionToken argument is invalid or expired."

class BadVerb(OAIPMHError):
    def __init__(self, base_url):
        super(BadVerb, self).__init__(base_url)
        self.code = "badVerb"
        self.description = "Value of the verb argument is not a legal OAI-PMH verb, the verb argument is missing, or the verb argument is repeated."

class CannotDisseminateFormat(OAIPMHError):
    def __init__(self, base_url):
        super(CannotDisseminateFormat, self).__init__(base_url)
        self.code = "cannotDisseminateFormat"
        self.description = "The metadata format identified by the value given for the metadataPrefix argument is not supported by the item or by the repository."

class IdDoesNotExist(OAIPMHError):
    def __init__(self, base_url):
        super(IdDoesNotExist, self).__init__(base_url)
        self.code = "idDoesNotExist"
        self.description = "The value of the identifier argument is unknown or illegal in this repository."

class NoRecordsMatch(OAIPMHError):
    def __init__(self, base_url):
        super(NoRecordsMatch, self).__init__(base_url)
        self.code = "noRecordsMatch"
        self.description = "The combination of the values of the from, until, set and metadataPrefix arguments results in an empty list."

class NoMetadataFormats(OAIPMHError):
    def __init__(self, base_url):
        super(NoMetadataFormats, self).__init__(base_url)
        self.code = "noMetadataFormats"
        self.description = "There are no metadata formats available for the specified item."

class NoSetHierarchy(OAIPMHError):
    def __init__(self, base_url):
        super(NoSetHierarchy, self).__init__(base_url)
        self.code = "noSetHierarchy"
        self.description = "The repository does not support sets."

#####################################################################
## Crosswalks
#####################################################################

class OAI_DC_Crosswalk(object):
    PMH_NAMESPACE = "http://www.openarchives.org/OAI/2.0/"
    PMH = "{%s}" % PMH_NAMESPACE
    
    XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    XSI = "{%s}" % XSI_NAMESPACE
    
    OAIDC_NAMESPACE = "http://www.openarchives.org/OAI/2.0/oai_dc/"
    OAIDC = "{%s}" % OAIDC_NAMESPACE
    
    DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
    DC = "{%s}" % DC_NAMESPACE
    
    NSMAP = {None : PMH_NAMESPACE, "xsi" : XSI_NAMESPACE, "oai_dc" : OAIDC_NAMESPACE, "dc" : DC_NAMESPACE}
    
    def crosswalk(self, record):
        raise NotImplementedError()
    
    def header(self, record):
        raise NotImplementedError()

class OAI_DC_Article(OAI_DC_Crosswalk):
    def crosswalk(self, record):
        bibjson = record.bibjson()
        
        metadata = etree.Element(self.PMH + "metadata", nsmap=self.NSMAP)
        oai_dc = etree.SubElement(metadata, self.OAIDC + "dc")
        oai_dc.set(self.XSI + "schemaLocation", 
            "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd")
        
        if bibjson.title is not None:
            title = etree.SubElement(oai_dc, self.DC + "title")
            title.text = bibjson.title
        
        for identifier in bibjson.get_identifiers():
            idel = etree.SubElement(oai_dc, self.DC + "identifier")
            idel.text = identifier.get("id")
        
        # FIXME: not sure if we want this here?
        #created = etree.SubElement(oai_dc, self.DC + "date")
        #created.text = normalise_date(record.created_date)
        
        # work out the date of publication
        date = bibjson.get_publication_date()
        if date != "":
            monthyear = etree.SubElement(oai_dc, self.DC + "date")
            monthyear.text = date
        
        if len(bibjson.get_urls()) > 0:
            for url in bibjson.get_urls():
                urlel = etree.SubElement(oai_dc, self.DC + "relation")
                urlel.text = url.get("url")
        
        if bibjson.abstract is not None:
            abstract = etree.SubElement(oai_dc, self.DC + "description")
            abstract.text = bibjson.abstract
        
        if len(bibjson.author) > 0:
            for author in bibjson.author:
                ael = etree.SubElement(oai_dc, self.DC + "creator")
                ael.text = author.get("name")
        
        if bibjson.publisher is not None:
            pubel = etree.SubElement(oai_dc, self.DC + "publisher")
            pubel.text = bibjson.publisher
        
        for keyword in bibjson.keywords:
            subj = etree.SubElement(oai_dc, self.DC + "subject")
            subj.text = keyword
        
        return metadata
        
    def header(self, record):
        bibjson = record.bibjson()
        head = etree.Element(self.PMH + "header", nsmap=self.NSMAP)
        
        identifier = etree.SubElement(head, self.PMH + "identifier")
        identifier.text = make_oai_identifier(record.id, "article")
        
        datestamp = etree.SubElement(head, self.PMH + "datestamp")
        datestamp.text = normalise_date(record.created_date)
        
        """
        FIXME: we need to sort out the subject classifications for articles
        for subs in bibjson.subjects():
            scheme = subs.get("scheme")
            term = subs.get("term")
            
            subel = etree.SubElement(head, self.PMH + "setSpec")
            subel.text = scheme + ":" + term
        """
        
        return head

class OAI_DC_Journal(OAI_DC_Crosswalk):
    def crosswalk(self, record):
        bibjson = record.bibjson()
        
        metadata = etree.Element(self.PMH + "metadata", nsmap=self.NSMAP)
        oai_dc = etree.SubElement(metadata, self.OAIDC + "dc")
        oai_dc.set(self.XSI + "schemaLocation", 
            "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd")
        
        if bibjson.title is not None:
            title = etree.SubElement(oai_dc, self.DC + "title")
            title.text = bibjson.title
        
        for identifier in bibjson.get_identifiers():
            idel = etree.SubElement(oai_dc, self.DC + "identifier")
            idel.text = identifier.get("id")
        
        for keyword in bibjson.keywords:
            subj = etree.SubElement(oai_dc, self.DC + "subject")
            subj.text = keyword
        
        if bibjson.language is not None and len(bibjson.language) > 0:
            for language in bibjson.language:
                lang = etree.SubElement(oai_dc, self.DC + "language")
                lang.text = language
        
        if bibjson.author_pays_url is not None:
            relation = etree.SubElement(oai_dc, self.DC + "relation")
            relation.text = bibjson.author_pays_url
        
        if bibjson.get_license() is not None:
            rights = etree.SubElement(oai_dc, self.DC + "rights")
            rights.text = bibjson.license.get("title")
        
        if bibjson.publisher is not None:
            pub = etree.SubElement(oai_dc, self.DC + "publisher")
            pub.text = bibjson.publisher
        
        if len(bibjson.get_urls()) > 0:
            for url in bibjson.get_urls():
                urlel = etree.SubElement(oai_dc, self.DC + "relation")
                urlel.text = url.get("url")
        
        if bibjson.provider is not None:
            prov = etree.SubElement(oai_dc, self.DC + "publisher")
            prov.text = bibjson.provider
        
        created = etree.SubElement(oai_dc, self.DC + "date")
        created.text = normalise_date(record.created_date)
        
        for subs in bibjson.subjects():
            scheme = subs.get("scheme")
            term = subs.get("term")
            
            subel = etree.SubElement(oai_dc, self.DC + "subject")
            subel.text = scheme + ":" + term
            
        return metadata
    
    def header(self, record):
        bibjson = record.bibjson()
        head = etree.Element(self.PMH + "header", nsmap=self.NSMAP)
        
        identifier = etree.SubElement(head, self.PMH + "identifier")
        identifier.text = make_oai_identifier(record.id, "journal")
        
        datestamp = etree.SubElement(head, self.PMH + "datestamp")
        datestamp.text = normalise_date(record.created_date)
        
        for subs in bibjson.subjects():
            scheme = subs.get("scheme")
            term = subs.get("term")
            
            subel = etree.SubElement(head, self.PMH + "setSpec")
            subel.text = scheme + ":" + term
        
        return head

CROSSWALKS = {
    "oai_dc" : {
        "article" : OAI_DC_Article,
        "journal" : OAI_DC_Journal
    }
}










