from portality.dao import DomainObject
from portality.core import app
from portality.models.v2.bibjson import JournalLikeBibJSON
from portality.models.v2 import shared_structs
from portality.lib import es_data_mapping, dates, coerce
from portality.lib.seamless import SeamlessMixin
from portality.lib.coerce import COERCE_MAP

from copy import deepcopy
from datetime import datetime

import string, uuid
from unidecode import unidecode

JOURNAL_STRUCT = {
    "fields": {
        "last_reapplication": {"coerce": "utcdatetime"}
    },
    "objects": [
        "admin", "index"
    ],

    "structs": {
        "admin": {
            "fields": {
                "in_doaj": {"coerce": "bool"},
                "ticked": {"coerce": "bool"},
                "current_application": {"coerce": "unicode"}
            },
            "lists": {
                "related_applications": {"contains": "object"}
            },
            "structs": {
                "related_applications": {
                    "fields": {
                        "application_id": {"coerce": "unicode"},
                        "date_accepted": {"coerce": "utcdatetime"},
                        "status": {"coerce": "unicode"}
                    }
                },
                "contact": {
                    "name": {"coerce": "unicode"},
                    "email": {"coerce": "unicode"}
                }
            }
        },
        "index": {
            "fields": {
                "publisher_ac": {"coerce": "unicode"},
                "institution_ac": {"coerce": "unicode"}
            }
        }
    }
}


class ContinuationException(Exception):
    pass


