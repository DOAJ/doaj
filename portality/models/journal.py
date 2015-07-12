from portality.dao import DomainObject
from copy import deepcopy
from datetime import datetime
from portality.core import app
from portality.models import GenericBibJSON

import string
from unidecode import unidecode

# NOTE: DomainObject interferes with new style @property getter/setter
# so we can't use them here
class Journal(DomainObject):
    __type__ = "journal"

    @classmethod
    def find_by_issn(cls, issn, in_doaj=None):
        q = JournalQuery()
        q.find_by_issn(issn, in_doaj=in_doaj)
        result = cls.query(q=q.query)
        # create an arry of objects, using cls rather than Journal, which means subclasses can use it too (i.e. Suggestion)
        records = [cls(**r.get("_source")) for r in result.get("hits", {}).get("hits", [])]
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

    def snapshot(self):
        from portality.models import JournalHistory

        snap = deepcopy(self.data)
        if "id" in snap:
            snap["about"] = snap["id"]
            del snap["id"]
        if "index" in snap:
            del snap["index"]
        if "last_updated" in snap:
            del snap["last_updated"]
        if "created_date" in snap:
            del snap["created_date"]

        hist = JournalHistory(**snap)
        hist.save()

    ########################################################################
    ## Functions for handling continuations


    def history(self):
        """
        returns a list of ordered history objects with their date, replaces, replacedby and bibjson object
        as a tuple

        [(date, replaces, isreplacedby, bibjson)]
        """
        # get the raw history object from the data.  It constists of a date, an optional replaces/isreplacedby,
        # and the bibjson of the old version of the journal
        histories = self.data.get("history", [])
        if histories is None:
            histories = []

        # convert the histories into a lookup structure that we can use for ordering
        # of the form ([issns of replaces], [issns of record], [issns of isreplacedby])
        # also we record a mapping of a record's issns to the return value, which is a tuple of date, replaces, isreplacedby, and the bibjson object

        lookup = []
        register = []
        for h in histories:
            # get the issns for the current bibjson record
            bj = JournalBibJSON(h.get("bibjson"))
            eissns = bj.get_identifiers(JournalBibJSON.E_ISSN)
            pissns = bj.get_identifiers(JournalBibJSON.P_ISSN)

            # store the bibjson record in the register for use later
            register.append(
                (
                    eissns + pissns,
                    (h.get("date"), h.get("replaces"), h.get("isreplacedby"), bj)
                )
            )

            # put all the information we have into the lookup structure
            lookup.append((h.get("replaces"), eissns + pissns, h.get("isreplacedby")))

        # now construct an ordered list of issns based on inspeection of the lookup structure.
        # we loop through the lookup, and pull out the isreplacedby issns.  For each of those issns,
        # we look at all the other entries in the lookup to determine if one of them is the one that
        # replaces the current one (by comparing the irb issns to the record issns).  If we don't find
        # a match, then the entry in the lookup we are inspecting is the latest history record, and
        # we record the issn, and delete the record from the lookup.  That way, the lookup structure
        # reduces in size until there is nothing left.
        #
        # There are various things that can throw the ordering - basically, if there isn't a clean
        # replaces/isreplacedby chain, then the ordering will be unpredictable.  So ... manage your data
        # properly!
        ordered = []
        while len(lookup) > 0:
            i = 0                       # counter that we will use to refer to the current lookup row when we want to delete it
            for entry in lookup:
                found = False
                irbs = entry[2]         # is an array, so there could be multiple values here
                if irbs is not None:    # it could be none - the history API allows for it
                    for irb in irbs:
                        for other in lookup:
                            if irb in other[1] and irb not in other[2]: # make sure we don't inspect the same record as where our irb comes from
                                found = True
                                break
                        if found:               # propagate the break
                            break
                if not found:
                    if len(entry[1]) > 0:               # check there is an ISSN.  If there is not, this is a data fail - there's not a lot we can do about it
                        ordered.append(entry[1][0])     # add just one issn to the ordered list - we don't need any more info
                    del lookup[i]                   # remove this record from the lookup
                    break                           # and start again from scratch, since the array has now been modified
                i += 1

        # finally, take the ordered list of issns, and map them to the return values held in the
        # register.
        output = []
        for o in ordered:
            for r in register:
                if o in r[0]:
                    output.append(r[1])

        return output

    def get_history_raw(self):
        return self.data.get("history")

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

    def get_history_around(self, issn):
        cbj = self.bibjson()
        eissns = cbj.get_identifiers(JournalBibJSON.E_ISSN)
        pissns = cbj.get_identifiers(JournalBibJSON.P_ISSN)

        # if the supplied issn is one for the current version of the journal, return no
        # future continuations, and all of the past ones in order
        if issn in eissns or issn in pissns:
            return [], [h[3] for h in self.history()]

        # otherwise this is an old issn, so the current version is the most recent
        # future continuation
        future = [cbj]
        past = []
        trip = False

        # for each historical version, look to see if the supplied ISSN is the one
        # while putting all others in the past/future bins, depending on whether we've
        # passed the target or not
        for h in self.history():
            eissns = h[3].get_identifiers(JournalBibJSON.E_ISSN)
            pissns = h[3].get_identifiers(JournalBibJSON.P_ISSN)
            if issn in eissns or issn in pissns:
                trip = True
                continue
            else:
                if not trip:
                    future.append(h[3])
                else:
                    past.append(h[3])

        return future, past

    def make_continuation(self, replaces=None, isreplacedby=None):
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

    def set_history(self, history):
        self.data["history"] = history

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

    @property
    def toc_id(self):
        bibjson = self.bibjson()
        id_ = bibjson.get_one_identifier(bibjson.E_ISSN)
        if not id_:
            id_ = bibjson.get_one_identifier(bibjson.P_ISSN)
        if not id_:
            id_ = self.id
        return id_

    def issns_for_title(self, title):
        """locate the issns associated with the supplied title"""
        if title is None:
            return None

        incoming_title = title.strip().lower()

        # first check the main title / alt_title on the journal
        current_title = self.bibjson().title
        current_alt_title = self.bibjson().alternative_title
        if current_title is not None:
            if incoming_title == current_title.strip().lower():
                return self.bibjson().issns()
        if current_alt_title is not None:
            if incoming_title == current_alt_title.strip().lower():
                return self.bibjson().issns()

        # now check all of the historical records
        for d, r, irb, bj in self.history():
            history_title = bj.title
            history_alt_title = bj.alternative_title
            if history_title is not None:
                if incoming_title == history_title.strip().lower():
                    return bj.issns()
            if history_alt_title is not None:
                if incoming_title == history_alt_title.strip().lower():
                    return bj.issns()

        # return None if we didn't find anything
        return None


    #######################################################################


    def make_reapplication(self):
        from portality.models import Suggestion
        raw_reapp = deepcopy(self.data)

        # remove all the properties that won't be carried
        if "id" in raw_reapp:
            del raw_reapp["id"]
        if "index" in raw_reapp:
            del raw_reapp["index"]
        if "created_date" in raw_reapp:
            del raw_reapp["created_date"]
        if "last_updated" in raw_reapp:
            del raw_reapp["last_updated"]
        # there should not be an old suggestion record, but just to be safe
        if "suggestion" in raw_reapp:
            del raw_reapp["suggestion"]

        # construct the new admin object from the ground up
        admin = raw_reapp.get("admin")
        if admin is not None:
            na = {}
            na["application_status"] = "reapplication"
            na["current_journal"] = self.id
            if "notes" in admin:
                na["notes"] = admin["notes"]
            if "contact" in admin:
                na["contact"] = admin["contact"]
            if "owner" in admin:
                na["owner"] = admin["owner"]
            if "editor_group" in admin:
                na["editor_group"] = admin["editor_group"]
            if "editor" in admin:
                na["editor"] = admin["editor"]
            raw_reapp["admin"] = na

        # make the new suggestion
        reapp = Suggestion(**raw_reapp)
        reapp.suggested_on = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # there is no suggester, so we copy the journal contact details into the
        # suggester fields
        contacts = reapp.contacts()
        if len(contacts) > 0:
            reapp.set_suggester(contacts[0].get("name"), contacts[0].get("email"))

        reapp.save()

        # update this record to include the reapplication id
        self.set_current_application(reapp.id)
        self.save()

        # finally, return the reapplication in case the caller needs it
        return reapp

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

    def get_latest_contact_name(self):
        try:
            contact = self.contacts()[-1]
        except IndexError as e:
            return ""
        return contact.get("name", "")

    def get_latest_contact_email(self):
        try:
            contact = self.contacts()[-1]
        except IndexError as e:
            return ""
        return contact.get("email", "")


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

    def remove_current_application(self):
        if "admin" in self.data and "current_application" in self.data["admin"]:
            del self.data["admin"]["current_application"]

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
        return self.data.get("admin", {}).get("ticked", False)

    def set_ticked(self, ticked):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["ticked"] = ticked

    def has_seal(self):
        return self.data.get("admin", {}).get("seal", False)

    def set_seal(self, value):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["seal"] = value

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
        has_apc = None
        has_seal = None
        classification_paths = []
        unpunctitle = None
        asciiunpunctitle = None

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

        # get the bibjson object to conver the language to the english form
        langs = cbib.language_name()

        # get the english name of the country
        country = cbib.country_name()

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
        schema_codes = list(set(schema_codes))

        # work out of the journal has an apc
        has_apc = "Yes" if len(self.bibjson().apc.keys()) > 0 else "No"

        # determine if the seal is applied
        has_seal = "Yes" if self.has_seal() else "No"

        # get the full classification paths for the subjects
        classification_paths = cbib.lcc_paths()

        # create an unpunctitle
        if cbib.title is not None:
            throwlist = string.punctuation + '\n\t'
            unpunctitle = "".join(c for c in cbib.title if c not in throwlist).strip()
            try:
                asciiunpunctitle = unidecode(unpunctitle)
            except:
                asciiunpunctitle = unpunctitle
        
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
        if has_apc:
            self.data["index"]["has_apc"] = has_apc
        if has_seal:
            self.data["index"]["has_seal"] = has_seal
        if len(classification_paths) > 0:
            self.data["index"]["classification_paths"] = classification_paths
        if unpunctitle is not None:
            self.data["index"]["unpunctitle"] = unpunctitle
        if asciiunpunctitle is not None:
            self.data["index"]["asciiunpunctitle"] = asciiunpunctitle

    def _ensure_in_doaj(self):
        # switching active to false takes the item out of the DOAJ
        # though note that switching active to True does not put something IN the DOAJ
        if not self.bibjson().active:
            self.set_in_doaj(False)

    def calculate_tick(self):
        created_date = self.created_date
        last_reapplied = self.last_reapplication

        tick_threshold = app.config.get("TICK_THRESHOLD", '2014-03-19T00:00:00Z')
        threshold = datetime.strptime(tick_threshold, "%Y-%m-%dT%H:%M:%SZ")

        if created_date is None:    # don't worry about the last_reapplied date - you can't reapply unless you've been created!
            # we haven't even saved the record yet.  All we need to do is check that the tick
            # threshold is in the past (which I suppose theoretically it could not be), then
            # set it
            if datetime.now() >= threshold:
                self.set_ticked(True)
            else:
                self.set_ticked(False)
            return

        # otherwise, this is an existing record, and we just need to update it

        # convert the strings to datetime objects
        created = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
        reappd = None
        if last_reapplied is not None:
            reappd = datetime.strptime(last_reapplied, "%Y-%m-%dT%H:%M:%SZ")

        if created >= threshold and self.is_in_doaj():
            self.set_ticked(True)
            return

        if reappd is not None and reappd >= threshold and self.is_in_doaj():
            self.set_ticked(True)
            return

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

    def _sync_owner_to_application(self):
        if self.current_application is None:
            return
        from portality.models import Suggestion
        ca = Suggestion.pull(self.current_application)
        if ca is not None and ca.owner != self.owner:
            ca.set_owner(self.owner)
            ca.save(sync_owner=False)

    def save(self, snapshot=True, sync_owner=True, **kwargs):
        self.prep()
        if sync_owner:
            self._sync_owner_to_application()
        super(Journal, self).save(**kwargs)
        if snapshot:
            self.snapshot()


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

    def country_name(self):
        if self.country is not None:
            from portality import datasets  # delayed import because of files to be loaded
            return datasets.get_country_name(self.country)
        return None

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

    def language_name(self):
        # copy the languages and convert them to their english forms
        from portality import datasets  # delayed import, as it loads some stuff from file
        if self.language is not None:
            langs = self.language
        langs = [datasets.name_for_lang(l) for l in langs]

        # now we need to ensure that these are all correctly unicoded
        def to_utf8_unicode(val):
            if isinstance(val, unicode):
                return val
            elif isinstance(val, basestring):
                try:
                    return val.decode("utf8", "strict")
                except UnicodeDecodeError:
                    raise ValueError(u"Could not decode string")
            else:
                return unicode(val)

        langs = [to_utf8_unicode(l) for l in langs]
        return list(set(langs))

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
    def apc_url(self):
        return self.bibjson.get("apc_url")

    @apc_url.setter
    def apc_url(self, val):
        self.bibjson["apc_url"] = val

    @property
    def apc(self):
        return self.bibjson.get("apc", {})

    def set_submission_charges(self, currency, average_price):
        if "submission_charges" not in self.bibjson:
            self.bibjson["submission_charges"] = {}
        self.bibjson["submission_charges"]["currency"] = currency
        self.bibjson["submission_charges"]["average_price"] = average_price

    @property
    def submission_charges_url(self):
        return self.bibjson.get("submission_charges_url")

    @submission_charges_url.setter
    def submission_charges_url(self, val):
        self.bibjson["submission_charges_url"] = val

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

    @property
    def flattened_archiving_policies(self):
        return [ap if not isinstance(ap, list) else ": ".join(ap) for ap in self.archiving_policy.get("policy", [])]

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

    # to help with ToC - we prefer to refer to a journal by E-ISSN, or
    # if not, then P-ISSN
    def get_preferred_issn(self):
        issn = self.get_one_identifier(self.E_ISSN)
        if not issn:
            issn = self.get_one_identifier(self.P_ISSN)
        return issn

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

    def find_by_issn(self, issn, in_doaj=None):
        self.query = deepcopy(self.issn_query)
        self.query["query"]["bool"]["must"][0]["term"]["index.issn.exact"] = issn
        if in_doaj is not None:
            self.query["query"]["bool"]["must"].append({"term" : {"admin.in_doaj" : in_doaj}})

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
