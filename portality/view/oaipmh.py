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
    if verb.lower() == "identify":
        result = identify(dao, request.base_url)
    
    # serialise and return
    resp = make_response(result.serialise())
    resp.mimetype = "text/xml"
    return resp

#####################################################################
## Utility methods
#####################################################################

def get_response_date():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    

#####################################################################
## OAI-PMH protocol operations implemented
#####################################################################

def get_record(identifier, metadata_prefix):
    pass

def identify(dao, base_url):
    idobj = Identify(base_url=base_url)
    idobj.earliest_datestamp = dao.earliest_datestamp()
    return idobj
    
def list_identifiers(metadata_prefix, from_date=None, until_date=None, 
                    oai_set=None, resumption_token=None):
    pass

def list_metadata_formats(identifier):
    pass

def list_records(metadata_prefix, from_date=None, until_date=None,
                    oai_set=None, resumption_token=None):
    pass
    
def list_sets(resumption_token=None):
    pass

#####################################################################
## Error Handling
#####################################################################

# badArgument - request contains illegal arguments
# cannotDisseminateFormat - metadataPrefix is wrong
# idDoesNotExist - identifier doesn't go anywhere
# badResumptionToken - resumption token doesn't work
# noRecordsMatch  - empty resul tset
# noSetHierarchy - repository does not support sets
# noMetadataFormats - there are no metadata formats for the given identifier


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
        req.set("verb", self.verb)
        req.text = self.base_url
        
        element = self.get_element()
        oai.append(element)
        
        return oai
    
    def serialise(self):
        xml = self._to_xml()
        return etree.tostring(xml)
        
    def get_element(self):
        raise NotImplementedError()

class GetRecord(OAI_PMH):
    pass

class Identify(OAI_PMH):
    def __init__(self, base_url):
        super(Identify, self).__init__(base_url)
        self.verb = "Identify"
        self.earliest_datestamp = None
    
    def get_element(self):
        identify = etree.Element(self.PMH + "Identify", nsmap=self.NSMAP)
        
        repo_name = etree.SubElement(identify, self.PMH + "repositoryName")
        repo_name.text = app.config["SERVICE_NAME"]
        
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
        
        if app.config["ADMIN_EMAIL"] not in ["", None]:
            admin_email = etree.SubElement(identify, self.PMH + "adminEmail")
            admin_email.text = app.config["ADMIN_EMAIL"]
        
        return identify

class ListIdentifiers(OAI_PMH):
    pass

class ListMetadataFormats(OAI_PMH):
    pass

class ListRecords(OAI_PMH):
    pass

class ListSets(OAI_PMH):
    pass