class JournalLikeObject(SeamlessMixin, DomainObject):

    @classmethod
    def find_by_issn(cls, issns, in_doaj=None, max=10):
        if not isinstance(issns, list):
            issns = [issns]
        q = JournalQuery()
        q.find_by_issn(issns, in_doaj=in_doaj, max=max)
        result = cls.query(q=q.query)
        # create an arry of objects, using cls rather than Journal, which means subclasses can use it too (i.e. Suggestion)
        records = [cls(**r.get("_source")) for r in result.get("hits", {}).get("hits", [])]
        return records

    @classmethod
    def issns_by_owner(cls, owner):
        q = IssnQuery(owner)
        res = cls.query(q=q.query())
        issns = [term.get("term") for term in res.get("facets", {}).get("issns", {}).get("terms", [])]
        return issns

    @classmethod
    def issns_by_query(cls, query):
        issns = []
        for j in cls.iterate(query):
            issns += j.known_issns()
        return issns

    @classmethod
    def find_by_journal_url(cls, url, in_doaj=None, max=10):
        q = JournalURLQuery(url, in_doaj, max)
        result = cls.query(q=q.query())
        # create an arry of objects, using cls rather than Journal, which means subclasses can use it too (i.e. Suggestion)
        records = [cls(**r.get("_source")) for r in result.get("hits", {}).get("hits", [])]
        return records

    ############################################
    ## base property methods

    @property
    def data(self):
        return self.__seamless__.data

    @property
    def has_apc(self):
        return self.__seamless__.get_single("bibjson.apc.has_apc")

    @property
    def id(self):
        return self.__seamless__.get_single("id")

    def set_id(self, id=None):
        if id is None:
            id = self.makeid()
        self.__seamless__.set_with_struct("id", id)

    def set_created(self, date=None):
        if date is None:
            date = dates.now()
        self.__seamless__.set_with_struct("created_date", date)

    @property
    def created_date(self):
        return self.__seamless__.get_single("created_date")

    @property
    def created_timestamp(self):
        return self.__seamless__.get_single("created_date", coerce=coerce.to_datestamp())

    def set_last_updated(self, date=None):
        if date is None:
            date = dates.now()
        self.__seamless__.set_with_struct("last_updated", date)

    @property
    def last_updated(self):
        return self.__seamless__.get_single("last_updated")

    @property
    def last_updated_timestamp(self):
        return self.__seamless__.get_single("last_updated", coerce=coerce.to_datestamp())

    def set_last_manual_update(self, date=None):
        if date is None:
            date = dates.now()
        self.__seamless__.set_with_struct("last_manual_update", date)

    @property
    def last_manual_update(self):
        return self.__seamless__.get_single("last_manual_update")

    @property
    def last_manual_update_timestamp(self):
        return self.__seamless__.get_single("last_manual_update", coerce=coerce.to_datestamp())

    def has_been_manually_updated(self):
        lmut = self.last_manual_update_timestamp
        if lmut is None:
            return False
        return lmut > datetime.utcfromtimestamp(0)

    def has_seal(self):
        return self.__seamless__.get_single("admin.seal", default=False)

    def set_seal(self, value):
        self.__seamless__.set_with_struct("admin.seal", value)

    @property
    def bulk_upload_id(self):
        return self.__seamless__.get_single("admin.bulk_upload")

    def set_bulk_upload_id(self, bulk_upload_id):
        self.__seamless__.set_with_struct("admin.bulk_upload", bulk_upload_id)

    @property
    def owner(self):
        return self.__seamless__.get_single("admin.owner")

    def set_owner(self, owner):
        self.__seamless__.set_with_struct("admin.owner", owner)

    def remove_owner(self):
        self.__seamless__.delete("admin.owner")

    @property
    def editor_group(self):
        return self.__seamless__.get_single("admin.editor_group")

    def set_editor_group(self, eg):
        self.__seamless__.set_with_struct("admin.editor_group", eg)

    def remove_editor_group(self):
        self.__seamless__.delete("admin.editor_group")

    @property
    def editor(self):
        return self.__seamless__.get_single("admin.editor")

    def set_editor(self, ed):
        self.__seamless__.set_with_struct("admin.editor", ed)

    def remove_editor(self):
        self.__seamless__.delete('admin.editor')

    @property
    def contact(self):
        return self.__seamless__.get_single("admin.contact")

    @property
    def contact_name(self):
        return self.__seamless__.get_single("admin.contact.name")

    @contact_name.setter
    def contact_name(self, name):
        self.__seamless__.set_with_struct("admin.contact.name", name)

    @property
    def contact_email(self):
        return self.__seamless__.get_single("admin.contact.email")

    @contact_email.setter
    def contact_email(self, email):
        self.__seamless__.set_with_struct("admin.contact.email", email)

    def set_contact(self, name, email):
        self.contact_name = name
        self.contact_email = email

    def remove_contact(self):
        self.__seamless__.delete("admin.contact")

    def add_note(self, note, date=None, id=None):
        if date is None:
            date = dates.now()
        obj = {"date": date, "note": note, "id": id}
        self.__seamless__.delete_from_list("admin.notes", matchsub=obj)
        if id is None:
            obj["id"] = uuid.uuid4()
        self.__seamless__.add_to_list_with_struct("admin.notes", obj)

    def remove_note(self, note):
        self.__seamless__.delete_from_list("admin.notes", matchsub=note)

    def set_notes(self, notes):
        self.__seamless__.set_with_struct("admin.notes", notes)

    def remove_notes(self):
        self.__seamless__.delete("admin.notes")

    @property
    def notes(self):
        return self.__seamless__.get_list("admin.notes")

    @property
    def ordered_notes(self):
        notes = self.notes
        clusters = {}
        for note in notes:
            if note["date"] not in clusters:
                clusters[note["date"]] = [note]
            else:
                clusters[note["date"]].append(note)
        ordered_keys = sorted(list(clusters.keys()), reverse=True)
        ordered = []
        for key in ordered_keys:
            clusters[key].reverse()
            ordered += clusters[key]
        return ordered

    def bibjson(self):
        bj = self.__seamless__.get_single("bibjson")
        if bj is None:
            self.__seamless__.set_single("bibjson", {})
            bj = self.__seamless__.get_single("bibjson")
        return JournalLikeBibJSON(bj)

    def set_bibjson(self, bibjson):
        bibjson = bibjson.data if isinstance(bibjson, JournalLikeBibJSON) else bibjson
        self.__seamless__.set_with_struct("bibjson", bibjson)

    ######################################################
    ## DEPRECATED METHODS

    def known_issns(self):
        """
        DEPRECATED

        all issns this journal is known by

        This used to mean "all issns the journal has ever been known by", but that definition has changed since
        continuations have been separated from the single journal object model.

        Now this is just a proxy for self.bibjson().issns()
        """
        return self.bibjson().issns()

    def get_latest_contact_name(self):
        return self.contact_name

    def get_latest_contact_email(self):
        return self.contact_email

    def add_contact(self, name, email):
        self.set_contact(name, email)

    def remove_contacts(self):
        self.remove_contact()

    ######################################################
    ## internal utility methods

    def _generate_index(self):
        # the index fields we are going to generate
        titles = []
        subjects = []
        schema_subjects = []
        schema_codes = []
        classification = []
        langs = []
        country = None
        license = []
        publisher = []
        has_seal = None
        classification_paths = []
        unpunctitle = None
        asciiunpunctitle = None
        continued = "No"
        has_editor_group = "No"
        has_editor = "No"

        # the places we're going to get those fields from
        cbib = self.bibjson()

        # get the title out of the current bibjson
        if cbib.title is not None:
            titles.append(cbib.title)
        if cbib.alternative_title:
            titles.append(cbib.alternative_title)

        # get the subjects and concatenate them with their schemes from the current bibjson
        for subs in cbib.subject:
            scheme = subs.get("scheme")
            term = subs.get("term")
            subjects.append(term)
            schema_subjects.append(scheme + ":" + term)
            classification.append(term)
            if "code" in subs:
                schema_codes.append(scheme + ":" + subs.get("code"))

        # add the keywords to the non-schema subjects (but not the classification)
        subjects += cbib.keywords

        # get the bibjson object to convert the languages to the english form
        langs = cbib.language_name()

        # get the english name of the country
        country = cbib.country_name()

        # get the type of the licenses
        for l in cbib.licences:
            license.append(l.get("type"))

        # deduplicate the lists
        titles = list(set(titles))
        subjects = list(set(subjects))
        schema_subjects = list(set(schema_subjects))
        classification = list(set(classification))
        license = list(set(license))
        schema_codes = list(set(schema_codes))

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

        # record if this journal object is a continuation
        if len(cbib.replaces) > 0 or len(cbib.is_replaced_by) > 0:
            continued = "Yes"

        if self.editor_group is not None:
            has_editor_group = "Yes"

        if self.editor is not None:
            has_editor = "Yes"

        # build the index part of the object
        index = {}

        if country is not None:
            index["country"] = country
        if has_seal:
            index["has_seal"] = has_seal
        if unpunctitle is not None:
            index["unpunctitle"] = unpunctitle
        if asciiunpunctitle is not None:
            index["asciiunpunctitle"] = asciiunpunctitle
        index["continued"] = continued
        index["has_editor_group"] = has_editor_group
        index["has_editor"] = has_editor

        index["issn"] = cbib.issns()
        if len(titles) > 0:
            index["title"] = titles
        if len(subjects) > 0:
            index["subject"] = subjects
        if len(schema_subjects) > 0:
            index["schema_subject"] = schema_subjects
        if len(classification) > 0:
            index["classification"] = classification
        if len(langs) > 0:
            index["language"] = langs
        if len(license) > 0:
            index["license"] = license
        if len(classification_paths) > 0:
            index["classification_paths"] = classification_paths
        if len(schema_codes) > 0:
            index["schema_code"] = schema_codes

        self.__seamless__.set_with_struct("index", index)


