import json, base64, sys, re
from lxml import etree
from datetime import datetime, timedelta
from flask import Blueprint, request, make_response
from portality.core import app
from portality.models import OAIPMHJournal, OAIPMHArticle
from portality.lib import analytics
from portality import datasets
from copy import deepcopy

blueprint = Blueprint('oaipmh', __name__)

#####################################################################
# Web API endpoints
#####################################################################


@blueprint.route("/oai", methods=["GET", "POST"])
@blueprint.route("/oai.<specified>", methods=["GET", "POST"])
def oaipmh(specified=None):
    # Google Analytics event, we don't know the action yet but it will be required.
    event = analytics.GAEvent(category=app.config.get('GA_CATEGORY_OAI', 'OAI-PMH'), action=None)
    # work out which endpoint we're going to
    if specified is None:
        dao = OAIPMHJournal()
        event.label = 'Journal'
    else:
        specified = specified.lower()
        dao = OAIPMHArticle()
        event.label = 'Article'

    # Add the identifier to the event if there is one
    ident = request.values.get('identifier', None)
    if ident is not None:
        event.fieldsobject = {app.config.get('GA_DIMENSIONS')['oai_res_id']: ident}

    # work out the verb and associated parameters
    verb = request.values.get("verb")
    event.action = verb

    # Now we have enough information about the request to send to analytics.
    event.submit()

    # call the appropriate protocol operation:
    # if no verb supplied
    if verb is None:
        result = BadVerb(request.base_url)

    # Identify
    elif verb.lower() == "identify":
        result = identify(dao, request.base_url)

    # ListMetadataFormats
    elif verb.lower() == "listmetadataformats":
        params = list_metadata_formats_params(request)
        result = list_metadata_formats(dao, request.base_url, specified, **params)

    # GetRecord
    elif verb.lower() == "getrecord":
        params = get_record_params(request)
        result = get_record(dao, request.base_url, specified, **params)

    # ListSets
    elif verb.lower() == "listsets":
        params = list_sets_params(request)
        result = list_sets(dao, request.base_url, **params)

    # ListRecords
    elif verb.lower() == "listrecords":
        params = list_records_params(request)
        result = list_records(dao, request.base_url, specified, **params)

    # ListIdentifiers
    elif verb.lower() == "listidentifiers":
        params = list_identifiers_params(request)
        result = list_identifiers(dao, request.base_url, specified, **params)

    # A verb we didn't understand
    else:
        result = BadVerb(request.base_url)

    # serialise and return
    resp = make_response(result.serialise())
    resp.mimetype = "text/xml"
    return resp

#####################################################################
# Utility methods/objects
#####################################################################


class DateFormat(object):
    @classmethod
    def granularity(self):
        return "YYYY-MM-DDThh:mm:ssZ"

    @classmethod
    def default_earliest(cls):
        return "1970-01-01T00:00:00Z"

    @classmethod
    def now(cls):
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def format(cls, date):
        return date.strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def legitimate_granularity(cls, datestr):
        formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"]
        success = False
        for f in formats:
            try:
                datetime.strptime(datestr, f)
                success = True
                break
            except Exception:
                pass
        return success


def make_set_spec(setspec):
    return base64.urlsafe_b64encode(setspec).replace("=", "~")


def decode_set_spec(setspec):
    # first, make sure the setspec is a string
    try:
        setspec = setspec.encode("utf-8")
    except:
        raise SetSpecException()

    # switch the ~ for =
    setspec = setspec.replace("~", "=")

    # base64 decode
    decoded = base64.urlsafe_b64decode(setspec)

    try:
        decoded = decoded.decode("utf-8")
    except:
        raise SetSpecException()

    return decoded


def get_start_after(docs):
    last_date = docs[-1].get("last_updated")
    count = 0
    for doc in docs:
        if doc.get("last_updated") == last_date:
            count += 1
    return (last_date, count)

def make_resumption_token(metadata_prefix=None, from_date=None, until_date=None, oai_set=None, start_number=None, start_after=None):
    d = {}
    if metadata_prefix is not None:
        d["m"] = metadata_prefix
    if from_date is not None:
        d["f"] = from_date
    if until_date is not None:
        d["u"] = until_date
    if oai_set is not None:
        d["s"] = oai_set
    if start_number is not None:
        d["n"] = start_number
    if start_after is not None:
        d["a"] = start_after
    j = json.dumps(d)
    b = base64.urlsafe_b64encode(j)
    return b


class ResumptionTokenException(Exception):
    pass


class SetSpecException(Exception):
    pass


def decode_resumption_token(resumption_token):
    # attempt to parse the resumption token out of base64 encoding and as a json object
    try:
        j = base64.urlsafe_b64decode(str(resumption_token))
    except TypeError:
        raise ResumptionTokenException()
    try:
        d = json.loads(j)
    except ValueError:
        raise ResumptionTokenException()

    # if we succeed read out the parameters
    params = {}
    if "m" in d: params["metadata_prefix"] = d.get("m")
    if "f" in d: params["from_date"] = d.get("f")
    if "u" in d: params["until_date"] = d.get("u")
    if "s" in d: params["oai_set"] = d.get("s")
    if "n" in d: params["start_number"] = d.get("n")
    if "a" in d: params["start_after"] = tuple(d.get("a"))
    return params


