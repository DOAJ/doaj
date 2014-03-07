from datetime import datetime
from copy import deepcopy
import json
import locale
import sys

from portality.core import app
from portality.dao import DomainObject as DomainObject
from portality.authorise import Authorise
from portality import xwalk

from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

############################################################################
# Generic/Utility classes and functions
############################################################################

class GenericBibJSON(object):
    # vocab of known identifier types
    P_ISSN = "pissn"
    E_ISSN = "eissn"
    DOI = "doi"
    
    # allowable values for the url types
    HOMEPAGE = "homepage"
    WAIVER_POLICY = "waiver_policy"
    EDITORIAL_BOARD = "editorial_board"
    AIMS_SCOPE = "aims_scope"
    AUTHOR_INSTRUCTIONS = "author_instructions"
    OA_STATEMENT = "oa_statement"
    FULLTEXT = "fulltext"
    
    # constructor
    def __init__(self, bibjson=None):
        self.bibjson = bibjson if bibjson is not None else {}
    
    # generic property getter and setter for ad-hoc extensions
    def get_property(self, prop):
        return self.bibjson.get(prop)
    
    def set_property(self, prop, value):
        self.bibjson[prop] = value
    
    # shared simple property getter and setters
        
    @property
    def title(self): return self.bibjson.get("title")
    @title.setter
    def title(self, val) : self.bibjson["title"] = val
    
    # complex getters and setters
    
    def _normalise_identifier(self, idtype, value):
        if idtype in [self.P_ISSN, self.E_ISSN]:
            return self._normalise_issn(value)
        return value
    
    def _normalise_issn(self, issn):
        issn = issn.upper()
        if len(issn) > 8: return issn
        if len(issn) == 8:
            if "-" in issn: return "0" + issn
            else: return issn[:4] + "-" + issn[4:]
        if len(issn) < 8:
            if "-" in issn: return ("0" * (9 - len(issn))) + issn
            else:
                issn = ("0" * (8 - len(issn))) + issn
                return issn[:4] + "-" + issn[4:]
    
    def add_identifier(self, idtype, value):
        if "identifier" not in self.bibjson:
            self.bibjson["identifier"] = []
        idobj = {"type" : idtype, "id" : self._normalise_identifier(idtype, value)}
        self.bibjson["identifier"].append(idobj)
    
    def get_identifiers(self, idtype=None):
        if idtype is None:
            return self.bibjson.get("identifier", [])
        
        ids = []
        for identifier in self.bibjson.get("identifier", []):
            if identifier.get("type") == idtype and identifier.get("id") not in ids:
                ids.append(identifier.get("id"))
        return ids

    def get_one_identifier(self, idtype=None):
        results = self.get_identifiers(idtype=idtype)
        if results:
            return results[0]
        else:
            return None

    def update_identifier(self, idtype, new_value):
        if not new_value:
            self.remove_identifiers(idtype=idtype)
            return

        if 'identifier' not in self.bibjson:
            return

        if not self.get_one_identifier(idtype):
            self.add_identifier(idtype, new_value)
            return

        # so an old identifier does actually exist, and we actually want
        # to update it
        for id_ in self.bibjson['identifier']:
            if id_['type'] == idtype:
                id_['id'] = new_value
    
    def remove_identifiers(self, idtype=None, id=None):
        # if we are to remove all identifiers, this is easy
        if idtype is None and id is None:
            self.bibjson["identifier"] = []
            return
        
        # else, find all the identifiers positions that we need to remove
        idx = 0
        remove = []
        for identifier in self.bibjson.get("identifier", []):
            if idtype is not None and id is None:
                if identifier.get("type") == idtype:
                    remove.append(idx)
            elif idtype is None and id is not None:
                if identifier.get("id") == id:
                    remove.append(idx)
            else:
                if identifier.get("type") == idtype and identifier.get("id") == id:
                    remove.append(idx)
            idx += 1
        
        # sort the positions of the ids to remove, largest first
        remove.sort(reverse=True)
        
        # now remove them one by one (having the largest first means the lower indices
        # are not affected
        for i in remove:
            del self.bibjson["identifier"][i]
    
    @property
    def keywords(self):
        return self.bibjson.get("keywords", [])
    
    def add_keyword(self, keyword):
        if "keywords" not in self.bibjson:
            self.bibjson["keywords"] = []
        self.bibjson["keywords"].append(keyword)
    
    def set_keywords(self, keywords):
        self.bibjson["keywords"] = keywords
    
    def add_url(self, url, urltype=None, content_type=None):
        if "link" not in self.bibjson:
            self.bibjson["link"] = []
        urlobj = {"url" : url}
        if urltype is not None:
            urlobj["type"] = urltype
        if content_type is not None:
            urlobj["content_type"] = content_type
        self.bibjson["link"].append(urlobj)
    
    def get_urls(self, urltype=None):
        if urltype is None:
            return self.bibjson.get("link", [])
        
        urls = []
        for link in self.bibjson.get("link", []):
            if link.get("type") == urltype:
                urls.append(link.get("url"))
        return urls

    def get_single_url(self, urltype):
        urls = self.get_urls(urltype=urltype)
        if urls:
            return urls[0]
        return None

    def update_url(self, url, urltype=None):
        if "link" not in self.bibjson:
            self.bibjson['link'] = []

        urls = self.bibjson['link']

        if urls:
            for u in urls: # do not reuse "url" as it's a parameter!
                if u['type'] == urltype:
                    u['url'] = url
        else:
            self.add_url(url, urltype)
    
    def add_subject(self, scheme, term, code=None):
        if "subject" not in self.bibjson:
            self.bibjson["subject"] = []
        sobj = {"scheme" : scheme, "term" : term}
        if code is not None:
            sobj["code"] = code
        self.bibjson["subject"].append(sobj)
    
    def subjects(self):
        return self.bibjson.get("subject", [])

############################################################################

####################################################################
## File upload model
####################################################################

class FileUpload(DomainObject):
    __type__ = "upload"
    
    @property
    def local_filename(self):
        return self.id + ".xml"
    
    @property
    def filename(self):
        return self.data.get("filename")
    
    @property
    def schema(self):
        return self.data.get("schema")
    
    @property
    def owner(self):
        return self.data.get("owner")
    
    @property
    def imported(self):
        return self.data.get("imported", 0)
    
    @property
    def failed_imports(self):
        return self.data.get("failed", 0)
    
    @property
    def updates(self):
        return self.data.get("update", 0)
    
    @property
    def new(self):
        return self.data.get("new", 0)
    
    def set_schema(self, s):
        self.data["schema"] = s
    
    def upload(self, owner, filename, status="incoming"):
        self.data["filename"] = filename
        self.data["owner"] = owner
        self.data["status"] = status
    
    def failed(self, message):
        self.data["status"] = "failed"
        self.data["error"] = message
    
    def validated(self, schema):
        self.data["status"] = "validated"
        self.data["schema"] = schema
    
    def processed(self, count, update, new):
        self.data["status"] = "processed"
        self.data["imported"] = count
        self.data["update"] = update
        self.data["new"] = new
    
    def partial(self, success, fail, update, new):
        self.data["status"] = "partial"
        self.data["imported"] = success
        self.data["failed"] = fail
        self.data["update"] = update
        self.data["new"] = new
    
    def exists(self):
        self.data["status"] = "exists"
    
    def downloaded(self):
        self.data["status"] = "downloaded"
    
    def created_timestamp(self):
        if "created_date" not in self.data:
            return None
        return datetime.strptime(self.data["created_date"], "%Y-%m-%dT%H:%M:%SZ")
    
    @classmethod
    def list_valid(self):
        q = ValidFileQuery()
        return self.iterate(q=q.query(), page_size=10000)
    
    @classmethod
    def list_remote(self):
        q = ExistsFileQuery()
        return self.iterate(q=q.query(), page_size=10000)
        
    @classmethod
    def by_owner(self, owner, size=10):
        q = OwnerFileQuery(owner)
        res = self.query(q=q.query())
        rs = [FileUpload(**r.get("_source")) for r in res.get("hits", {}).get("hits", [])]
        return rs