class Journal(JournalLikeObject):
    __type__ = "journal"

    __SEAMLESS_STRUCT__ = [
        shared_structs.JOURNAL_BIBJSON,
        shared_structs.SHARED_JOURNAL_LIKE,
        JOURNAL_STRUCT
    ]

    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        # FIXME: I have taken this out for the moment, as I'm not sure it's what we should be doing
        #if kwargs:
        #    self.add_autogenerated_fields(**kwargs)
        super(Journal, self).__init__(raw=kwargs)

    @classmethod
    def add_autogenerated_fields(cls, **kwargs):
        bib = kwargs["bibjson"]
        if "apc" in bib and bib["apc"] != '':
            bib["apc"]["has_apc"] = len(bib["apc"]["max"]) != 0
        else:
            bib["apc"] = {"has_apc": False}
        if "deposit_policy" in bib and bib["deposit_policy"] != '':
            bib["deposit_policy"]["has_policy"] = bib["deposit_policy"]["url"] is not None
        else:
            bib["deposit_policy"] = {"has_policy": False}
        if "other_charges" in bib and bib["other_charges"] != '':
            bib["other_charges"]["has_other_charges"] = bib["other_charges"]["url"] is not None
        else:
            bib["other_charges"] = {"has_other_charges": False}
        if "copyright" in bib and bib["copyright"]["url"] != '':
            bib["copyright"]["author_retains"] = bib["copyright"]["url"] is not None
        else:
            bib["copyright"] = {"author_retains": False}
        if "pid_scheme" in bib and bib["pid_scheme"] != '':
            bib["pid_scheme"]["has_pid_scheme"] = len(bib["pid_scheme"]["scheme"]) != 0
        else:
            bib["pid_scheme"] = {"has_pid_scheme": False}
        if "preservation" in bib and bib["preservation"] != '':
            bib["preservation"]["has_preservation"] = (len(bib["preservation"]) != 0 or
                                                    bib["national_library"] is not None)
        else:
            bib["preservation"] = {"has_preservation": True}

    #####################################################
    ## Journal-specific data access methods

    @classmethod
    def all_in_doaj(cls, page_size=5000):
        q = JournalQuery()
        return cls.iterate(q.all_in_doaj(), page_size=page_size, wrap=True)

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

    @classmethod
    def delete_selected(cls, query, articles=False, snapshot_journals=True, snapshot_articles=True):
        if articles:
            # list the issns of all the journals
            issns = cls.issns_by_query(query)

            # issue a delete request over all the articles by those issns
            from portality.models import Article
            Article.delete_by_issns(issns, snapshot=snapshot_articles)

        # snapshot the journal record
        if snapshot_journals:
            js = cls.iterate(query, page_size=1000)
            for j in js:
                j.snapshot()

        # finally issue a delete request against the journals
        cls.delete_by_query(query)

    def all_articles(self):
        from portality.models import Article
        return Article.find_by_issns(self.known_issns())

    def article_stats(self):
        from portality.models import Article
        q = ArticleStatsQuery(self.known_issns())
        data = Article.query(q=q.query())
        hits = data.get("hits", {})
        total = hits.get("total", 0)
        latest = None
        if total > 0:
            latest = hits.get("hits", [])[0].get("_source").get("created_date")
        return {
            "total": total,
            "latest": latest
        }

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    ############################################
    ## base property methods

    @property
    def toc_id(self):
        id_ = self.bibjson().get_preferred_issn()
        if not id_:
            id_ = self.id
        return id_

    @property
    def last_update_request(self):
        related = self.related_applications
        if len(related) == 0:
            return None
        sorted(related, key=lambda x: x.get("date_accepted", "1970-01-01T00:00:00Z"))
        return related[0].get("date_accepted", "1970-01-01T00:00:00Z")

    ############################################################
    ## revision history methods

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

    #######################################################################
    ## Conversion methods

    def make_continuation(self, type, eissn=None, pissn=None, title=None):
        # check that the type is one we know.  Must be either 'replaces' or 'is_replaced_by'
        if type not in ["replaces", "is_replaced_by"]:
            raise ContinuationException("type must be one of 'replaces' or 'is_replaced_by'")

        if eissn is None and pissn is None:
            raise ContinuationException("You must create a continuation with at least one issn")

        # take a copy of the raw data for this journal, and the issns for this journal
        raw_cont = deepcopy(self.data)
        bibjson = self.bibjson()
        issns = bibjson.issns()
        cissns = []

        # make a new instance of the journal - this will be our continuation
        del raw_cont["id"]
        del raw_cont["created_date"]
        del raw_cont["last_updated"]
        j = Journal(**raw_cont)

        # ensure that the journal is NOT in doaj.  That will be for the admin to decide
        j.set_in_doaj(False)

        # get a copy of the continuation's bibjson, then remove the existing issns
        cbj = j.bibjson()
        del cbj.eissn
        del cbj.pissn

        # also remove any existing continuation information
        del cbj.replaces
        del cbj.is_replaced_by
        del cbj.discontinued_date

        # now write the new identifiers
        if eissn is not None and eissn != "":
            cissns.append(eissn)
            cbj.eissn = eissn
        if pissn is not None and pissn != "":
            cissns.append(pissn)
            cbj.pissn = pissn

        # update the title
        if title is not None:
            cbj.title = title

        # now add the issns of the original journal in the appropriate field
        #
        # This is a bit confusing - because we're asking this of a Journal object, the relationship type we're asking
        # for relates to this journal, not to the continuation we are creating.  This means that when setting the
        # new continuations properties, we have to do the opposite to what we do to the journal's properties
        #
        # "replaces" means that the current journal replaces the new continuation
        if type == "replaces":
            bibjson.replaces = cissns
            cbj.is_replaced_by = issns

        # "is_replaced_by" means that the current journal is replaced by the new continuation
        elif type == "is_replaced_by":
            bibjson.is_replaced_by = cissns
            cbj.replaces = issns

        # save this journal
        self.save()

        # save the continuation, and return a copy to the caller
        j.save()
        return j

    ####################################################
    ## admin data methods

    def is_in_doaj(self):
        return self.__seamless__.get_single("admin.in_doaj", default=False)

    def set_in_doaj(self, value):
        self.__seamless__.set_with_struct("admin.in_doaj", value)

    def is_ticked(self):
        return self.__seamless__.get_single("admin.ticked", default=False)

    def set_ticked(self, ticked):
        self.__seamless__.set_with_struct("admin.ticked", ticked)

    @property
    def current_application(self):
        return self.__seamless__.get_single("admin.current_application")

    def set_current_application(self, application_id):
        self.__seamless__.set_with_struct("admin.current_application", application_id)

    def remove_current_application(self):
        self.__seamless__.delete("admin.current_application")

    @property
    def related_applications(self):
        return self.__seamless__.get_list("admin.related_applications")

    def add_related_application(self, application_id, date_accepted=None, status=None):
        obj = {"application_id": application_id}
        self.__seamless__.delete_from_list("admin.related_applications", matchsub=obj)
        if date_accepted is not None:
            obj["date_accepted"] = date_accepted
        if status is not None:
            obj["status"] = status
        self.__seamless__.add_to_list_with_struct("admin.related_applications", obj)

    def set_related_applications(self, related_applications_records):
        self.__seamless__.set_with_struct("admin.related_applications", related_applications_records)

    def remove_related_applications(self):
        self.__seamless__.delete("admin.related_applications")

    def related_application_record(self, application_id):
        for record in self.related_applications:
            if record.get("application_id") == application_id:
                return record
        return None

    def latest_related_application_id(self):
        related = self.related_applications
        if len(related) == 0:
            return None
        if len(related) == 1:
            return related[0].get("application_id")
        sorted(related, key=lambda x: x.get("date_accepted", "1970-01-01T00:00:00Z"))
        return related[0].get("application_id")

    ########################################################################
    ## Functions for handling continuations

    def get_future_continuations(self):
        irb = self.bibjson().is_replaced_by
        q = ContinuationQuery(irb)

        future = []
        journals = self.q2obj(q=q.query())
        subjournals = []
        for j in journals:
            subjournals += j.get_future_continuations()

        future = journals + subjournals
        return future

    def get_past_continuations(self):
        replaces = self.bibjson().replaces
        q = ContinuationQuery(replaces)

        past = []
        journals = self.q2obj(q=q.query())
        subjournals = []
        for j in journals:
            subjournals += j.get_past_continuations()

        past = journals + subjournals
        return past

    #######################################################################

    #####################################################
    ## operations we can do to the journal

    def calculate_tick(self):
        created_date = self.created_date
        last_update_request = self.last_update_request

        tick_threshold = app.config.get("TICK_THRESHOLD", '2014-03-19T00:00:00Z')
        threshold = datetime.strptime(tick_threshold, "%Y-%m-%dT%H:%M:%SZ")

        if created_date is None:  # don't worry about the last_update_request date - you can't update unless you've been created!
            # we haven't even saved the record yet.  All we need to do is check that the tick
            # threshold is in the past (which I suppose theoretically it could not be), then
            # set it
            if datetime.utcnow() >= threshold:
                self.set_ticked(True)
            else:
                self.set_ticked(False)
            return

        # otherwise, this is an existing record, and we just need to update it

        # convert the strings to datetime objects
        created = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
        lud = None
        if last_update_request is not None:
            lud = datetime.strptime(last_update_request, "%Y-%m-%dT%H:%M:%SZ")

        if created >= threshold and self.is_in_doaj():
            self.set_ticked(True)
            return

        if lud is not None and lud >= threshold and self.is_in_doaj():
            self.set_ticked(True)
            return

        self.set_ticked(False)

    def propagate_in_doaj_status_to_articles(self):
        for article in self.all_articles():
            article.set_in_doaj(self.is_in_doaj())
            article.save()

    def prep(self, is_update=True):
        self._ensure_in_doaj()
        self.calculate_tick()
        self._generate_index()
        self._calculate_has_apc()
        self._generate_autocompletes()
        if is_update:
            self.set_last_updated()

    def save(self, snapshot=True, sync_owner=True, **kwargs):
        self.prep()
        self.verify_against_struct()
        if sync_owner:
            self._sync_owner_to_application()
        res = super(Journal, self).save(**kwargs)
        if snapshot:
            self.snapshot()
        return res

    ######################################################
    ## internal utility methods

    def _generate_autocompletes(self):
        bj = self.bibjson()
        publisher = bj.publisher
        institution = bj.institution

        if publisher is not None:
            self.__seamless__.set_with_struct("index.publisher_ac", publisher.lower())

        if institution is not None:
            self.__seamless__.set_with_struct("index.institution_ac", institution.lower())

    def _ensure_in_doaj(self):
        if self.__seamless__.get_single("admin.in_doaj", default=None) is None:
            self.set_in_doaj(False)

    def _sync_owner_to_application(self):
        if self.current_application is None:
            return
        from portality.models.v2.application import Application
        ca = Application.pull(self.current_application)
        if ca is not None and ca.owner != self.owner:
            ca.set_owner(self.owner)
            ca.save(sync_owner=False)

    def _calculate_has_apc(self):
        # work out of the journal has an apc
        has_apc = "No Information"
        apc_present = self.bibjson().has_apc
        if apc_present:
            has_apc = "Yes"
        elif self.is_ticked():  # Because if an item is not ticked we want to say "No Information"
            has_apc = "No"

        self.__seamless__.set_with_struct("index.has_apc", has_apc)


MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"],
    "exceptions": {
        "admin.notes.note": {
            "type": "string",
            "index": "not_analyzed",
            "include_in_all": False
        }
    }
}


########################################################
## Data Access Queries

class JournalQuery(object):
    """
    wrapper around the kinds of queries we want to do against the journal type
    """
    issn_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "terms": {"index.issn.exact": "<issn>"}
                    }
                ]
            }
        }
    }

    all_doaj = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"admin.in_doaj": True}}
                ]
            }
        }
    }

    _minified_fields = ["id", "bibjson.title", "last_updated"]

    def __init__(self, minified=False, sort_by_title=False):
        self.query = None
        self.minified = minified
        self.sort_by_title = sort_by_title

    def find_by_issn(self, issns, in_doaj=None, max=10):
        self.query = deepcopy(self.issn_query)
        self.query["query"]["bool"]["must"][0]["terms"]["index.issn.exact"] = issns
        if in_doaj is not None:
            self.query["query"]["bool"]["must"].append({"term": {"admin.in_doaj": in_doaj}})
        self.query["size"] = max

    def all_in_doaj(self):
        q = deepcopy(self.all_doaj)
        if self.minified:
            q["fields"] = self._minified_fields
        if self.sort_by_title:
            q["sort"] = [{"bibjson.title.exact": {"order": "asc"}}]
        return q


