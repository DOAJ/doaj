from portality.dao import DomainObject
from copy import deepcopy
from datetime import datetime
from portality.core import app
from portality import xwalk
from portality.models import GenericBibJSON

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
    def all_in_doaj(cls, page_size=5000, minified=False):
        q = JournalQuery(minified=minified, sort_by_title=minified)
        wrap = not minified
        return cls.iterate(q.all_in_doaj(), page_size=page_size, wrap=wrap)

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

    def get_history_for(self, issn):
        histories = self.data.get("history", [])
        for h in histories:
            bibjson = h.get("bibjson")
            if bibjson is None:
                continue
            jbj = JournalBibJSON(bibjson)
            eissns = jbj.get_identifiers(JournalBibJSON.E_ISSN)
            pissns = jbj.get_identifiers(JournalBibJSON.P_ISSN)
            if issn in eissns or issn in pissns:
                return jbj
        return None

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
                snobj["isreplacedby"] = [isreplacedby]
        if "history" not in self.data:
            self.data["history"] = []
        self.data["history"].append(snobj)

    def remove_history(self, issn):
        histories = self.data.get("history")
        if histories is None:
            return
        remove = -1
        for i in range(len(histories)):
            h = histories[i]
            bibjson = h.get("bibjson")
            if bibjson is None:
                continue
            jbj = JournalBibJSON(bibjson)
            eissns = jbj.get_identifiers(JournalBibJSON.E_ISSN)
            pissns = jbj.get_identifiers(JournalBibJSON.P_ISSN)
            if issn in eissns or issn in pissns:
                remove = i
                break
        if remove >= 0:
            del histories[i]
        if len(histories) == 0:
            del self.data["history"]

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

    def remove_note(self, note):
        self.notes().remove(note)

    def set_notes(self, notes):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data['admin']['notes'] = notes

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
        return self.data.get("admin", {}).get("owner", '')

    def set_owner(self, owner):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["owner"] = owner

    @property
    def editor_group(self):
        return self.data.get("admin", {}).get("editor_group")

    def set_editor_group(self, eg):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["editor_group"] = eg

    @property
    def editor(self):
        return self.data.get("admin", {}).get("editor")

    def set_editor(self, ed):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["editor"] = ed

    @property
    def current_application(self):
        return self.data.get("admin", {}).get("current_application")

    def set_current_application(self, application_id):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["current_application"] = application_id

    def known_issns(self):
        """ all issns this journal has ever been known by """
        issns = []

        # the places we're going to get those fields from
        cbib = self.bibjson()
        hist = self.history()

        # get the issns out of the current bibjson
        issns += cbib.get_identifiers(cbib.P_ISSN)
        issns += cbib.get_identifiers(cbib.E_ISSN)

        # now get the issns
        for date, r, irb, hbib in hist:
            issns += hbib.get_identifiers(hbib.P_ISSN)
            issns += hbib.get_identifiers(hbib.E_ISSN)

        return issns

    def is_ticked(self):
        return self.data.get("ticked", False)

    def set_ticked(self, ticked):
        self.data["ticked"] = ticked

    @property
    def last_reapplication(self):
        return self.data.get("last_reapplication")

    def set_last_reapplication(self, date=None):
        if date is None:
            self.data['last_reapplication'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            self.data['last_reapplication'] = date

    @property
    def bulk_upload_id(self):
        return self.data.get("admin", {}).get("bulk_upload")

    def set_bulk_upload_id(self, bulk_upload_id):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["bulk_upload"] = bulk_upload_id

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

    def calculate_tick(self):
        created_date = self.data.get("created_date", None)

        tick_threshold = app.config.get("TICK_THRESHOLD", '2014-03-19T00:00:00Z')
        threshold = datetime.strptime(tick_threshold, "%Y-%m-%dT%H:%M:%SZ")

        if not created_date:
            # we haven't even saved the record yet.  All we need to do is check that the tick
            # threshold is in the past (which I suppose theoretically it could not be), then
            # set it
            if datetime.now() > threshold:
                self.set_ticked(True)
            else:
                self.set_ticked(False)
            return

        # otherwise, this is an existing record, and we just need to update it
        created = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")

        if created > threshold and self.is_in_doaj():
            self.set_ticked(True)
        else:
            self.set_ticked(False)

    def all_articles(self):
        from portality.models import Article
        return Article.find_by_issns(self.known_issns())

    def propagate_in_doaj_status_to_articles(self):
        for article in self.all_articles():
            article.set_in_doaj(self.is_in_doaj())
            article.save()

    def prep(self):
        self._ensure_in_doaj()
        self._generate_index()
        self.calculate_tick()
        self.data['last_updated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def save(self, **kwargs):
        self.prep()
        super(Journal, self).save(**kwargs)

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
        # Identifier
        homepage = bibjson.get_urls(urltype="homepage")
        if len(homepage) > 0:
            row.append(homepage[0])
        else:
            row.append("")
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
        row.append( "" ) # author pays - DEPRECATED
        row.append("") # author pays url - DEPRECATED

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
        return self.bibjson.get("author_pays_url")

    @author_pays_url.setter
    def author_pays_url(self, val):
        self.bibjson["author_pays_url"] = val

    @property
    def author_pays(self):
        return self.bibjson.get("author_pays")

    @author_pays.setter
    def author_pays(self, val):
        self.bibjson["author_pays"] = val

    @author_pays.deleter
    def author_pays(self):
        if "author_pays" in self.bibjson:
            del self.bibjson["author_pays"]

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
    def active(self): return self.bibjson.get("active", True)
    @active.setter
    def active(self, val) : self.bibjson["active"] = val

    # journal-specific complex part getters and setters

    @property
    def language(self):
        return self.bibjson.get("language", [])

    def set_language(self, language):
        if isinstance(language, list):
            self.bibjson["language"] = language
        else:
            self.bibjson["language"] = [language]

    def add_language(self, language):
        if "language" not in self.bibjson:
            self.bibjson["language"] = []
        self.bibjson["language"].append(language)

    def set_license(self, license_title, license_type, url=None, version=None, open_access=None,
                    by=None, sa=None, nc=None, nd=None,
                    embedded=None, embedded_example_url=None):
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
        if embedded is not None:
            lobj["embedded"] = embedded
        if embedded_example_url is not None:
            lobj["embedded_example_url"] = embedded_example_url

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
        return self.bibjson.get("apc", {})

    def set_submission_charges(self, currency, average_price):
        if "submission_charges" not in self.bibjson:
            self.bibjson["submission_charges"] = {}
        self.bibjson["submission_charges"]["currency"] = currency
        self.bibjson["submission_charges"]["average_price"] = average_price

    @property
    def submission_charges(self):
        return self.bibjson.get("submission_charges", {})

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
        return self.bibjson.get("archiving_policy", {})

    def set_editorial_review(self, process, review_url):
        if "editorial_review" not in self.bibjson:
            self.bibjson["editorial_review"] = {}
        self.bibjson["editorial_review"]["process"] = process
        self.bibjson["editorial_review"]["url"] = review_url

    @property
    def editorial_review(self):
        return self.bibjson.get("editorial_review", {})

    def set_plagiarism_detection(self, url, has_detection=True):
        if "plagiarism_detection" not in self.bibjson:
            self.bibjson["plagiarism_detection"] = {}
        self.bibjson["plagiarism_detection"]["detection"] = has_detection
        self.bibjson["plagiarism_detection"]["url"] = url

    @property
    def plagiarism_detection(self):
        return self.bibjson.get("plagiarism_detection", {})

    def set_article_statistics(self, url, has_statistics=True):
        if "article_statistics" not in self.bibjson:
            self.bibjson["article_statistics"] = {}
        self.bibjson["article_statistics"]["statistics"] = has_statistics
        self.bibjson["article_statistics"]["url"] = url

    @property
    def article_statistics(self):
        return self.bibjson.get("article_statistics", {})

    @property
    def deposit_policy(self):
        return self.bibjson.get("deposit_policy", [])

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
        return self.bibjson.get("author_copyright", {})

    def set_author_publishing_rights(self, url, holds_rights=True):
        if "author_publishing_rights" not in self.bibjson:
            self.bibjson["author_publishing_rights"] = {}
        self.bibjson["author_publishing_rights"]["publishing_rights"] = holds_rights
        self.bibjson["author_publishing_rights"]["url"] = url

    @property
    def author_publishing_rights(self):
        return self.bibjson.get("author_publishing_rights", {})

    @property
    def allows_fulltext_indexing(self): return self.bibjson.get("allows_fulltext_indexing")
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

    _minified_fields = ["id", "bibjson.title", "last_updated"]

    def __init__(self, minified=False, sort_by_title=False):
        self.query = None
        self.minified = minified
        self.sort_by_title = sort_by_title

    def find_by_issn(self, issn):
        self.query = deepcopy(self.issn_query)
        self.query["query"]["bool"]["must"][0]["term"]["index.issn.exact"] = issn

    def all_in_doaj(self):
        q = deepcopy(self.all_doaj)
        if self.minified:
            q["fields"] = self._minified_fields
        if self.sort_by_title:
            q["sort"] = [{"bibjson.title.exact" : {"order" : "asc"}}]
        return q

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
