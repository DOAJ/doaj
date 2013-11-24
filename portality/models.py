from datetime import datetime
from copy import deepcopy

from portality.core import app
from portality.dao import DomainObject as DomainObject


# The default Portality account object.  We don't need this yet, but we will soon
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

class Account(DomainObject, UserMixin):
    __type__ = 'account'

    @classmethod
    def pull_by_email(cls,email):
        res = cls.query(q='email:"' + email + '"')
        if res.get('hits',{}).get('total',0) == 1:
            return cls(**res['hits']['hits'][0]['_source'])
        else:
            return None

    def set_password(self, password):
        self.data['password'] = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.data['password'], password)

    @property
    def is_super(self):
        return not self.is_anonymous() and self.id in app.config['SUPER_USER']

# NOTE: DomainObject interferes with new style @property getter/setter
# so we can't use them here
class Journal(DomainObject):
    __type__ = "journal"
    CSV_HEADER = ["Title","Title Alternative","Identifier","Publisher","Language","ISSN","EISSN","Keyword","Start Year","End Year","Added on date","Subjects","Country","Publication fee","Further Information","CC License","Content in DOAJ"]
    
    def bibjson(self):
        if "bibjson" not in self.data:
            self.data["bibjson"] = {}
        return BibJSON(self.data.get("bibjson"))

    def set_bibjson(self, bibjson):
        bibjson = bibjson.bibjson if isinstance(bibjson, BibJSON) else bibjson
        self.data["bibjson"] = bibjson
    
    def history(self):
        hs = self.data.get("history", [])
        tuples = []
        for h in hs:
            tuples.append((h.get("date"), BibJSON(h.get("bibjson"))))
        return tuples
    
    def snapshot(self):
        snap = deepcopy(self.data.get("bibjson"))
        self.add_history(snap)
    
    def add_history(self, bibjson, date=None):
        bibjson = bibjson.bibjson if isinstance(bibjson, BibJSON) else bibjson
        if date is None:
            date = datetime.now().isoformat()
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
    
    def application_status(self):
        return self.data.get("admin", {}).get("application_status")
    
    def set_application_status(self, value):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["application_status"] = value
    
    def contact_email(self):
        return self.data.get("admin", {}).get("contact_email")
    
    def set_contact_email(self, value):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["contact_email"] = value
    
    def contact_name(self):
        return self.data.get("admin", {}).get("contact_name")
    
    def set_contact_name(self, value):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["contact_name"] = value
    
    def add_note(self, note, date=None):
        if date is None:
            date = datetime.now().isoformat()
        if "admin" not in self.data:
            self.data["admin"] = {}
        if "notes" not in self.data.get("admin"):
            self.data["admin"]["notes"] = []
        self.data["admin"]["notes"].append({"date" : date, "note" : note})
    
    def add_correspondence(self, message, date=None):
        if date is None:
            date = datetime.now().isoformat()
        if "admin" not in self.data:
            self.data["admin"] = {}
        if "owner_correspondence" not in self.data.get("admin"):
            self.data["admin"]["owner_correspondence"] = []
        self.data["admin"]["owner_correspondence"].append({"date" : date, "note" : message})
    
    def _generate_index(self):
        # the index fields we are going to generate
        issns = []
        titles = []
        
        # the places we're going to get those fields from
        cbib = self.bibjson()
        hist = self.history()
        
        # get the issns out of the current bibjson
        issns += cbib.get_identifiers(cbib.P_ISSN)
        issns += cbib.get_identifiers(cbib.E_ISSN)
        
        # get the title out of the current bibjson
        titles.append(cbib.title)
        
        # now get the issns and titles out of the historic records
        for date, hbib in hist:
            issns += hbib.get_identifiers(hbib.P_ISSN)
            issns += hbib.get_identifiers(hbib.E_ISSN)
            titles.append(hbib.title)
        
        # deduplicate the lists
        issns = list(set(issns))
        titles = list(set(titles))
        
        # build the index part of the object
        self.data["index"] = {}
        if len(issns) > 0:
            self.data["index"]["issn"] = issns
        if len(titles) > 0:
            self.data["index"]["title"] = titles
    
    def save(self):
        self._generate_index()
        super(Journal, self).save()

    def csv(self, multival_sep=','):
        YES_NO = {True: 'Yes', False: 'No', None: '', '': ''}
        row = []
        c = self.data['bibjson']
        row.append(c.get('title', ''))
        row.append('') # in place of Title Alternative
        row.append( multival_sep.join(c.get('link', '')) )
        row.append(c.get('publisher', ''))
        row.append(c.get('language', ''))

        # we're following the old CSV format strictly for now, so only 1
        # ISSN allowed - below is the code for handling multiple ones

        # ISSN taken from Print ISSN
        # row.append( multival_sep.join([id_['id'] for id_ in c['identifier'] if id_['type'] == 'pissn']) )
        pissns = [id_['id'] for id_ in c.get('identifier', []) if id_['type'] == 'pissn']
        row.append(pissns[0] if len(pissns) > 0 else '') # just the 1st one

        # EISSN - the same as ISSN applies
        # row.append( multival_sep.join([id_['id'] for id_ in c['identifier'] if id_['type'] == 'eissn']) )
        eissns = [id_['id'] for id_ in c.get('identifier', []) if id_['type'] == 'eissn']
        row.append(eissns[0] if len(eissns) > 0 else '') # just the 1st one

        row.append( multival_sep.join(c.get('keywords', '')) )
        row.append(c.get('oa_start', {}).get('year'))
        row.append(c.get('oa_end', {}).get('year'))
        row.append(self.data.get('created_date', ''))
        row.append( multival_sep.join([subject['term'] for subject in c.get('subject', [])]) )
        row.append(c.get('country', ''))
        row.append(YES_NO[c.get('author_pays', '')])
        row.append(c.get('author_pays_url', ''))

        # for now, follow the strange format of the CC License column
        # that the old CSV had. Also, only take the first CC license we see!
        cc_licenses = [lic['type'][3:] for lic in c.get('license', []) if lic['type'].startswith('cc-')]
        row.append(cc_licenses[0] if len(cc_licenses) > 0 else '')
        
        row.append(YES_NO[c.get('active')])
        return row