class JournalURLQuery(object):
    def __init__(self, url, in_doaj=None, max=10):
        self.url = url
        self.in_doaj = in_doaj
        self.max = max

    def query(self):
        q = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "terms": {"bibjson.ref.journal.exact": self.url}
                        }
                    ]
                }
            },
            "size" : self.max
        }
        if self.in_doaj is not None:
            q["query"]["bool"]["must"].append({"term": {"admin.in_doaj": self.in_doaj}})
        return q

class IssnQuery(object):
    base_query = {
        "query": {
            "term": {"admin.owner.exact": "<owner id here>"}
        },
        "size": 0,
        "facets": {
            "issns": {
                "terms": {
                    "field": "index.issn.exact",
                    "size": 10000,
                    "order": "term"
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
        "query": {
            "term": {"bibjson.publisher.name.exact": "<publisher name here>"}
        },
        "size": 10000
    }

    inexact_query = {
        "query": {
            "term": {"bibjson.publisher.name": "<publisher name here>"}
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
            q["query"]["term"]["bibjson.publisher.name.exact"] = self.publisher
        else:
            q = deepcopy(self.inexact_query)
            q["query"]["term"]["bibjson.publisher.name"] = self.publisher.lower()
        return q


class TitleQuery(object):
    base_query = {
        "query": {
            "term": {"index.title.exact": "<title here>"}
        },
        "size": 10000
    }

    def __init__(self, title):
        self.title = title

    def query(self):
        q = deepcopy(self.base_query)
        q["query"]["term"]["index.title.exact"] = self.title
        return q


class ContinuationQuery(object):
    def __init__(self, issns):
        self.issns = issns

    def query(self):
        return {
            "query": {
                "bool": {
                    "must": [
                        {"terms": {"index.issn.exact": self.issns}}
                    ]
                }
            },
            "size": 10000
        }


class ArticleStatsQuery(object):
    def __init__(self, issns):
        self.issns = issns

    def query(self):
        return {
            "query": {
                "bool": {
                    "must": [
                        {"terms": {"index.issn.exact": self.issns}},
                        {"term": {"admin.in_doaj": True}}
                    ]
                }
            },
            "size": 1,
            "_source": {
                "include": ["created_date"]
            },
            "sort": [{"created_date": {"order": "desc"}}]
        }