class ValidFileQuery(object):
    base_query = {
        "query" : {
            "term" : { "status.exact" : "validated" }
        },
        "sort" : [
            {"created_date" : "asc"}
        ]
    }
    def __init__(self):
        self._query = deepcopy(self.base_query)
    
    def query(self):
        return self._query

class ExistsFileQuery(object):
    base_query = {
        "query" : {
            "term" : { "status.exact" : "exists" }
        },
        "sort" : [
            {"created_date" : "asc"}
        ]
    }
    def __init__(self):
        self._query = deepcopy(self.base_query)
    
    def query(self):
        return self._query

class OwnerFileQuery(object):
    base_query = {
        "query" : {
            "bool" : {
                "must" : []
            }
        },
        "sort" : [
            {"created_date" : "desc"}
        ],
        "size" : 10
    }
    def __init__(self, owner, size=10):
        self._query = deepcopy(self.base_query)
        owner_term = {"term" : {"owner" : owner}}
        self._query["query"]["bool"]["must"].append(owner_term)
        self._query["size"] = size
    
    def query(self):
        return self._query

####################################################################

####################################################################
## Account object and related classes
####################################################################

class Account(DomainObject, UserMixin):
    __type__ = 'account'

    @classmethod
    def pull_by_email(cls, email):
        res = cls.query(q='email:"' + email + '"')
        if res.get('hits',{}).get('total',0) == 1:
            return cls(**res['hits']['hits'][0]['_source'])
        else:
            return None
    
    @property
    def name(self):
        return self.data.get("name")
    
    def set_name(self, name):
        self.data["name"] = name
    
    @property
    def email(self):
        return self.data.get("email")

    def set_email(self, email):
        self.data["email"] = email

    def set_password(self, password):
        self.data['password'] = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.data['password'], password)
        
    @property
    def journal(self):
        return self.data.get("journal")
    
    def add_journal(self, jid):
        if jid in self.data.get("journal", []):
            return
        if "journal" not in self.data:
            self.data["journal"] = []
        self.data["journal"].append(jid)
    
    def remove_journal(self, jid):
        if "journal" not in self.data:
            return
        self.data["journal"].remove(jid)

    @property
    def is_super(self):
        # return not self.is_anonymous() and self.id in app.config['SUPER_USER']
        return Authorise.has_role(app.config["SUPER_USER_ROLE"], self.data.get("role", []))
    
    def has_role(self, role):
        return Authorise.has_role(role, self.data.get("role", []))
    
    def add_role(self, role):
        if "role" not in self.data:
            self.data["role"] = []
        self.data["role"].append(role)
    
    @property
    def role(self):
        return self.data.get("role", [])
    
    def set_role(self, role):
        if not isinstance(role, list):
            role = [role]
        self.data["role"] = role
            
    def prep(self):
        self.data['last_updated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

#########################################################################


#########################################################################
## Journal object and related classes
#########################################################################

# NOTE: DomainObject interferes with new style @property getter/setter
# so we can't use them here
class Journal(DomainObject):
    __type__ = "journal"
    CSV_HEADER = ["Title", "Title Alternative", "Identifier", "Publisher", "Language",
                    "ISSN", "EISSN", "Keyword", "Start Year", "End Year", "Added on date",
                    "Subjects", "Country", "Publication fee", "Further Information", 
                    "CC License", "Content in DOAJ"]
    
    @classmethod
    def find_by_issn(self, issn):
        q = JournalQuery()
        q.find_by_issn(issn)
        result = self.query(q=q.query)
        records = [Journal(**r.get("_source")) for r in result.get("hits", {}).get("hits", [])]
        return records
    
    @classmethod
    def all_in_doaj(cls, page_size=5000):
        q = JournalQuery()
        return cls.iterate(q.all_in_doaj(), page_size=page_size)
    
    @classmethod
    def issns_by_owner(cls, owner):
        q = IssnQuery(owner)
        res = cls.query(q=q.query())
        issns = [term.get("term") for term in res.get("facets", {}).get("issns", {}).get("terms", [])]
        return issns
    
    @classmethod
    def find_by_publisher(cls, publisher, exact=True):
        q = PublisherQuery(publisher, exact)
        result = cls.query(q=q.query())
        records = [Journal(**r.get("_source")) for r in result.get("hits", {}).get("hits", [])]
        return records
    
    @classmethod
    def find_by_title(cls, title):
        q = TitleQuery(title)
        result = cls.query(q=q.query())
        records = [Journal(**r.get("_source")) for r in result.get("hits", {}).get("hits", [])]
        return records
    
    def bibjson(self):
        if "bibjson" not in self.data:
            self.data["bibjson"] = {}
        return JournalBibJSON(self.data.get("bibjson"))

    def set_bibjson(self, bibjson):
        bibjson = bibjson.bibjson if isinstance(bibjson, JournalBibJSON) else bibjson
        self.data["bibjson"] = bibjson
    
    def history(self):
        histories = self.data.get("history", [])
        return [(h.get("date"), h.get("replaces"), h.get("isreplacedby"), JournalBibJSON(h.get("bibjson"))) for h in histories]
    
    def snapshot(self, replaces=None, isreplacedby=None):
        snap = deepcopy(self.data.get("bibjson"))
        self.add_history(snap, replaces=replaces, isreplacedby=isreplacedby)
    
    def add_history(self, bibjson, date=None, replaces=None, isreplacedby=None):
        bibjson = bibjson.bibjson if isinstance(bibjson, JournalBibJSON) else bibjson
        if date is None:
            date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        snobj = {"date" : date, "bibjson" : bibjson}
        if replaces is not None:
            if isinstance(replaces, list):
                snobj["replaces"] = replaces
            else:
                snobj["replaces"] = [replaces]
        if isreplacedby is not None:
            if isinstance(isreplacedby, list):
                snobj["isreplacedby"] = isreplacedby
            else:
                snobj["isreplacedby"] = [replaces]
        if "history" not in self.data:
            self.data["history"] = []
        self.data["history"].append(snobj)
    
    def is_in_doaj(self):
        return self.data.get("admin", {}).get("in_doaj", False)
    
    def set_in_doaj(self, value):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["in_doaj"] = value
    
    @property
    def application_status(self):
        return self.data.get("admin", {}).get("application_status")
    
    def set_application_status(self, value):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["application_status"] = value
    
    def contacts(self):
        return self.data.get("admin", {}).get("contact", [])
        
    def add_contact(self, name, email):
        if "admin" not in self.data:
            self.data["admin"] = {}
        if "contact" not in self.data["admin"]:
            self.data["admin"]["contact"] = []
        self.data["admin"]["contact"].append({"name" : name, "email" : email})
    
    def add_note(self, note, date=None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        if "admin" not in self.data:
            self.data["admin"] = {}
        if "notes" not in self.data.get("admin"):
            self.data["admin"]["notes"] = []
        self.data["admin"]["notes"].append({"date" : date, "note" : note})
    
    def notes(self):
        return self.data.get("admin", {}).get("notes", [])
    
    def add_correspondence(self, message, date=None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        if "admin" not in self.data:
            self.data["admin"] = {}
        if "owner_correspondence" not in self.data.get("admin"):
            self.data["admin"]["owner_correspondence"] = []
        self.data["admin"]["owner_correspondence"].append({"date" : date, "note" : message})
    
    def correspondence(self):
        return self.data.get("admin", {}).get("owner_correspondence", [])
    
    @property
    def owner(self):
        return self.data.get("admin", {}).get("owner")
    
    def set_owner(self, owner):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["owner"] = owner
    
    def _generate_index(self):
        # the index fields we are going to generate
        issns = []
        titles = []
        subjects = []
        schema_subjects = []
        schema_codes = []
        classification = []
        langs = []
        country = None
        license = []
        publisher = []
        urls = {}
        
        # the places we're going to get those fields from
        cbib = self.bibjson()
        hist = self.history()
        
        # get the issns out of the current bibjson
        issns += cbib.get_identifiers(cbib.P_ISSN)
        issns += cbib.get_identifiers(cbib.E_ISSN)
        
        # get the title out of the current bibjson
        if cbib.title is not None:
            titles.append(cbib.title)
        
        # get the subjects and concatenate them with their schemes from the current bibjson
        for subs in cbib.subjects():
            scheme = subs.get("scheme")
            term = subs.get("term")
            subjects.append(term)
            schema_subjects.append(scheme + ":" + term)
            classification.append(term)
            if "code" in subs:
                schema_codes.append(scheme + ":" + subs.get("code"))
        
        # add the keywords to the non-schema subjects (but not the classification)
        subjects += cbib.keywords
        
        # now get the issns and titles out of the historic records
        for date, r, irb, hbib in hist:
            issns += hbib.get_identifiers(hbib.P_ISSN)
            issns += hbib.get_identifiers(hbib.E_ISSN)
            if hbib.title is not None:
                titles.append(hbib.title)
        
        # copy the languages
        if cbib.language is not None:
            langs = cbib.language
        
        # copy the country
        if cbib.country is not None:
            country = xwalk.get_country_name(cbib.country)
        
        # get the title of the license
        lic = cbib.get_license()
        if lic is not None:
            license.append(lic.get("title"))
        
        # copy the publisher/institution
        if cbib.publisher:
            publisher.append(cbib.publisher)
        if cbib.institution:
            publisher.append(cbib.institution)
        
        # extract and convert all of the urls by their type
        links = cbib.get_urls()
        for link in links:
            lt = link.get("type")
            if lt is not None:
                urls[lt + "_url"] = link.get("url")
        
        # deduplicate the lists
        issns = list(set(issns))
        titles = list(set(titles))
        subjects = list(set(subjects))
        schema_subjects = list(set(schema_subjects))
        classification = list(set(classification))
        license = list(set(license))
        publisher = list(set(publisher))
        langs = list(set(langs))
        schema_codes = list(set(schema_codes))
        
        # build the index part of the object
        self.data["index"] = {}
        if len(issns) > 0:
            self.data["index"]["issn"] = issns
        if len(titles) > 0:
            self.data["index"]["title"] = titles
        if len(subjects) > 0:
            self.data["index"]["subject"] = subjects
        if len(schema_subjects) > 0:
            self.data["index"]["schema_subject"] = schema_subjects
        if len(classification) > 0:
            self.data["index"]["classification"] = classification
        if len(publisher) > 0:
            self.data["index"]["publisher"] = publisher
        if len(license) > 0:
            self.data["index"]["license"] = license
        if len(langs) > 0:
            self.data["index"]["language"] = langs
        if country is not None:
            self.data["index"]["country"] = country
        if len(schema_codes) > 0:
            self.data["index"]["schema_code"] = schema_codes
        if len(urls.keys()) > 0:
            self.data["index"].update(urls)
    
    def _ensure_in_doaj(self):
        # switching active to false takes the item out of the DOAJ
        # though note that switching active to True does not put something IN the DOAJ
        if not self.bibjson().active:
            self.set_in_doaj(False)
    
    def prep(self):
        self._ensure_in_doaj()
        self._generate_index()
        self.data['last_updated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def save(self):
        self.prep()
        super(Journal, self).save()

    def csv(self, multival_sep=','):
        """
        CSV_HEADER = ["Title", "Title Alternative", "Identifier", "Publisher", "Language",
                    "ISSN", "EISSN", "Keyword", "Start Year", "End Year", "Added on date",
                    "Subjects", "Country", "Publication fee", "Further Information", 
                    "CC License", "Content in DOAJ"]
        """
        YES_NO = {True: 'Yes', False: 'No', None: '', '': ''}
        row = []
        
        bibjson = self.bibjson()
        index = self.data.get('index', {})
        row.append(bibjson.title) # Title
        row.append(bibjson.alternative_title) # Title Alternative
        row.append( multival_sep.join([u.get("url") for u in bibjson.get_urls()]) ) # Identifier
        row.append(bibjson.publisher)
        row.append( multival_sep.join(bibjson.language))

        # we're following the old CSV format strictly for now, so only 1
        # ISSN allowed - below is the code for handling multiple ones

        # ISSN taken from Print ISSN
        # row.append( multival_sep.join([id_['id'] for id_ in c['identifier'] if id_['type'] == 'pissn']) )
        pissns = bibjson.get_identifiers(bibjson.P_ISSN)
        row.append(pissns[0] if len(pissns) > 0 else '') # just the 1st one

        # EISSN - the same as ISSN applies
        # row.append( multival_sep.join([id_['id'] for id_ in c['identifier'] if id_['type'] == 'eissn']) )
        eissns = bibjson.get_identifiers(bibjson.E_ISSN)
        row.append(eissns[0] if len(eissns) > 0 else '') # just the 1st one

        row.append( multival_sep.join(bibjson.keywords) ) # Keywords
        row.append( bibjson.oa_start.get('year', '')) # Year OA began
        row.append( bibjson.oa_end.get('year', '')) # Year OA ended
        row.append( self.created_date ) # Date created
        row.append( multival_sep.join([subject['term'] for subject in bibjson.subjects()]) ) # Subject terms
        row.append( index.get('country', '') ) # Country
        row.append( bibjson.author_pays ) # author pays
        row.append(bibjson.author_pays_url) # author pays url

        # for now, follow the strange format of the CC License column
        # that the old CSV had. Also, only take the first CC license we see!
        lic = bibjson.get_license()
        if lic is not None:
            lt = lic.get("type", "")
            if lt.lower().startswith("cc"):
                row.append(lt[3:])
            else:
                row.append("")
        else:
            row.append("")
        #cc_licenses = [lic['type'][3:] for lic in c.get('license', []) if lic['type'].startswith('cc-')]
        #row.append(cc_licenses[0] if len(cc_licenses) > 0 else '')
        
        row.append(YES_NO.get(self.is_in_doaj(), ""))
        return row

class JournalBibJSON(GenericBibJSON):
    
    # journal-specific simple property getter and setters
    @property
    def alternative_title(self): return self.bibjson.get("alternative_title")
    @alternative_title.setter
    def alternative_title(self, val) : self.bibjson["alternative_title"] = val
    
    @property
    def author_pays_url(self): 
        """
        Deprecated - DO NOT USE
        """
        return None
        # url self.bibjson.get("author_pays_url")
        
        
    @author_pays_url.setter
    def author_pays_url(self, val): 
        """
        Deprecated - DO NOT USE
        """
        pass
        # self.bibjson["author_pays_url"] = val
    
    @property
    def author_pays(self): 
        """
        Deprecated - DO NOT USE
        """
        # return self.bibjson.get("author_pays")
        return None
        
    @author_pays.setter
    def author_pays(self, val): 
        """
        Deprecated - DO NOT USE
        """
        # self.bibjson["author_pays"] = val
        pass
    
    @property
    def country(self): return self.bibjson.get("country")
    @country.setter
    def country(self, val) : self.bibjson["country"] = val
    
    @property
    def publisher(self): return self.bibjson.get("publisher")
    @publisher.setter
    def publisher(self, val) : self.bibjson["publisher"] = val
    
    @property
    def provider(self): return self.bibjson.get("provider")
    @provider.setter
    def provider(self, val) : self.bibjson["provider"] = val
    
    @property
    def institution(self): return self.bibjson.get("institution")
    @institution.setter
    def institution(self, val) : self.bibjson["institution"] = val
    
    @property
    def active(self): return self.bibjson.get("active")
    @active.setter
    def active(self, val) : self.bibjson["active"] = val
    
    # journal-specific complex part getters and setters
    
    @property
    def language(self): 
        return self.bibjson.get("language")
    
    def set_language(self, language):
        if isinstance(language, list):
            self.bibjson["language"] = language
        else:
            self.bibjson["language"] = [language]
    
    def add_language(self, language):
        if "language" not in self.bibjson:
            self.bibjson["language"] = []
        self.bibjson["language"].append(language)
    
    def set_license(self, license_title, license_type, url=None, version=None, open_access=None, by=None, sa=None, nc=None, nd=None):
        if "license" not in self.bibjson:
            self.bibjson["license"] = []
        
        # FIXME: why is there not a "remove license" function
        if not license_title and not license_type:  # something wants to delete the license
            del self.bibjson['license']
            return
        
        lobj = {"title" : license_title, "type" : license_type}
        if url is not None:
            lobj["url"] = url
        if version is not None:
            lobj["version"] = version
        if open_access is not None:
            lobj["open_access"] = open_access
        if by is not None:
            lobj["BY"] = by
        if sa is not None:
            lobj["SA"] = sa
        if nc is not None:
            lobj["NC"] = nc
        if nd is not None:
            lobj["ND"] = nd
        
        if len(self.bibjson['license']) >= 1:
            self.bibjson["license"][0] = lobj
        else:
            self.bibjson["license"].append(lobj)
    
    def get_license(self):
        return self.bibjson.get("license", [None])[0]

    def get_license_type(self):
        lobj = self.get_license()
        if lobj:
            return lobj['type']
        return None
    
    def set_open_access(self, open_access):
        if "license" not in self.bibjson:
            self.bibjson["license"] = []
        if len(self.bibjson["license"]) == 0:
            lobj = {"open_access" : open_access}
            self.bibjson["license"].append(lobj)
        else:
            self.bibjson["license"][0]["open_access"] = open_access
    
    def set_oa_start(self, year=None, volume=None, number=None):
        """
        Volume and Number are deprecated
        """
        oaobj = {}
        if year is not None:
            oaobj["year"] = year
        """
        if volume is not None:
            oaobj["volume"] = volume
        if number is not None:
            oaobj["number"] = number
        """
        self.bibjson["oa_start"] = oaobj
    
    @property
    def oa_start(self):
        return self.bibjson.get("oa_start", {})
    
    def set_oa_end(self, year=None, volume=None, number=None):
        """
        Volume and Number are deprecated
        """
        oaobj = {}
        if year is not None:
            oaobj["year"] = year
        """
        if volume is not None:
            oaobj["volume"] = volume
        if number is not None:
            oaobj["number"] = number
        """
        self.bibjson["oa_end"] = oaobj
    
    @property
    def oa_end(self):
        return self.bibjson.get("oa_end", {})
    
    def set_apc(self, currency, average_price):
        if "apc" not in self.bibjson:
            self.bibjson["apc"] = {}
        self.bibjson["apc"]["currency"] = currency
        self.bibjson["apc"]["average_price"] = average_price
    
    @property
    def apc(self):
        return self.bibjson.get("apc") 
    
    def set_submission_charges(self, currency, average_price):
        if "submission_charges" not in self.bibjson:
            self.bibjson["submission_charges"] = {}
        self.bibjson["submission_charges"]["currency"] = currency
        self.bibjson["submission_charges"]["average_price"] = average_price
    
    @property
    def submission_charges(self):
        return self.bibjson.get("submission_charges")
    
    def set_archiving_policy(self, policies, policy_url):
        if "archiving_policy" not in self.bibjson:
            self.bibjson["archiving_policy"] = {}
        if not isinstance(policies, list):
            policies = [policies]
        self.bibjson["archiving_policy"]["policy"] = policies
        self.bibjson["archiving_policy"]["url"] = policy_url
    
    def add_archiving_policy(self, policy_name):
        if "archiving_policy" not in self.bibjson:
            self.bibjson["archiving_policy"] = {}
        self.bibjson["archiving_policy"]["policy"].append(policy_name)
    
    @property
    def archiving_policy(self): 
        return self.bibjson.get("archiving_policy")
    
    def set_editorial_review(self, process, review_url):
        if "editorial_review" not in self.bibjson:
            self.bibjson["editorial_review"] = {}
        self.bibjson["editorial_review"]["process"] = process
        self.bibjson["editorial_review"]["url"] = review_url
    
    @property
    def editorial_review(self):
        return self.bibjson.get("editorial_review") 
        
    def set_plagiarism_detection(self, url, has_detection=True):
        if "plagiarism_detection" not in self.bibjson:
            self.bibjson["plagiarism_detection"] = {}
        self.bibjson["plagiarism_detection"]["detection"] = has_detection
        self.bibjson["plagiarism_detection"]["url"] = url
    
    @property
    def plagiarism_detection(self):
        return self.bibjson.get("plagiarism_detection")
        
    def set_article_statistics(self, url, has_statistics=True):
        if "article_statistics" not in self.bibjson:
            self.bibjson["article_statistics"] = {}
        self.bibjson["article_statistics"]["statistics"] = has_statistics
        self.bibjson["article_statistics"]["url"] = url
    
    @property
    def article_statistics(self):
        return self.bibjson.get("article_statistics") 
    
    @property
    def deposit_policy(self):
        return self.bibjson.get("deposit_policy")
    
    @deposit_policy.setter
    def deposit_policy(self, policies):
        if not isinstance(policies, list):
            policies = [policies]
        self.bibjson["deposit_policy"] = policies
    
    def add_deposit_policy(self, policy):
        if "deposit_policy" not in self.bibjson:
            self.bibjson["deposit_policy"] = []
        self.bibjson["deposit_policy"].append(policy)
    
    def set_author_copyright(self, url, holds_copyright=True):
        if "author_copyright" not in self.bibjson:
            self.bibjson["author_copyright"] = {}
        self.bibjson["author_copyright"]["copyright"] = holds_copyright
        self.bibjson["author_copyright"]["url"] = url
    
    @property
    def author_copyright(self):
        return self.bibjson.get("author_copyright") 
    
    def set_author_publishing_rights(self, url, holds_rights=True):
        if "author_publishing_rights" not in self.bibjson:
            self.bibjson["author_publishing_rights"] = {}
        self.bibjson["author_publishing_rights"]["publishing_rights"] = holds_rights
        self.bibjson["author_publishing_rights"]["url"] = url
    
    @property
    def author_publishing_rights(self):
        return self.bibjson.get("author_publishing_rights")
    
    @property
    def allows_fulltext_indexing(self): return self.bibjson.get("allows_fulltext_indexing", False)
    @allows_fulltext_indexing.setter
    def allows_fulltext_indexing(self, allows): self.bibjson["allows_fulltext_indexing"] = allows
    
    @property
    def persistent_identifier_scheme(self):
        return self.bibjson.get("persistent_identifier_scheme", [])
        
    @persistent_identifier_scheme.setter
    def persistent_identifier_scheme(self, schemes):
        if not isinstance(schemes, list):
            schemes = [schemes]
        self.bibjson["persistent_identifier_scheme"] = schemes
    
    def add_persistent_identifier_scheme(self, scheme):
        if "persistent_identifier_scheme" not in self.bibjson:
            self.bibjson["persistent_identifier_scheme"] = []
        self.bibjson["persistent_identifier_scheme"].append(scheme)

    @property
    def format(self):
        return self.bibjson.get("format", [])
        
    @format.setter
    def format(self, form):
        if not isinstance(form, list):
            form = [form]
        self.bibjson["format"] = form
    
    def add_format(self, form):
        if "format" not in self.bibjson:
            self.bibjson["format"] = []
        self.bibjson["format"].append(form)
    
    @property
    def publication_time(self): return self.bibjson.get("publication_time")
    @publication_time.setter
    def publication_time(self, weeks): self.bibjson["publication_time"] = weeks
    
class JournalQuery(object):
    """
    wrapper around the kinds of queries we want to do against the journal type
    """
    issn_query = {
        "query": {
        	"bool": {
            	"must": [
                	{
                    	"term" :  { "index.issn.exact" : "<issn>" }
                    }
                ]
            }
        }
    }
    
    all_doaj = {
	    "query" : {
        	"bool" : {
            	"must" : [
            	    {"term" : {"admin.in_doaj" : True}}
            	]
            }
        }
    }
    
    def __init__(self):
        self.query = None
    
    def find_by_issn(self, issn):
        self.query = deepcopy(self.issn_query)
        self.query["query"]["bool"]["must"][0]["term"]["index.issn.exact"] = issn
        
    def all_in_doaj(self):
        return deepcopy(self.all_doaj)

class IssnQuery(object):
    base_query = {
        "query" : {
            "term" : { "admin.owner.exact" : "<owner id here>" }
        },
        "size" : 0,
        "facets" : {
            "issns" : {
                "terms" : {
                    "field" : "index.issn.exact",
                    "size" : 10000,
                    "order" : "term"
                }
            }
        }
    }
    
    def __init__(self, owner):
        self._query = deepcopy(self.base_query)
        self._query["query"]["term"]["admin.owner.exact"] = owner
    
    def query(self):
        return self._query

class PublisherQuery(object):
    exact_query = {
        "query" : {
            "term" : {"index.publisher.exact" : "<publisher name here>"}
        },
        "size": 10000
    }
    
    inexact_query = {
        "query" : {
            "term" : {"index.publisher" : "<publisher name here>"}
        },
        "size": 10000
    }

    def __init__(self, publisher, exact=True):
        self.publisher = publisher
        self.exact = exact
    
    def query(self):
        q = None
        if self.exact:
            q = deepcopy(self.exact_query)
            q["query"]["term"]["index.publisher.exact"] = self.publisher
        else:
            q = deepcopy(self.inexact_query)
            q["query"]["term"]["index.publisher"] = self.publisher.lower()
        return q

class TitleQuery(object):
    base_query = {
        "query" : {
            "term" : {"index.title.exact" : "<title here>"}
        },
        "size": 10000
    }
    
    def __init__(self, title):
        self.title = title
    
    def query(self):
        q = deepcopy(self.base_query)
        q["query"]["term"]["index.title.exact"] = self.title
        return q

############################################################################

############################################################################
## Suggestion object and related classes
############################################################################

class Suggestion(Journal):
    __type__ = "suggestion"
    
    def _set_suggestion_property(self, name, value):
        if "suggestion" not in self.data:
            self.data["suggestion"] = {}
        self.data["suggestion"][name] = value

    ### suggestion properties (as in, the Suggestion model's "suggestion" object ###

    @property
    def suggested_by_owner(self):
        """
        Deprecated - DO NOT USE
        """
        return self.data.get("suggestion", {}).get("suggested_by_owner")
    
    @suggested_by_owner.setter
    def suggested_by_owner(self, val): 
        """
        Deprecated - DO NOT USE
        """
        self._set_suggestion_property("suggested_by_owner", val)

    @property
    def suggested_on(self): return self.data.get("suggestion", {}).get("suggested_on")
    @suggested_on.setter
    def suggested_on(self, val): self._set_suggestion_property("suggested_on", val)
    
    @property
    def articles_last_year(self):
        return self.data.get("suggestion", {}).get("articles_last_year")
    
    def set_articles_last_year(self, count, url):
        if "suggestion" not in self.data:
            self.data["suggestion"] = {}
        if "articles_last_year" not in self.data["suggestion"]:
            self.data["suggestion"]["articles_last_year"] = {}
        self.data["suggestion"]["articles_last_year"]["count"] = count
        self.data["suggestion"]["articles_last_year"]["url"] = url
    
    @property
    def article_metadata(self): return self.data.get("suggestion", {}).get("article_metadata")
    @article_metadata.setter
    def article_metadata(self, val): self._set_suggestion_property("article_metadata", val)
    
    @property
    def description(self): 
        """
        Deprecated - DO NOT USE
        """
        return self.data.get("suggestion", {}).get("description")
    
    @description.setter
    def description(self, val): 
        """
        Deprecated - DO NOT USE
        """
        self._set_suggestion_property("description", val)
    
    @property
    def suggester(self): return self.data.get("suggestion", {}).get("suggester", {})
    def set_suggester(self, name, email):
        self._set_suggestion_property("suggester", {"name" : name, "email" : email})

############################################################################

####################################################################
# Article and related classes
####################################################################

class Article(DomainObject):
    __type__ = "article"
    
    @classmethod
    def duplicates(cls, issns=None, publisher_record_id=None, doi=None, fulltexts=None, title=None, volume=None, number=None, start=None, should_match=None):
        # some input sanitisation
        issns = issns if isinstance(issns, list) else []
        urls = fulltexts if isinstance(fulltexts, list) else [fulltexts] if isinstance(fulltexts, str) or isinstance(fulltexts, unicode) else []
        
        q = DuplicateArticleQuery(issns=issns, 
                                    publisher_record_id=publisher_record_id, 
                                    doi=doi, 
                                    urls=urls,
                                    title=title,
                                    volume=volume,
                                    number=number,
                                    start=start,
                                    should_match=should_match)
        # print json.dumps(q.query())
        
        res = cls.query(q=q.query())
        articles = [cls(**hit.get("_source")) for hit in res.get("hits", {}).get("hits", [])]
        return articles
    
    def bibjson(self):
        if "bibjson" not in self.data:
            self.data["bibjson"] = {}
        return ArticleBibJSON(self.data.get("bibjson"))

    def set_bibjson(self, bibjson):
        bibjson = bibjson.bibjson if isinstance(bibjson, ArticleBibJSON) else bibjson
        self.data["bibjson"] = bibjson
    
    def history(self):
        hs = self.data.get("history", [])
        tuples = []
        for h in hs:
            tuples.append((h.get("date"), ArticleBibJSON(h.get("bibjson"))))
        return tuples
    
    def snapshot(self):
        snap = deepcopy(self.data.get("bibjson"))
        self.add_history(snap)
    
    def add_history(self, bibjson, date=None):
        bibjson = bibjson.bibjson if isinstance(bibjson, ArticleBibJSON) else bibjson
        if date is None:
            date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        snobj = {"date" : date, "bibjson" : bibjson}
        if "history" not in self.data:
            self.data["history"] = []
        self.data["history"].append(snobj)
    
    def is_in_doaj(self):
        return self.data.get("admin", {}).get("in_doaj", False)
    
    def set_in_doaj(self, value):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["in_doaj"] = value
    
    def publisher_record_id(self):
        return self.data.get("admin", {}).get("publisher_record_id")
    
    def set_publisher_record_id(self, pri):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["publisher_record_id"] = pri
    
    def upload_id(self):
        return self.data.get("admin", {}).get("upload_id")
    
    def set_upload_id(self, uid):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["upload_id"] = uid
    
    def merge(self, old):
        # this takes an old version of the article and brings
        # forward any useful information that is needed.  The rules of merge are:
        # - ignore "index" (it gets regenerated on save)
        # - always take the "created_date"
        # - any top level field that does not exist in the current item (esp "id" and "history")
        # - in "admin", copy any field that does not already exist
        
        # always take the created date
        self.set_created(old.created_date)
        
        # take the id
        if self.id is None:
            self.set_id(old.id)
        
        # take the history
        if len(self.data.get("history", [])) == 0:
            self.data["history"] = deepcopy(old.data.get("history", []))
        
        # take the bibjson
        if "bibjson" not in self.data:
            self.set_bibjson(deepcopy(old.bibjson()))
        
        # take the admin if there isn't one
        if "admin" not in self.data:
            self.data["admin"] = deepcopy(old.data.get("admin", {}))
        else:
            # otherwise, copy any admin keys that don't exist on the current item
            oa = old.data.get("admin", {})
            for key in oa:
                if key not in self.data["admin"]:
                    self.data["admin"][key] = deepcopy(oa[key])
        
    def _generate_index(self):
        # the index fields we are going to generate
        issns = []
        subjects = []
        schema_subjects = []
        schema_codes = []
        classification = []
        langs = []
        country = None
        license = []
        publisher = []
        
        # the places we're going to get those fields from
        cbib = self.bibjson()
        jindex = self.data.get('index', {})
        hist = self.history()
        
        # get the issns out of the current bibjson
        issns += cbib.get_identifiers(cbib.P_ISSN)
        issns += cbib.get_identifiers(cbib.E_ISSN)
        
        # now get the issns out of the historic records
        for date, hbib in hist:
            issns += hbib.get_identifiers(hbib.P_ISSN)
            issns += hbib.get_identifiers(hbib.E_ISSN)
        
        # get the subjects and concatenate them with their schemes from the current bibjson
        for subs in cbib.subjects():
            scheme = subs.get("scheme")
            term = subs.get("term")
            subjects.append(term)
            schema_subjects.append(scheme + ":" + term)
            classification.append(term)
            if "code" in subs:
                schema_codes.append(scheme + ":" + subs.get("code"))
        
        # copy the languages
        if cbib.journal_language is not None:
            langs = cbib.journal_language
        
        # copy the country
        if jindex.get('country'):
            country = jindex.get('country')
        elif cbib.journal_country:
            country = xwalk.get_country_name(cbib.journal_country)
        
        # get the title of the license
        lic = cbib.get_journal_license()
        if lic is not None:
            license.append(lic.get("title"))
        
        # copy the publisher/provider
        if cbib.publisher:
            publisher.append(cbib.publisher)
        
        # deduplicate the list
        issns = list(set(issns))
        subjects = list(set(subjects))
        schema_subjects = list(set(schema_subjects))
        classification = list(set(classification))
        license = list(set(license))
        publisher = list(set(publisher))
        langs = list(set(langs))
        schema_codes = list(set(schema_codes))
        
        # work out what the date of publication is
        date = cbib.get_publication_date()
        
        # build the index part of the object
        self.data["index"] = {}
        if len(issns) > 0:
            self.data["index"]["issn"] = issns
        if date != "":
            self.data["index"]["date"] = date
        if len(subjects) > 0:
            self.data["index"]["subject"] = subjects
        if len(schema_subjects) > 0:
            self.data["index"]["schema_subject"] = schema_subjects
        if len(classification) > 0:
            self.data["index"]["classification"] = classification
        if len(publisher) > 0:
            self.data["index"]["publisher"] = publisher
        if len(license) > 0:
            self.data["index"]["license"] = license
        if len(langs) > 0:
            self.data["index"]["language"] = langs
        if country is not None:
            self.data["index"]["country"] = country
        if schema_codes > 0:
            self.data["index"]["schema_code"] = schema_codes
    
    def prep(self):
        self._generate_index()
        self.data['last_updated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def save(self):
        self._generate_index()
        super(Article, self).save()
    
class ArticleBibJSON(GenericBibJSON):
    
    # article-specific simple getters and setters
    @property
    def year(self): return self.bibjson.get("year")
    @year.setter
    def year(self, val) : self.bibjson["year"] = str(val)
    
    @property
    def month(self): return self.bibjson.get("month")
    @month.setter
    def month(self, val) : self.bibjson["month"] = str(val)
    
    @property
    def start_page(self): return self.bibjson.get("start_page")
    @start_page.setter
    def start_page(self, val) : self.bibjson["start_page"] = val
    
    @property
    def end_page(self): return self.bibjson.get("end_page")
    @end_page.setter
    def end_page(self, val) : self.bibjson["end_page"] = val
    
    @property
    def abstract(self): return self.bibjson.get("abstract")
    @abstract.setter
    def abstract(self, val) : self.bibjson["abstract"] = val
    
    # article-specific complex part getters and setters
    
    def _set_journal_property(self, prop, value):
        if "journal" not in self.bibjson:
            self.bibjson["journal"] = {}
        self.bibjson["journal"][prop] = value
    
    @property
    def volume(self):
        return self.bibjson.get("journal", {}).get("volume")
    
    @volume.setter
    def volume(self, value):
        self._set_journal_property("volume", value)
    
    @property
    def number(self):
        return self.bibjson.get("journal", {}).get("number")
    
    @number.setter
    def number(self, value):
        self._set_journal_property("number", value)
    
    @property
    def journal_title(self):
        return self.bibjson.get("journal", {}).get("title")
    
    @journal_title.setter
    def journal_title(self, title):
        self._set_journal_property("title", title)
    
    @property
    def journal_language(self):
        return self.bibjson.get("journal", {}).get("language")
    
    @journal_language.setter
    def journal_language(self, lang):
        self._set_journal_property("language", lang)
    
    # beware, the index part of an article will contain the same as the
    # index part of a journal, not the same as the bibjson part of a
    # journal!
    # the method below is referring to the bibjson part of a journal
    @property
    def journal_country(self):
        return self.bibjson.get("journal", {}).get("country")
    
    @journal_country.setter
    def journal_country(self, country):
        self._set_journal_property("country", country)
    
    @property
    def publisher(self):
        return self.bibjson.get("journal", {}).get("publisher")
    
    @publisher.setter
    def publisher(self, value):
        self._set_journal_property("publisher", value)
        
    def add_author(self, name, email=None, affiliation=None):
        if "author" not in self.bibjson:
            self.bibjson["author"] = []
        aobj = {"name" : name}
        if email is not None:
            aobj["email"] = email
        if affiliation is not None:
            aobj["affiliation"] = affiliation
        self.bibjson["author"].append(aobj)
    
    @property
    def author(self):
        return self.bibjson.get("author", [])
    
    def set_journal_license(self, licence_title, licence_type, url=None, version=None, open_access=None):
        lobj = {"title" : licence_title, "type" : licence_type}
        if url is not None:
            lobj["url"] = url
        if version is not None:
            lobj["version"] = version
        if open_access is not None:
            lobj["open_access"] = open_access
        
        self._set_journal_property("license", [lobj])
    
    def get_journal_license(self):
        return self.bibjson.get("journal", {}).get("license", [None])[0]
    
    def get_publication_date(self):
        # work out what the date of publication is
        date = ""
        if self.year is not None:
            # fix 2 digit years
            if len(self.year) == 2:
                if int(self.year) <=13:
                    self.year = "20" + self.year
                else:
                    self.year = "19" + self.year
                    
            # if we still don't have a 4 digit year, forget it
            if len(self.year) != 4:
                return date
            
            # build up our proposed datestamp
            date += str(self.year)
            if self.month is not None:
                try:
                    if len(self.month) == 1:
                        date += "-0" + str(self.month)
                    else:
                        date += "-" + str(self.month)
                except:
                    # FIXME: months are in all sorts of forms, we can only handle 
                    # numeric ones right now
                    date += "-01" 
            else:
                date += "-01"
            date += "-01T00:00:00Z"
            
            # attempt to confirm the format of our datestamp
            try:
                datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
            except:
                return ""
        return date

class DuplicateArticleQuery(object):
    base_query = {
        "query" : {
            "bool" : {
                "must" : []
            }
        }
    }
    
    _should = {
        "should" : [],
        "minimum_should_match" : 2
    }
    
    _volume_term = {"term" : {"bibjson.journal.volume.exact" : "<volume>"}}
    _number_term = {"term" : {"bibjson.journal.number.exact" : "<issue number>"}}
    _start_term = {"term" : {"bibjson.start_page.exact" : "<start page>"}}
    _issn_terms = {"terms" : { "index.issn.exact" : ["<list of issns>"] }}
    _pubrec_term = {"term" : {"admin.publisher_record_id.exact" : "<publisher record id>"}}
    _identifier_term = {"term" : {"bibjson.identifier.id.exact" : "<doi or issn here>"}}
    _url_terms = {"terms" : {"bibjson.link.url.exact" : ["<urls here>"]}}
    _fuzzy_title = {"fuzzy" : {"bibjson.title.exact" : "<title here>"}}

    def __init__(self, issns=None, publisher_record_id=None, doi=None, urls=None, title=None, volume=None, number=None, start=None, should_match=None):
        self.issns = issns if isinstance(issns, list) else []
        self.publisher_record_id = publisher_record_id
        self.doi = doi
        self.urls = urls if isinstance(urls, list) else [urls] if isinstance(urls, str) or isinstance(urls, unicode) else []
        self.title = title
        self.volume = volume
        self.number = number
        self.start = start
        self.should_match = should_match
    
    def query(self):
        # - MUST be from at least one of the ISSNs
        # - MUST have the publisher record id
        # - MUST have the doi unless should_match is set
        # - MUST have the one of the fulltext urls unless should_match is set
        # - MUST fuzzy match the title
        # - SHOULD have <should_match> of: volume, issue, start page, fulltext url, doi
        
        q = deepcopy(self.base_query)
        if len(self.issns) > 0:
            it = deepcopy(self._issn_terms)
            it["terms"]["index.issn.exact"] = self.issns
            q["query"]["bool"]["must"].append(it)
        
        if self.publisher_record_id is not None:
            pr = deepcopy(self._pubrec_term)
            pr["term"]["admin.publisher_record_id.exact"] = self.publisher_record_id
            q["query"]["bool"]["must"].append(pr)
        
        if self.doi is not None and self.should_match is None:
            idt = deepcopy(self._identifier_term)
            idt["term"]["bibjson.identifier.id.exact"] = self.doi
            q["query"]["bool"]["must"].append(idt)
        
        if len(self.urls) > 0 and self.should_match is None:
            uq = deepcopy(self._url_terms)
            uq["terms"]["bibjson.link.url.exact"] = self.urls
            q["query"]["bool"]["must"].append(uq)
        
        if self.title is not None:
            ft = deepcopy(self._fuzzy_title)
            ft["fuzzy"]["bibjson.title.exact"] = self.title
            q["query"]["bool"]["must"].append(ft)
        
        if self.should_match is not None:
            term_count = 0
            s = deepcopy(self._should)
            
            if self.volume is not None:
                term_count += 1
                vt = deepcopy(self._volume_term)
                vt["term"]["bibjson.journal.volume.exact"] = self.volume
                s["should"].append(vt)
            
            if self.number is not None:
                term_count += 1
                nt = deepcopy(self._number_term)
                nt["term"]["bibjson.journal.number.exact"] = self.number
                s["should"].append(nt)
                
            if self.start is not None:
                term_count += 1
                st = deepcopy(self._start_term)
                st["term"]["bibjson.start_page.exact"] = self.start
                s["should"].append(st)
            
            if len(self.urls) > 0:
                term_count += 1
                uq = deepcopy(self._url_terms)
                uq["terms"]["bibjson.link.url.exact"] = self.urls
                s["should"].append(uq)
            
            if self.doi is not None:
                term_count += 1
                idt = deepcopy(self._identifier_term)
                idt["term"]["bibjson.identifier.id.exact"] = self.doi
                s["should"].append(idt)
            
            msm = self.should_match
            if msm > term_count:
                msm = term_count    
            s["minimum_should_match"] = msm
            
            q["query"]["bool"].update(s)
            
        return q
            
    

####################################################################

####################################################################
## OAI-PMH Record Objects
####################################################################

class OAIPMHRecord(object):
    earliest = {
	        "query" : {
            	"bool" : {
                	"must" : [
                	    {"term" : {"admin.in_doaj" : True}}
                	]
                }
            },
            "size" : 0,
            "facets" : {
            	"earliest" : {
                	"terms" : {
                    	"field" : "last_updated",
                        "order" : "term"
                    }
                }
            }
        }
    
    sets = {
	    "query" : {
        	"bool" : {
            	"must" : [
            	    {"term" : {"admin.in_doaj" : True}}
            	]
            }
        },
        "size" : 0,
        "facets" : {
        	"sets" : {
            	"terms" : {
                	"field" : "index.schema_subject.exact",
                    "order" : "term",
                    "size" : 100000
                }
            }
        }
    }
    
    records = {
	    "query" : {
        	"bool" : {
            	"must" : [
            	    {"term" : {"admin.in_doaj" : True}}
            	]
            }
        },
        "from" : 0,
        "size" : 25
    }
    
    set_limit = {"term" : { "index.schema_subject.exact" : "<set name>" }}
    range_limit = { "range" : { "last_updated" : {"gte" : "<from date>", "lte" : "<until date>"} } }
    created_sort = {"last_updated" : {"order" : "desc"}}
    
    def earliest_datestamp(self):
        result = self.query(q=self.earliest)
        dates = [t.get("term") for t in result.get("facets", {}).get("earliest", {}).get("terms", [])]
        for d in dates:
            if d > 0:
                return datetime.fromtimestamp(d / 1000.0).strftime("%Y-%m-%dT%H:%M:%SZ")
        return None
    
    def identifier_exists(self, identifier):
        obj = self.pull(identifier)
        return obj is not None
    
    def list_sets(self):
        result = self.query(q=self.sets)
        sets = [t.get("term") for t in result.get("facets", {}).get("sets", {}).get("terms", [])]
        return sets
    
    def list_records(self, from_date=None, until_date=None, oai_set=None, list_size=None, start_number=None):
        q = deepcopy(self.records)
        if from_date is not None or until_date is not None or oai_set is not None:
            
            if oai_set is not None:
                s = deepcopy(self.set_limit)
                s["term"]["index.schema_subject.exact"] = oai_set
                q["query"]["bool"]["must"].append(s)
            
            if until_date is not None or from_date is not None:
                d = deepcopy(self.range_limit)
                
                if until_date is not None:
                    d["range"]["last_updated"]["lte"] = until_date
                else:
                    del d["range"]["last_updated"]["lte"]
                
                if from_date is not None:
                    d["range"]["last_updated"]["gte"] = from_date
                else:
                    del d["range"]["last_updated"]["gte"]
                
                q["query"]["bool"]["must"].append(d)
        
        if list_size is not None:
            q["size"] = list_size
            
        if start_number is not None:
            q["from"] = start_number
        
        q["sort"] = [deepcopy(self.created_sort)]
        
        # do the query
        # print json.dumps(q)
        results = self.query(q=q)
        
        total = results.get("hits", {}).get("total", 0)
        return total, [hit.get("_source") for hit in results.get("hits", {}).get("hits", [])]
        

class OAIPMHArticle(OAIPMHRecord, Article):
    def list_records(self, from_date=None, until_date=None, oai_set=None, list_size=None, start_number=None):
        total, results = super(OAIPMHArticle, self).list_records(from_date=from_date, 
            until_date=until_date, oai_set=oai_set, list_size=list_size, start_number=start_number)
        return total, [Article(**r) for r in results]
    
    def pull(self, identifier):
        # override the default pull, as we care about whether the item is in_doaj
        record = super(OAIPMHArticle, self).pull(identifier)
        if record.is_in_doaj():
            return record
        return None

class OAIPMHJournal(OAIPMHRecord, Journal):
    def list_records(self, from_date=None, until_date=None, oai_set=None, list_size=None, start_number=None):
        total, results = super(OAIPMHJournal, self).list_records(from_date=from_date, 
            until_date=until_date, oai_set=oai_set, list_size=list_size, start_number=start_number)
        return total, [Journal(**r) for r in results]
    
    def pull(self, identifier):
        # override the default pull, as we care about whether the item is in_doaj
        record = super(OAIPMHJournal, self).pull(identifier)
        if record.is_in_doaj():
            return record
        return None

####################################################################

####################################################################
## Atom Record Object
####################################################################

class AtomRecord(Journal):
    records = {
	    "query" : {
        	"bool" : {
            	"must" : [
            	    {"term" : {"admin.in_doaj" : True}},
            	    { "range" : { "last_updated" : {"gte" : "<from date>"} } }
            	]
            }
        },
        "size" : 20,
        "sort" : {"last_updated" : {"order" : "desc"}}
    }
    
    def list_records(self, from_date, list_size):
        q = deepcopy(self.records)
        q["query"]["bool"]["must"][1]["range"]["last_updated"]["gte"] = from_date
        q["size"] = list_size
        
        # do the query
        # print json.dumps(q)
        results = self.query(q=q)
        
        return [AtomRecord(**hit.get("_source")) for hit in results.get("hits", {}).get("hits", [])]

#######################################################################

#######################################################################
## Classes for working across both Journals and Articles
#######################################################################

class JournalArticle(DomainObject):
    __type__ = 'journal,article'
    __readonly__ = True  # TODO actually heed this attribute in all DomainObject methods which modify data
    
    @classmethod
    def site_statistics(cls):
        # first check the cache
        stats = Cache.get_site_statistics()
        if stats is not None:
            return stats
        
        # we didn't get anything from the cache, so we need to generate and
        # cache a new set
        
        # prep the query and result objects
        q = JournalArticleQuery()
        stats = {
            "articles" : 0,
            "journals" : 0,
            "countries" : 0,
            "searchable" : 0
        }
        
        # do the query
        res = cls.query(q=q.site_statistics())
        
        # pull the journal and article facets out
        terms = res.get("facets", {}).get("type", {}).get("terms", [])

        # can't use the Python , option when formatting numbers since we
        # need to be compatible with Python 2.6
        # otherwise we would be able to do "{0:,}".format(t.get("count", 0))

        if sys.version_info[0] == 2 and sys.version_info[1] < 7:
            locale.setlocale(locale.LC_ALL, 'en_US')
            for t in terms:
                if t.get("term") == "journal":
                    stats["journals"] = locale.format("%d", t.get("count", 0), grouping=True)
                if t.get("term") == "article":
                    stats["articles"] = locale.format("%d", t.get("count", 0), grouping=True)
            
            # count the size of the countries facet
            stats["countries"] = locale.format("%d", len(res.get("facets", {}).get("countries", {}).get("terms", [])), grouping=True)
            
            # count the size of the journals facet (which tells us how many journals have articles)
            stats["searchable"] = locale.format("%d", len(res.get("facets", {}).get("journals", {}).get("terms", [])), grouping=True)
            
            locale.resetlocale()
        else:
            for t in terms:
                if t.get("term") == "journal":
                    stats["journals"] = "{0:,}".format(t.get("count", 0))
                if t.get("term") == "article":
                    stats["articles"] = "{0:,}".format(t.get("count", 0))
            
            # count the size of the countries facet
            stats["countries"] = "{0:,}".format(len(res.get("facets", {}).get("countries", {}).get("terms", [])))
            
            # count the size of the journals facet (which tells us how many journals have articles)
            stats["searchable"] = "{0:,}".format(len(res.get("facets", {}).get("journals", {}).get("terms", [])))

        # now cache and return
        Cache.cache_site_statistics(stats)
        
        return stats
        

class JournalArticleQuery(object):
    stats = {
	    "query":{
        	"bool" : {
            	"must" : [
                	{"term" : {"admin.in_doaj" : True}}
                ]
            }
	    },
        "size" : 0,
        "facets" : {
        	"type" : {
            	"terms" : {"field" : "_type"} 
            },
            "countries" : {
			    "terms" : {"field" : "index.country.exact", "size" : 10000 }
		    },
            "journals" : {
            	"terms" : {"field" : "bibjson.journal.title.exact", "size" : 15000 }
            }
        }
    }
    
    def site_statistics(self):
        return deepcopy(self.stats)


########################################################################

class Cache(DomainObject):
    __type__ = "cache"
    
    @classmethod
    def get_site_statistics(cls):
        rec = cls.pull("site_statistics")
        
        """
        returnable = rec is not None
        if rec is not None:
            marked_regen = rec.marked_regen()
            if not marked_regen:
                stale = rec.is_stale()
                if stale:
                    rec.mark_for_regen()
                else:
                    returnable = True
            else:
                returnable = True
        """
        returnable = rec is not None
        if rec is not None:
            if rec.is_stale():
                returnable = False
        
        # if the cache exists and is in date (or is otherwise returnable), then explicilty build the
        # cache object and return it
        if returnable:
            return {
                "articles" : rec.data.get("articles"),
                "journals" : rec.data.get("journals"),
                "countries" : rec.data.get("countries"),
                "searchable" : rec.data.get("searchable")
            }
        
        # if we get to here, then we don't return the cache
        return None
    
    @classmethod
    def cache_site_statistics(cls, stats):
        cobj = cls(**stats)
        cobj.set_id("site_statistics")
        cobj.save()
    
    def mark_for_regen(self):
        self.update({"regen" : True})
    
    def is_stale(self):
        lu = datetime.strptime(self.last_updated, "%Y-%m-%dT%H:%M:%SZ")
        now = datetime.now()
        dt = now - lu

        # compatibility with Python 2.6
        if hasattr(dt, 'total_seconds'):
            total_seconds = dt.total_seconds()
        else:
            total_seconds = (dt.microseconds + (dt.seconds + dt.days * 24 * 3600) * 10**6) / 10**6

        return total_seconds > app.config.get("SITE_STATISTICS_TIMEOUT")
    
    def marked_regen(self):
        return self.data.get("regen", False)
        








