def make_oai_identifier(identifier, qualifier):
    return "oai:" + app.config.get("OAIPMH_IDENTIFIER_NAMESPACE") + "/" + qualifier + ":" + identifier


def extract_internal_id(oai_identifier):
    # most of the identifier is for show - we only care about the hex string at the end
    return oai_identifier.split(":")[-1]


def get_response_date():
    # return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    return DateFormat.now()


def normalise_date(date):
    # FIXME: do we need a more powerful date normalisation routine?
    try:
        datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        return date
    except:
        return "T".join(date.split(" ")) + "Z"


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
    return {"identifier": identifier, "metadata_prefix": metadata_prefix}


def list_sets_params(req):
    resumption = req.values.get("resumptionToken")
    return {"resumption_token" : resumption}


def list_records_params(req):
    from_date = req.values.get("from")
    until_date = req.values.get("until")
    oai_set = req.values.get("set")
    resumption_token = req.values.get("resumptionToken")
    metadata_prefix = req.values.get("metadataPrefix")
    return {
        "from_date": from_date,
        "until_date": until_date,
        "oai_set": oai_set,
        "resumption_token": resumption_token,
        "metadata_prefix": metadata_prefix
    }


def list_identifiers_params(req):
    from_date = req.values.get("from")
    until_date = req.values.get("until")
    oai_set = req.values.get("set")
    resumption_token = req.values.get("resumptionToken")
    metadata_prefix = req.values.get("metadataPrefix")
    return {
        "from_date": from_date,
        "until_date": until_date,
        "oai_set": oai_set,
        "resumption_token": resumption_token,
        "metadata_prefix": metadata_prefix
    }

###########################################################
# XML Character encoding hacks
###########################################################


_illegal_unichrs = [(0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F),
                    (0x7F, 0x84), (0x86, 0x9F),
                    (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF)]