class Suggestion(Journal):
    __type__ = "suggestion"
    
    def _set_suggestion_property(self, name, value):
        if "suggestion" not in self.data:
            self.data["suggestion"] = {}
        self.data["suggestion"][name] = value
    
    def description(self): return self.data.get("suggestion", {}).get("description")
    
    def set_description(self, value): self._set_suggestion_property("description", value)
    
    def suggester_name(self): return self.data.get("suggestion", {}).get("suggester_name")
    
    def set_suggester_name(self, value): self._set_suggestion_property("suggester_name", value)
    
    def suggester_email(self): return self.data.get("suggestion", {}).get("suggester_email")
    
    def set_suggester_email(self, value): self._set_suggestion_property("suggester_email", value)
    
    def suggested_by_owner(self): return self.data.get("suggestion", {}).get("suggested_by_owner")
    
    def set_suggested_by_owner(self, value): self._set_suggestion_property("suggested_by_owner", value)
    
    def suggested_on(self): return self.data.get("suggestion", {}).get("suggested_on")
    
    def set_suggested_on(self, value): self._set_suggestion_property("suggested_on", value)
        

class BibJSON(object):
    
    # vocab of known identifier types
    P_ISSN = "pissn"
    E_ISSN = "eissn"
    
    # constructor
    def __init__(self, bibjson={}):
        self.bibjson = bibjson
    
    # generic property getter and setter for ad-hoc extensions
    def get_property(self, prop):
        return self.bibjson.get(prop)
    
    def set_property(self, prop, value):
        self.bibjson[prop] = value
    
    # simple property getter and setters
    
    @property
    def title(self): return self.bibjson.get("title")
    @title.setter
    def title(self, val) : self.bibjson["title"] = val
    
    @property
    def language(self): return self.bibjson.get("language")
    @language.setter
    def language(self, val) : self.bibjson["language"] = val
    
    @property
    def author_pays_url(self): return self.bibjson.get("author_pays_url")
    @author_pays_url.setter
    def author_pays_url(self, val) : self.bibjson["author_pays_url"] = val
    
    @property
    def author_pays(self): return self.bibjson.get("author_pays")
    @author_pays.setter
    def author_pays(self, val) : self.bibjson["author_pays"] = val
    
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
    def active(self): return self.bibjson.get("active")
    @active.setter
    def active(self, val) : self.bibjson["active"] = val
    
    @property
    def for_free(self): return self.bibjson.get("for_free")
    @for_free.setter
    def for_free(self, val) : self.bibjson["for_free"] = val
    
    # complex part getters and setters
    
    def add_identifier(self, idtype, value):
        if "identifier" not in self.bibjson:
            self.bibjson["identifier"] = []
        idobj = {"type" : idtype, "id" : value}
        self.bibjson["identifier"].append(idobj)
    
    def get_identifiers(self, idtype):
        ids = []
        for identifier in self.bibjson.get("identifier", []):
            if identifier.get("type") == idtype and identifier.get("id") not in ids:
                ids.append(identifier.get("id"))
        return ids
    
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
    
    def add_keyword(self, keyword):
        if "keywords" not in self.bibjson:
            self.bibjson["keywords"] = []
        self.bibjson["keywords"].append(keyword)
    
    def set_keywords(self, keywords):
        self.bibjson["keywords"] = keywords
    
    def set_license(self, licence_title, licence_type, url=None, version=None, open_access=None):
        if "license" not in self.bibjson:
            self.bibjson["license"] = []
        
        lobj = {"title" : licence_title, "type" : licence_type}
        if url is not None:
            lobj["url"] = url
        if version is not None:
            lobj["version"] = version
        if open_access is not None:
            lobj["open_access"] = open_access
        
        self.bibjson["license"].append(lobj)
    
    def set_open_access(self, open_access):
        if "license" not in self.bibjson:
            self.bibjson["license"] = []
        if len(self.bibjson["license"]) == 0:
            lobj = {"open_access" : open_access}
            self.bibjon["license"].append(lobj)
        else:
            self.bibjson["license"][0]["open_access"] = open_access
    
    def add_url(self, url):
        if "link" not in self.bibjson:
            self.bibjson["link"] = []
        self.bibjson["link"].append({"url" : url})
    
    def set_oa_start(self, year=None, volume=None, number=None):
        oaobj = {}
        if year is not None:
            oaobj["year"] = year
        if volume is not None:
            oaobj["volume"] = volume
        if number is not None:
            oaobj["number"] = number
        self.bibjson["oa_start"] = oaobj
    
    def set_oa_end(self, year=None, volume=None, number=None):
        oaobj = {}
        if year is not None:
            oaobj["year"] = year
        if volume is not None:
            oaobj["volume"] = volume
        if number is not None:
            oaobj["number"] = number
        self.bibjson["oa_end"] = oaobj

    def add_subject(self, scheme, term):
        if "subject" not in self.bibjson:
            self.bibjson["subject"] = []
        sobj = {"scheme" : scheme, "term" : term}
        self.bibjson["subject"].append(sobj)





















    