if sys.maxunicode >= 0x10000:  # not narrow build
    _illegal_unichrs.extend([(0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
                             (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
                             (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                             (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
                             (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
                             (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                             (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
                             (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)])
_illegal_ranges = ["%s-%s" % (unichr(low), unichr(high))
                   for (low, high) in _illegal_unichrs]
_illegal_xml_chars_RE = re.compile(u'[%s]' % u''.join(_illegal_ranges))


def valid_XML_char_ordinal(i):
    return ( # conditions ordered by presumed frequency
        0x20 <= i <= 0xD7FF
        or i in (0x9, 0xA, 0xD)
        or 0xE000 <= i <= 0xFFFD
        or 0x10000 <= i <= 0x10FFFF
        )


def clean_unreadable(input_string):
    try:
        return _illegal_xml_chars_RE.sub("", input_string)
    except TypeError as e:
        app.logger.error("Unable to strip illegal XML chars from: {x}, {y}".format(x=input_string, y=type(input_string)))
        return None


def xml_clean(input_string):
    cleaned_string = ''.join(c for c in input_string if valid_XML_char_ordinal(ord(c)))
    return cleaned_string


def set_text(element, input_string):
    if input_string is None:
        return
    input_string = clean_unreadable(input_string)
    try:
        element.text = input_string
    except ValueError:
        element.text = xml_clean(input_string)


#####################################################################
# OAI-PMH protocol operations implemented
#####################################################################

def get_record(dao, base_url, specified_oai_endpoint, identifier=None, metadata_prefix=None):
    # check that we have both identifier and prefix - they are both required
    if identifier is None or metadata_prefix is None:
        return BadArgument(base_url)

    # get the formats and check that we have formats that we can disseminate
    formats = app.config.get("OAIPMH_METADATA_FORMATS", {}).get(specified_oai_endpoint)
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
    repo_name = app.config.get("SERVICE_NAME")
    admin_email = app.config.get("ADMIN_EMAIL")
    idobj = Identify(base_url, repo_name, admin_email)
    idobj.earliest_datestamp = dao.earliest_datestamp()
    return idobj


def list_identifiers(dao, base_url, specified_oai_endpoint, metadata_prefix=None, from_date=None, until_date=None, oai_set=None, resumption_token=None):
    if resumption_token is None:
        # do an initial list records
        return _parameterised_list_identifiers(
            dao, base_url,
            specified_oai_endpoint, metadata_prefix=metadata_prefix, from_date=from_date,
            until_date=until_date, oai_set=oai_set
        )
    else:
        # resumption of previous request
        if (metadata_prefix is not None or from_date is not None or until_date is not None
                or oai_set is not None):
            return BadArgument(base_url)
        return _resume_list_identifiers(dao, base_url, specified_oai_endpoint, resumption_token=resumption_token)


def _parameterised_list_identifiers(dao, base_url, specified_oai_endpoint, metadata_prefix=None, from_date=None, until_date=None, oai_set=None, start_number=0, start_after=None):
    # metadata prefix is required
    if metadata_prefix is None:
        return BadArgument(base_url)

    # get the formats and check that we have formats that we can disseminate
    formats = app.config.get("OAIPMH_METADATA_FORMATS", {}).get(specified_oai_endpoint)
    if formats is None or len(formats) == 0:
        return CannotDisseminateFormat(base_url)

    # check that the dates are formatted correctly
    fl = True
    ul = True
    if from_date is not None:
        fl = DateFormat.legitimate_granularity(from_date)
    if until_date is not None:
        ul = DateFormat.legitimate_granularity(until_date)

    if not fl or not ul:
        return BadArgument(base_url)

    #try:
        #if from_date is not None:
        #    datetime.strptime(from_date, "%Y-%m-%d")
        #if until_date is not None:
        #    datetime.strptime(until_date, "%Y-%m-%d")
    #except:
    #    return BadArgument(base_url)

    # get the result set size
    list_size = app.config.get("OAIPMH_LIST_IDENTIFIERS_PAGE_SIZE", 25)

    # decode the oai_set to something we can query with
    try:
        decoded_set = decode_set_spec(oai_set) if oai_set is not None else None
    except SetSpecException:
        return BadArgument(base_url)

    for f in formats:
        if f.get("metadataPrefix") == metadata_prefix:
            # do the query and set up the response object
            total, results = dao.list_records(from_date, until_date, decoded_set, list_size, start_number, start_after)

            # if there are no results, PMH requires us to throw an error
            if len(results) == 0:
                return NoRecordsMatch(base_url)

            # get the full total
            full_total = total
            if start_after is not None:
                full_total = total + start_number - start_after[1]

            # work out if we need a resumption token.  It can have one of 3 values:
            # - None = do not include the rt in the response
            # - some value = include in the response
            # - the empty string = include in the response
            resumption_token = None
            if total > len(results):
                start_after = get_start_after(results)
                new_start = start_number + len(results)
                resumption_token = make_resumption_token(metadata_prefix=metadata_prefix, from_date=from_date,
                      until_date=until_date, oai_set=oai_set, start_number=new_start, start_after=start_after)
            else:
                resumption_token = ""

            li = ListIdentifiers(base_url, from_date=from_date, until_date=until_date, oai_set=oai_set, metadata_prefix=metadata_prefix)
            if resumption_token is not None:
                expiry = app.config.get("OAIPMH_RESUMPTION_TOKEN_EXPIRY", -1)
                li.set_resumption(resumption_token, complete_list_size=full_total, cursor=start_number, expiry=expiry)

            for r in results:
                # do the crosswalk (header only in this operation)
                xwalk = get_crosswalk(f.get("metadataPrefix"), dao.__type__)
                header = xwalk.header(r)

                # add to the response
                li.add_record(header)
            return li

    # if we have not returned already, this means we can't disseminate this format
    return CannotDisseminateFormat(base_url)


def _resume_list_identifiers(dao, base_url, specified_oai_endpoint, resumption_token=None):
    try:
        params = decode_resumption_token(resumption_token)
    except ResumptionTokenException:
        return BadResumptionToken(base_url)
    return _parameterised_list_identifiers(dao, base_url, specified_oai_endpoint, **params)


def list_metadata_formats(dao, base_url, specified_oai_endpoint, identifier=None):
    # if we are given an identifier, it has to be valid
    if identifier is not None:
        if not dao.identifier_exists(identifier):
            return IdDoesNotExist(base_url)

    # get the configured formats - there should always be some, but just in case
    # the service is mis-configured, this will throw the correct error
    formats = app.config.get("OAIPMH_METADATA_FORMATS", {}).get(specified_oai_endpoint)
    if formats is None or len(formats) == 0:
        return NoMetadataFormats(base_url)

    # create and return the list metadata formats response
    oai_id = None
    if identifier is not None:
        oai_id = make_oai_identifier(identifier, dao.__type__)
    lmf = ListMetadataFormats(base_url=base_url, identifier=oai_id)
    for f in formats:
        lmf.add_format(f.get("metadataPrefix"), f.get("schema"), f.get("metadataNamespace"))
    return lmf


def list_records(dao, base_url, specified_oai_endpoint, metadata_prefix=None, from_date=None, until_date=None, oai_set=None, resumption_token=None):

    if resumption_token is None:
        # do an initial list records
        return _parameterised_list_records(dao, base_url, specified_oai_endpoint, metadata_prefix=metadata_prefix, from_date=from_date, until_date=until_date, oai_set=oai_set)
    else:
        # resumption of previous request
        if (metadata_prefix is not None or from_date is not None or until_date is not None
                or oai_set is not None):
            return BadArgument(base_url)
        return _resume_list_records(dao, base_url, specified_oai_endpoint, resumption_token=resumption_token)


def _parameterised_list_records(dao, base_url, specified_oai_endpoint, metadata_prefix=None, from_date=None, until_date=None, oai_set=None, start_number=0, start_after=None):
    # metadata prefix is required
    if metadata_prefix is None:
        return BadArgument(base_url)

    # get the formats and check that we have formats that we can disseminate
    formats = app.config.get("OAIPMH_METADATA_FORMATS", {}).get(specified_oai_endpoint)
    if formats is None or len(formats) == 0:
        return CannotDisseminateFormat(base_url)

    # check that the dates are formatted correctly
    fl = True
    ul = True
    if from_date is not None:
        fl = DateFormat.legitimate_granularity(from_date)
    if until_date is not None:
        ul = DateFormat.legitimate_granularity(until_date)

    if not fl or not ul:
        return BadArgument(base_url)

    # check that the dates are formatted correctly
    #try:
    #    if from_date is not None:
    #        datetime.strptime(from_date, "%Y-%m-%d")
    #    if until_date is not None:
    #        datetime.strptime(until_date, "%Y-%m-%d")
    #except:
    #    return BadArgument(base_url)

    # get the result set size
    list_size = app.config.get("OAIPMH_LIST_RECORDS_PAGE_SIZE", 25)

    # decode the oai_set to something we can query with
    try:
        decoded_set = decode_set_spec(oai_set) if oai_set is not None else None
    except SetSpecException:
        return BadArgument(base_url)

    for f in formats:
        if f.get("metadataPrefix") == metadata_prefix:
            # do the query and set up the response object
            total, results = dao.list_records(from_date, until_date, decoded_set, list_size, start_number, start_after)

            # if there are no results, PMH requires us to throw an error
            if len(results) == 0:
                return NoRecordsMatch(base_url)

            # get the full total
            full_total = total
            if start_after is not None:
                full_total = total + start_number - start_after[1]

            # work out if we need a resumption token.  It can have one of 3 values:
            # - None = do not include the rt in the response
            # - some value = include in the response
            # - the empty string = include in the response
            resumption_token = None
            if total > len(results):
                start_after = get_start_after(results)
                new_start = start_number + len(results)
                resumption_token = make_resumption_token(metadata_prefix=metadata_prefix, from_date=from_date,
                    until_date=until_date, oai_set=oai_set, start_number=new_start, start_after=start_after)
            else:
                resumption_token = ""

            lr = ListRecords(base_url, from_date=from_date, until_date=until_date, oai_set=oai_set, metadata_prefix=metadata_prefix)
            if resumption_token is not None:
                expiry = app.config.get("OAIPMH_RESUMPTION_TOKEN_EXPIRY", -1)
                lr.set_resumption(resumption_token, complete_list_size=full_total, cursor=start_number, expiry=expiry)

            for r in results:
                # do the crosswalk
                xwalk = get_crosswalk(f.get("metadataPrefix"), dao.__type__)
                metadata = xwalk.crosswalk(r)
                header = xwalk.header(r)

                # add to the response
                lr.add_record(metadata, header)
            return lr

    # if we have not returned already, this means we can't disseminate this format
    return CannotDisseminateFormat(base_url)


def _resume_list_records(dao, base_url, specified_oai_endpoint, resumption_token=None):
    try:
        params = decode_resumption_token(resumption_token)
    except ResumptionTokenException:
        return BadResumptionToken(base_url)
    return _parameterised_list_records(dao, base_url, specified_oai_endpoint, **params)


def list_sets(dao, base_url, resumption_token=None):
    # This implementation does not support resumption tokens for this operation
    if resumption_token is not None:
        return BadResumptionToken(base_url)

    # just ask the DAO to get a list of all the sets for us, then we
    # give the set spec and set name as the same string
    ls = ListSets(base_url)
    sets = dao.list_sets()
    for s in sets:
        ls.add_set(make_set_spec(s), s)
    return ls


#####################################################################
# Objects
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
        return etree.tostring(xml, xml_declaration=True, encoding="UTF-8")

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
    def __init__(self, base_url, repo_name, admin_email):
        super(Identify, self).__init__(base_url)
        self.verb = "Identify"
        self.repo_name = repo_name
        self.admin_email = admin_email
        self.earliest_datestamp = None

    def get_element(self):
        identify = etree.Element(self.PMH + "Identify", nsmap=self.NSMAP)

        repo_name = etree.SubElement(identify, self.PMH + "repositoryName")
        repo_name.text = self.repo_name

        base = etree.SubElement(identify, self.PMH + "baseURL")
        base.text = self.base_url

        protocol = etree.SubElement(identify, self.PMH + "protocolVersion")
        protocol.text = self.VERSION

        admin_email = etree.SubElement(identify, self.PMH + "adminEmail")
        admin_email.text = self.admin_email

        earliest = etree.SubElement(identify, self.PMH + "earliestDatestamp")
        if self.earliest_datestamp is not None:
            earliest.text = self.earliest_datestamp
        else:
            # earliest.text = "1970-01-01T00:00:00Z" # beginning of the unix epoch
            DateFormat.default_earliest()

        deletes = etree.SubElement(identify, self.PMH + "deletedRecord")
        deletes.text = "transient" # keep the door open

        granularity = etree.SubElement(identify, self.PMH + "granularity")
        # granularity.text = "YYYY-MM-DD"
        granularity.text = DateFormat.granularity()

        return identify


class ListIdentifiers(OAI_PMH):
    def __init__(self, base_url, from_date=None, until_date=None, oai_set=None, metadata_prefix=None):
        super(ListIdentifiers, self).__init__(base_url)
        self.verb = "ListIdentifiers"
        self.from_date = from_date
        self.until_date = until_date
        self.oai_set = oai_set
        self.metadata_prefix = metadata_prefix
        self.records = []
        self.resumption = None

    def set_resumption(self, resumption_token, complete_list_size=None, cursor=None, expiry=-1):
        self.resumption = {"resumption_token" : resumption_token, "expiry" : expiry}
        if complete_list_size is not None:
            self.resumption["complete_list_size"] = complete_list_size
        if cursor is not None:
            self.resumption["cursor"] = cursor

    def add_record(self, header):
        self.records.append(header)

    def add_request_attributes(self, element):
        if self.from_date is not None:
            element.set("from", self.from_date)
        if self.until_date is not None:
            element.set("until", self.until_date)
        if self.oai_set is not None:
            element.set("set", self.oai_set)
        if self.metadata_prefix is not None:
            element.set("metadataPrefix", self.metadata_prefix)

    def get_element(self):
        lr = etree.Element(self.PMH + "ListIdentifiers", nsmap=self.NSMAP)

        for header in self.records:
            lr.append(header)

        if self.resumption is not None:
            rt = etree.SubElement(lr, self.PMH + "resumptionToken")
            if "complete_list_size" in self.resumption:
                rt.set("completeListSize", str(self.resumption.get("complete_list_size")))
            if "cursor" in self.resumption:
                rt.set("cursor", str(self.resumption.get("cursor")))
            expiry = self.resumption.get("expiry", -1)
            expire_date = None
            if expiry >= 0:
                # expire_date = (datetime.now() + timedelta(0, expiry)).strftime("%Y-%m-%dT%H:%M:%SZ")
                expire_date = DateFormat.format(datetime.now() + timedelta(0, expiry))
                rt.set("expirationDate", expire_date)
            rt.text = self.resumption.get("resumption_token")

        return lr


class ListMetadataFormats(OAI_PMH):
    def __init__(self, base_url, identifier=None):
        super(ListMetadataFormats, self).__init__(base_url)
        self.verb = "ListMetadataFormats"
        self.identifier = identifier
        self.formats = []

    def add_format(self, metadata_prefix, schema, metadata_namespace):
        self.formats.append(
            {
                "metadataPrefix": metadata_prefix,
                "schema": schema,
                "metadataNamespace": metadata_namespace
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
    def __init__(self, base_url, from_date=None, until_date=None, oai_set=None, metadata_prefix=None):
        super(ListRecords, self).__init__(base_url)
        self.verb = "ListRecords"
        self.from_date = from_date
        self.until_date = until_date
        self.oai_set = oai_set
        self.metadata_prefix = metadata_prefix
        self.records = []
        self.resumption = None
        self.resumption_expiry = -1

    def set_resumption(self, resumption_token, complete_list_size=None, cursor=None, expiry=-1):
        self.resumption = {"resumption_token" : resumption_token, "expiry" : expiry}
        if complete_list_size is not None:
            self.resumption["complete_list_size"] = complete_list_size
        if cursor is not None:
            self.resumption["cursor"] = cursor

    def add_record(self, metadata, header):
        self.records.append((metadata, header))

    def add_request_attributes(self, element):
        if self.from_date is not None:
            element.set("from", self.from_date)
        if self.until_date is not None:
            element.set("until", self.until_date)
        if self.oai_set is not None:
            element.set("set", self.oai_set)
        if self.metadata_prefix is not None:
            element.set("metadataPrefix", self.metadata_prefix)

    def get_element(self):
        lr = etree.Element(self.PMH + "ListRecords", nsmap=self.NSMAP)

        for metadata, header in self.records:
            r = etree.SubElement(lr, self.PMH + "record")
            r.append(header)
            r.append(metadata)

        if self.resumption is not None:
            rt = etree.SubElement(lr, self.PMH + "resumptionToken")
            if "complete_list_size" in self.resumption:
                rt.set("completeListSize", str(self.resumption.get("complete_list_size")))
            if "cursor" in self.resumption:
                rt.set("cursor", str(self.resumption.get("cursor")))
            expiry = self.resumption.get("expiry", -1)
            expire_date = None
            if expiry >= 0:
                # expire_date = (datetime.now() + timedelta(0, expiry)).strftime("%Y-%m-%dT%H:%M:%SZ")
                expire_date = DateFormat.format(datetime.now() + timedelta(0, expiry))
                rt.set("expirationDate", expire_date)
            rt.text = self.resumption.get("resumption_token")

        return lr


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
# Error Handling
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
# Crosswalks
#####################################################################

class OAI_Crosswalk(object):
    PMH_NAMESPACE = "http://www.openarchives.org/OAI/2.0/"
    PMH = "{%s}" % PMH_NAMESPACE

    XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    XSI = "{%s}" % XSI_NAMESPACE

    NSMAP = {None: PMH_NAMESPACE, "xsi": XSI_NAMESPACE}

    def crosswalk(self, record):
        raise NotImplementedError()

    def header(self, record):
        raise NotImplementedError()

    def _generate_header_subjects(self, parent_element, subjects):
        if subjects is None:
            subjects = []

        for subs in subjects:
            scheme = subs.get("scheme", '')
            term = subs.get("term", '')

            if term:
                prefix = ''
                if scheme:
                    prefix = scheme + ':'

                subel = etree.SubElement(parent_element, self.PMH + "setSpec")
                set_text(subel, make_set_spec(prefix + term))


class OAI_DC(OAI_Crosswalk):
    OAIDC_NAMESPACE = "http://www.openarchives.org/OAI/2.0/oai_dc/"
    OAIDC = "{%s}" % OAIDC_NAMESPACE

    DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
    DC = "{%s}" % DC_NAMESPACE

    NSMAP = deepcopy(OAI_Crosswalk.NSMAP)
    NSMAP.update({"oai_dc": OAIDC_NAMESPACE, "dc": DC_NAMESPACE})

    def _generate_subjects(self, parent_element, subjects, keywords):
        if keywords is None:
            keywords = []
        if subjects is None:
            subjects = []

        for keyword in keywords:
            subj = etree.SubElement(parent_element, self.DC + "subject")
            set_text(subj, keyword)

        for subs in subjects:
            scheme = subs.get("scheme")
            code = subs.get("code")
            term = subs.get("term")

            if scheme and scheme.lower() == 'lcc':
                attrib = {"{{{nspace}}}type".format(nspace=self.XSI_NAMESPACE): "dcterms:LCSH"}
                termtext = term
                codetext = code
            else:
                attrib = {}
                termtext = scheme + ':' + term if term else None
                codetext = scheme + ':' + code if code else None

            if termtext:
                subel = etree.SubElement(parent_element, self.DC + "subject", **attrib)
                set_text(subel, termtext)

            if codetext:
                sel2 = etree.SubElement(parent_element, self.DC + "subject", **attrib)
                set_text(sel2, codetext)


class OAI_DC_Article(OAI_DC):
    def crosswalk(self, record):
        bibjson = record.bibjson()

        metadata = etree.Element(self.PMH + "metadata", nsmap=self.NSMAP)
        oai_dc = etree.SubElement(metadata, self.OAIDC + "dc")
        oai_dc.set(self.XSI + "schemaLocation",
            "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd")

        if bibjson.title is not None:
            title = etree.SubElement(oai_dc, self.DC + "title")
            set_text(title, bibjson.title)

        # all the external identifiers (ISSNs, etc)
        for identifier in bibjson.get_identifiers():
            idel = etree.SubElement(oai_dc, self.DC + "identifier")
            set_text(idel, identifier.get("id"))

        # our internal identifier
        url = app.config['BASE_URL'] + "/article/" + record.id
        idel = etree.SubElement(oai_dc, self.DC + "identifier")
        set_text(idel, url)

        # work out the date of publication
        date = bibjson.get_publication_date()
        if date != "":
            monthyear = etree.SubElement(oai_dc, self.DC + "date")
            set_text(monthyear, date)

        for url in bibjson.get_urls():
            urlel = etree.SubElement(oai_dc, self.DC + "relation")
            set_text(urlel, url.get("url"))

        for identifier in bibjson.get_identifiers(idtype=bibjson.P_ISSN) + bibjson.get_identifiers(idtype=bibjson.E_ISSN):
            journallink = etree.SubElement(oai_dc, self.DC + "relation")
            set_text(journallink, app.config['BASE_URL'] + "/toc/" + identifier)

        if bibjson.abstract is not None:
            abstract = etree.SubElement(oai_dc, self.DC + "description")
            set_text(abstract, bibjson.abstract)

        if len(bibjson.author) > 0:
            for author in bibjson.author:
                ael = etree.SubElement(oai_dc, self.DC + "creator")
                set_text(ael, author.get("name"))

        if bibjson.publisher is not None:
            pubel = etree.SubElement(oai_dc, self.DC + "publisher")
            set_text(pubel, bibjson.publisher)

        objecttype = etree.SubElement(oai_dc, self.DC + "type")
        set_text(objecttype, "article")

        self._generate_subjects(parent_element=oai_dc, subjects=bibjson.subjects(), keywords=bibjson.keywords)

        jlangs = bibjson.journal_language
        if jlangs is not None:
            for language in jlangs:
                langel = etree.SubElement(oai_dc, self.DC + "language")
                set_text(langel, language)

        if bibjson.get_journal_license() is not None:
            prov = etree.SubElement(oai_dc, self.DC + "provenance")
            set_text(prov, "Journal Licence: " + bibjson.get_journal_license().get("title"))

        citation = self._make_citation(bibjson)
        if citation is not None:
            cite = etree.SubElement(oai_dc, self.DC + "source")
            set_text(cite, citation)

        return metadata

    def header(self, record):
        bibjson = record.bibjson()
        head = etree.Element(self.PMH + "header", nsmap=self.NSMAP)

        identifier = etree.SubElement(head, self.PMH + "identifier")
        set_text(identifier, make_oai_identifier(record.id, "article"))

        datestamp = etree.SubElement(head, self.PMH + "datestamp")
        set_text(datestamp, normalise_date(record.last_updated))

        self._generate_header_subjects(parent_element=head, subjects=bibjson.subjects())
        return head

    def _make_citation(self, bibjson):
        # [title], Vol [vol], Iss [iss], Pp [start]-end (year)
        ctitle = bibjson.journal_title
        cvol = bibjson.volume
        ciss = bibjson.number
        cstart = bibjson.start_page
        cend = bibjson.end_page
        cyear = bibjson.year

        citation = ""
        if ctitle is not None:
            citation += ctitle

        if cvol is not None:
            if citation != "":
                citation += ", "
            citation += "Vol " + cvol

        if ciss is not None:
            if citation != "":
                citation += ", "
            citation += "Iss " + ciss

        if cstart is not None or cend is not None:
            if citation != "":
                citation += ", "
            if (cstart is None and cend is not None) or (cstart is not None and cend is None):
                citation += "p "
            else:
                citation += "Pp "
            if cstart is not None:
                citation += cstart
            if cend is not None:
                if cstart is not None:
                    citation += "-"
                citation += cend

        if cyear is not None:
            if citation != "":
                citation += " "
            citation += "(" + cyear + ")"

        return citation if citation != "" else None


class OAI_DC_Journal(OAI_DC):
    def crosswalk(self, record):
        bibjson = record.bibjson()

        metadata = etree.Element(self.PMH + "metadata", nsmap=self.NSMAP)
        oai_dc = etree.SubElement(metadata, self.OAIDC + "dc")
        oai_dc.set(self.XSI + "schemaLocation",
            "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd")

        if bibjson.title is not None:
            title = etree.SubElement(oai_dc, self.DC + "title")
            set_text(title, bibjson.title)

        # external identifiers (ISSNs, etc)
        for identifier in bibjson.get_identifiers():
            idel = etree.SubElement(oai_dc, self.DC + "identifier")
            set_text(idel, identifier.get("id"))

        # our internal identifier
        url = app.config["BASE_URL"] + "/toc/" + record.toc_id
        idel = etree.SubElement(oai_dc, self.DC + "identifier")
        set_text(idel, url)

        if bibjson.language is not None and len(bibjson.language) > 0:
            for language in bibjson.language:
                lang = etree.SubElement(oai_dc, self.DC + "language")
                set_text(lang, language)

        if bibjson.author_pays_url is not None:
            relation = etree.SubElement(oai_dc, self.DC + "relation")
            set_text(relation, bibjson.author_pays_url)

        if bibjson.get_license() is not None:
            rights = etree.SubElement(oai_dc, self.DC + "rights")
            set_text(rights, bibjson.get_license().get("title"))

        if bibjson.publisher is not None:
            pub = etree.SubElement(oai_dc, self.DC + "publisher")
            set_text(pub, bibjson.publisher)

        if len(bibjson.get_urls()) > 0:
            for url in bibjson.get_urls():
                urlel = etree.SubElement(oai_dc, self.DC + "relation")
                set_text(urlel, url.get("url"))

        if bibjson.provider is not None:
            prov = etree.SubElement(oai_dc, self.DC + "publisher")
            set_text(prov, bibjson.provider)

        created = etree.SubElement(oai_dc, self.DC + "date")
        set_text(created, normalise_date(record.created_date))

        objecttype = etree.SubElement(oai_dc, self.DC + "type")
        set_text(objecttype, "journal")

        self._generate_subjects(parent_element=oai_dc, subjects=bibjson.subjects(), keywords=bibjson.keywords)

        return metadata

    def header(self, record):
        bibjson = record.bibjson()
        head = etree.Element(self.PMH + "header", nsmap=self.NSMAP)

        identifier = etree.SubElement(head, self.PMH + "identifier")
        set_text(identifier, make_oai_identifier(record.id, "journal"))

        datestamp = etree.SubElement(head, self.PMH + "datestamp")
        set_text(datestamp, normalise_date(record.last_updated))

        self._generate_header_subjects(parent_element=head, subjects=bibjson.subjects())
        return head


class OAI_DOAJ_Article(OAI_Crosswalk):
    OAI_DOAJ_NAMESPACE = "http://doaj.org/features/oai_doaj/1.0/"
    OAI_DOAJ = "{%s}" % OAI_DOAJ_NAMESPACE

    NSMAP = deepcopy(OAI_Crosswalk.NSMAP)
    NSMAP.update({"oai_doaj": OAI_DOAJ_NAMESPACE})

    def crosswalk(self, record):
        bibjson = record.bibjson()

        metadata = etree.Element(self.PMH + "metadata", nsmap=self.NSMAP)
        oai_doaj_article = etree.SubElement(metadata, self.OAI_DOAJ + "doajArticle")
        oai_doaj_article.set(self.XSI + "schemaLocation",
            "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd http://doaj.org/features/oai_doaj/1.0/ https://doaj.org/static/doaj/doajArticles.xsd")

        # look up the journal's language
        jlangs = bibjson.journal_language
        # first, if there are any languages recorded, get the 3-char code
        # corresponding to the first language
        language = None
        if jlangs:
            if isinstance(jlangs, list):
                jlangs = jlangs[0]
            if jlangs in datasets.languages_3char_code_index:
                language = jlangs.lower()
            else:
                char3 = datasets.languages_fullname_to_3char_code.get(jlangs)
                if char3 is None:
                    char3 = datasets.languages_dict.get(jlangs, {}).get("iso639-3_code")
                if char3 is not None:
                    language = char3.lower()

        # if the language code lookup was successful, add it to the
        # result
        if language:
            langel = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "language")
            set_text(langel, language)

        if bibjson.publisher:
            publel = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "publisher")
            set_text(publel, bibjson.publisher)

        if bibjson.journal_title:
            journtitel = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "journalTitle")
            set_text(journtitel, bibjson.journal_title)

        # all the external identifiers (ISSNs, etc)
        if bibjson.get_one_identifier(bibjson.P_ISSN):
            issn = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "issn")
            set_text(issn, bibjson.get_one_identifier(bibjson.P_ISSN))

        if bibjson.get_one_identifier(bibjson.E_ISSN):
            eissn = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "eissn")
            set_text(eissn, bibjson.get_one_identifier(bibjson.E_ISSN))

        # work out the date of publication
        date = bibjson.get_publication_date()
        # convert it to the format required by the XML schema by parsing
        # it into a Python datetime and getting it back out as string.
        # If it's not coming back properly from the bibjson, throw it
        # away.
        try:
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
            date = date.strftime("%Y-%m-%d")
        except:
            date = ""

        if date:
            monthyear = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "publicationDate")
            set_text(monthyear, date)

        if bibjson.volume:
            volume = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "volume")
            set_text(volume, bibjson.volume)

        if bibjson.number:
            issue = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "issue")
            set_text(issue, bibjson.number)

        if bibjson.start_page:
            start_page = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "startPage")
            set_text(start_page, bibjson.start_page)

        if bibjson.end_page:
            end_page = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "endPage")
            set_text(end_page, bibjson.end_page)

        if bibjson.get_one_identifier(bibjson.DOI):
            doi = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "doi")
            set_text(doi, bibjson.get_one_identifier(bibjson.DOI))

        if record.publisher_record_id():
            pubrecid = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "publisherRecordId")
            set_text(pubrecid, record.publisher_record_id())

        # document type
        # as of Mar 2015 this was not being ingested when people upload XML
        # conforming to the doajArticle schema, so it's not being output either

        if bibjson.title is not None:
            title = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "title")
            set_text(title, bibjson.title)

        affiliations = []
        if bibjson.author:
            authors_elem = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "authors")
            for author in bibjson.author:  # bibjson.author is a list, despite the name
                author_elem = etree.SubElement(authors_elem, self.OAI_DOAJ + "author")
                if author.get('name'):
                    name_elem = etree.SubElement(author_elem, self.OAI_DOAJ + "name")
                    set_text(name_elem, author.get('name'))
                if author.get('email'):
                    email_elem = etree.SubElement(author_elem, self.OAI_DOAJ + "email")
                    set_text(email_elem, author.get('email'))
                if author.get('affiliation'):
                    new_affid = len(affiliations)  # use the length of the list as the id for each new item
                    affiliations.append((new_affid, author['affiliation']))
                    author_affiliation_elem = etree.SubElement(author_elem, self.OAI_DOAJ + "affiliationId")
                    set_text(author_affiliation_elem, str(new_affid))

        if affiliations:
            affiliations_elem = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "affiliationsList")
            for affid, affiliation in affiliations:
                attrib = {"affiliationId": str(affid)}
                affiliation_elem = etree.SubElement(affiliations_elem, self.OAI_DOAJ + "affiliationName", **attrib)
                set_text(affiliation_elem, affiliation)

        if bibjson.abstract:
            abstract = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "abstract")
            set_text(abstract, bibjson.abstract)

        ftobj = bibjson.get_single_url('fulltext', unpack_urlobj=False)
        if ftobj:
            attrib = {}
            if "content_type" in ftobj:
                attrib['format'] = ftobj['content_type']

            fulltext_url_elem = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "fullTextUrl", **attrib)

            if "url" in ftobj:
                set_text(fulltext_url_elem, ftobj['url'])

        if bibjson.keywords:
            keywords_elem = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + 'keywords')
            for keyword in bibjson.keywords:
                kel = etree.SubElement(keywords_elem, self.OAI_DOAJ + 'keyword')
                set_text(kel, keyword)

        return metadata

    def header(self, record):
        bibjson = record.bibjson()
        head = etree.Element(self.PMH + "header", nsmap=self.NSMAP)

        identifier = etree.SubElement(head, self.PMH + "identifier")
        set_text(identifier, make_oai_identifier(record.id, "article"))

        datestamp = etree.SubElement(head, self.PMH + "datestamp")
        set_text(datestamp, normalise_date(record.last_updated))

        self._generate_header_subjects(parent_element=head, subjects=bibjson.subjects())
        return head


CROSSWALKS = {
    "oai_dc": {
        "article": OAI_DC_Article,
        "journal": OAI_DC_Journal
    },
    'oai_doaj': {
        "article": OAI_DOAJ_Article
    }
}
