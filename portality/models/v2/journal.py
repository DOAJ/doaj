from portality.dao import DomainObject
from portality.core import app
from portality.models.v2.bibjson import JournalLikeBibJSON
from portality.models.v2 import shared_structs
from portality.lib import dataobj, es_data_mapping, dates
from portality import datasets

from copy import deepcopy
from datetime import datetime

import string
from unidecode import unidecode

class ContinuationException(Exception):
    pass

class JournalLikeObject(dataobj.DataObj, DomainObject):

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

    ############################################
    ## base property methods

    @property
    def id(self):
        return self._get_single("id")

    def set_id(self, id=None):
        if id is None:
            id = self.makeid()
        self._set_with_struct("id", id)

    def set_created(self, date=None):
        if date is None:
            date = dates.now()
        self._set_with_struct("created_date", date)

    @property
    def created_date(self):
        return self._get_single("created_date")

    @property
    def created_timestamp(self):
        return self._get_single("created_date", coerce=dataobj.to_datestamp())

    def set_last_updated(self, date=None):
        if date is None:
            date = dates.now()
        self._set_with_struct("last_updated", date)

    @property
    def last_updated(self):
        return self._get_single("last_updated")

    @property
    def last_updated_timestamp(self):
        return self._get_single("last_updated", coerce=dataobj.to_datestamp())

    def bibjson(self):
        bj = self._get_single("bibjson")
        if bj is None:
            self._set_single("bibjson", {})
            bj = self._get_single("bibjson")
        return JournalLikeBibJSON(bj)

    def set_bibjson(self, bibjson):
        bibjson = bibjson.data if isinstance(bibjson, JournalLikeBibJSON) else bibjson
        self._set_with_struct("bibjson", bibjson)

    def set_last_manual_update(self, date=None):
        if date is None:
            date = dates.now()
        self._set_with_struct("last_manual_update", date)

    @property
    def last_manual_update(self):
        return self._get_single("last_manual_update")

    @property
    def last_manual_update_timestamp(self):
        return self._get_single("last_manual_update", coerce=dataobj.to_datestamp())

    def has_been_manually_updated(self):
        return self.last_manual_update_timestamp > datetime.utcfromtimestamp(0)

    def contacts(self):
        return self._get_list("admin.contact")

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
        self._add_to_list_with_struct("admin.contact", {"name" : name, "email" : email})

    def remove_contacts(self):
        self._delete("admin.contact")

    def add_note(self, note, date=None):
        if date is None:
            date = dates.now()
        obj = {"date" : date, "note" : note}
        self._delete_from_list("admin.notes", matchsub=obj)
        self._add_to_list_with_struct("admin.notes", obj)

    def remove_note(self, note):
        self._delete_from_list("admin.notes", matchsub=note)

    def set_notes(self, notes):
        self._set_with_struct("admin.notes", notes)

    def remove_notes(self):
        self._delete("admin.notes")

    @property
    def notes(self):
        return self._get_list("admin.notes")

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
        # return sorted(notes, key=lambda x: x["date"], reverse=True)

    @property
    def owner(self):
        return self._get_single("admin.owner")

    def set_owner(self, owner):
        self._set_with_struct("admin.owner", owner)

    def remove_owner(self):
        self._delete("admin.owner")

    @property
    def editor_group(self):
        return self._get_single("admin.editor_group")

    def set_editor_group(self, eg):
        self._set_with_struct("admin.editor_group", eg)

    def remove_editor_group(self):
        self._delete("admin.editor_group")

    @property
    def editor(self):
        return self._get_single("admin.editor")

    def set_editor(self, ed):
        self._set_with_struct("admin.editor", ed)

    def remove_editor(self):
        self._delete('admin.editor')

    def known_issns(self):
        """
        DEPRECATED

        all issns this journal is known by

        This used to mean "all issns the journal has ever been known by", but that definition has changed since
        continuations have been separated from the single journal object model.

        Now this is just a proxy for self.bibjson().issns()
        """
        return self.bibjson().issns()

    def has_seal(self):
        return self._get_single("admin.seal", default=False)

    def set_seal(self, value):
        self._set_with_struct("admin.seal", value)

    @property
    def bulk_upload_id(self):
        return self._get_single("admin.bulk_upload")

    def set_bulk_upload_id(self, bulk_upload_id):
        self._set_with_struct("admin.bulk_upload", bulk_upload_id)

    ######################################################
    ## internal utility methods

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
        has_seal = None
        classification_paths = []
        unpunctitle = None
        asciiunpunctitle = None
        continued = "No"
        has_editor_group = "No"
        has_editor = "No"

        # the places we're going to get those fields from
        cbib = self.bibjson()

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

        # get the bibjson object to convert the languages to the english form
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
        if len(issns) > 0:
            index["issn"] = issns
        if len(titles) > 0:
            index["title"] = titles
        if len(subjects) > 0:
            index["subject"] = subjects
        if len(schema_subjects) > 0:
            index["schema_subject"] = schema_subjects
        if len(classification) > 0:
            index["classification"] = classification
        if len(publisher) > 0:
            index["publisher"] = publisher
        if len(license) > 0:
            index["license"] = license
        if len(langs) > 0:
            index["language"] = langs
        if country is not None:
            index["country"] = country
        if len(schema_codes) > 0:
            index["schema_code"] = schema_codes
        if len(list(urls.keys())) > 0:
            index.update(urls)
        if has_seal:
            index["has_seal"] = has_seal
        if len(classification_paths) > 0:
            index["classification_paths"] = classification_paths
        if unpunctitle is not None:
            index["unpunctitle"] = unpunctitle
        if asciiunpunctitle is not None:
            index["asciiunpunctitle"] = asciiunpunctitle
        index["continued"] = continued
        index["has_editor_group"] = has_editor_group
        index["has_editor"] = has_editor
        self._set_with_struct("index", index)

class Journal(JournalLikeObject):
    __type__ = "journal"

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        self._add_struct(shared_structs.SHARED_BIBJSON)
        self._add_struct(shared_structs.JOURNAL_BIBJSON_EXTENSION)
        self._add_struct(JOURNAL_STRUCT)
        super(Journal, self).__init__(raw=kwargs)

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
            "total" : total,
            "latest" : latest
        }

    def mappings(self):
        return es_data_mapping.create_mapping(self.get_struct(), MAPPING_OPTS)

    ############################################
    ## base property methods

    @property
    def toc_id(self):
        bibjson = self.bibjson()
        id_ = bibjson.get_one_identifier(bibjson.E_ISSN)
        if not id_:
            id_ = bibjson.get_one_identifier(bibjson.P_ISSN)
        if not id_:
            id_ = self.id
        return id_

    @property
    def last_update_request(self):
        related = self.related_applications
        if len(related) == 0:
            return None
        sorted(related, key=lambda x : x.get("date_accepted", "1970-01-01T00:00:00Z"))
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
        cbj.remove_identifiers(cbj.E_ISSN)
        cbj.remove_identifiers(cbj.P_ISSN)

        # also remove any existing continuation information
        del cbj.replaces
        del cbj.is_replaced_by
        del cbj.discontinued_date

        # now write the new identifiers
        if eissn is not None and eissn != "":
            cissns.append(eissn)
            cbj.add_identifier(cbj.E_ISSN, eissn)
        if pissn is not None and pissn != "":
            cissns.append(pissn)
            cbj.add_identifier(cbj.P_ISSN, pissn)

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
        return self._get_single("admin.in_doaj", default=False)

    def set_in_doaj(self, value):
        self._set_with_struct("admin.in_doaj", value)

    @property
    def current_application(self):
        return self._get_single("admin.current_application")

    def set_current_application(self, application_id):
        self._set_with_struct("admin.current_application", application_id)

    def remove_current_application(self):
        self._delete("admin.current_application")

    @property
    def related_applications(self):
        return self._get_list("admin.related_applications")

    def add_related_application(self, application_id, date_accepted=None, status=None):
        obj = {"application_id" : application_id}
        self._delete_from_list("admin.related_applications", matchsub=obj)
        if date_accepted is not None:
            obj["date_accepted"] = date_accepted
        if status is not None:
            obj["status"] = status
        self._add_to_list_with_struct("admin.related_applications", obj)

    def set_related_applications(self, related_applications_records):
        self._set_with_struct("admin.related_applications", related_applications_records)

    def remove_related_applications(self):
        self._delete("admin.related_applications")

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

    def is_ticked(self):
        return self._get_single("admin.ticked", default=False)

    def set_ticked(self, ticked):
        self._set_with_struct("admin.ticked", ticked)

    @property
    def toc_id(self):
        bibjson = self.bibjson()
        id_ = bibjson.get_one_identifier(bibjson.E_ISSN)
        if not id_:
            id_ = bibjson.get_one_identifier(bibjson.P_ISSN)
        if not id_:
            id_ = self.id
        return id_

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

        if created_date is None:    # don't worry about the last_update_request date - you can't update unless you've been created!
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

    def prep(self):
        self._ensure_in_doaj()
        self.calculate_tick()
        self._generate_index()
        self._calculate_has_apc()
        self._generate_autocompletes()
        self.set_last_updated()

    def save(self, snapshot=True, sync_owner=True, **kwargs):
        self.prep()
        self.check_construct()
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
        provider = bj.provider

        if publisher is not None:
            self._set_with_struct("index.publisher_ac", publisher.lower())

        if institution is not None:
            self._set_with_struct("index.institution_ac", institution.lower())

        if provider is not None:
            self._set_with_struct("index.provider_ac", provider.lower())

    def _calculate_has_apc(self):
        # work out of the journal has an apc
        has_apc = "No Information"
        apc_field_present = len(list(self.bibjson().apc.keys())) > 0
        if apc_field_present:
            has_apc = "Yes"
        elif self.is_ticked():
            has_apc = "No"

        self._set_with_struct("index.has_apc", has_apc)

    def _ensure_in_doaj(self):
        # switching active to false takes the item out of the DOAJ
        # though note that switching active to True does not put something IN the DOAJ
        if not self.bibjson().active:
            self.set_in_doaj(False)

    def _sync_owner_to_application(self):
        if self.current_application is None:
            return
        from portality.models import Suggestion
        ca = Suggestion.pull(self.current_application)
        if ca is not None and ca.owner != self.owner:
            ca.set_owner(self.owner)
            ca.save(sync_owner=False)


JOURNAL_STRUCT = {
    "fields" : {
        "id" : {"coerce" : "unicode"},
        "created_date" : {"coerce" : "utcdatetime"},
        "last_updated" : {"coerce" : "utcdatetime"},
        "last_reapplication" : {"coerce" : "utcdatetime"},
        "last_manual_update" : {"coerce" : "utcdatetime"}
    },
    "objects" : [
        "admin", "index"
    ],

    "structs" : {
        "admin" : {
            "fields" : {
                "in_doaj" : {"coerce" : "bool"},
                "ticked" : {"coerce" : "bool"},
                "seal" : {"coerce" : "bool"},
                "bulk_upload" : {"coerce" : "unicode"},
                "owner" : {"coerce" : "unicode"},
                "editor_group" : {"coerce" : "unicode"},
                "editor" : {"coerce" : "unicode"},
                "current_application" : {"coerce" : "unicode"}
            },
            "lists" : {
                "contact" : {"contains" : "object"},
                "notes" : {"contains" : "object"},
                "related_applications" : {"contains" : "object"}
            },
            "structs" : {
                "contact" : {
                    "fields" : {
                        "email" : {"coerce" : "unicode"},
                        "name" : {"coerce" : "unicode"}
                    }
                },
                "notes" : {
                    "fields" : {
                        "note" : {"coerce" : "unicode"},
                        "date" : {"coerce" : "utcdatetime"}
                    }
                },
                "related_applications" : {
                    "fields" : {
                        "application_id" : {"coerce" : "unicode"},
                        "date_accepted" : {"coerce" : "utcdatetime"},
                        "status" : {"coerce" : "unicode"}
                    }
                }
            }
        },
        "index" : {
            "fields" : {
                "country" : {"coerce" : "unicode"},
                "homepage_url" : {"coerce" : "unicode"},
                "waiver_policy_url" : {"coerce" : "unicode"},
                "editorial_board_url" : {"coerce" : "unicode"},
                "aims_scope_url" : {"coerce" : "unicode"},
                "author_instructions_url" : {"coerce" : "unicode"},
                "oa_statement_url" : {"coerce" : "unicode"},
                "has_apc" : {"coerce" : "unicode"},
                "has_seal" : {"coerce" : "unicode"},
                "unpunctitle" : {"coerce" : "unicode"},
                "asciiunpunctitle" : {"coerce" : "unicode"},
                "continued" : {"coerce" : "unicode"},
                "has_editor_group" : {"coerce" : "unicode"},
                "has_editor" : {"coerce" : "unicode"},
                "publisher_ac" : {"coerce" : "unicode"},
                "institution_ac" : {"coerce" : "unicode"},
                "provider_ac" : {"coerce" : "unicode"}
            },
            "lists" : {
                "issn" : {"contains" : "field", "coerce" : "unicode"},
                "title" : {"contains" : "field", "coerce" : "unicode"},
                "subject" : {"contains" : "field", "coerce" : "unicode"},
                "schema_subject" : {"contains" : "field", "coerce" : "unicode"},
                "classification" : {"contains" : "field", "coerce" : "unicode"},
                "language" : {"contains" : "field", "coerce" : "unicode"},
                "license" : {"contains" : "field", "coerce" : "unicode"},
                "classification_paths" : {"contains" : "field", "coerce" : "unicode"},
                "schema_code" : {"contains" : "field", "coerce" : "unicode"},
                "publisher" : {"contains" : "field", "coerce" : "unicode"}
            }
        }
    }
}

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
                        "terms" :  { "index.issn.exact" : "<issn>" }
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

    def find_by_issn(self, issns, in_doaj=None, max=10):
        self.query = deepcopy(self.issn_query)
        self.query["query"]["bool"]["must"][0]["terms"]["index.issn.exact"] = issns
        if in_doaj is not None:
            self.query["query"]["bool"]["must"].append({"term" : {"admin.in_doaj" : in_doaj}})
        self.query["size"] = max

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

class ContinuationQuery(object):
    def __init__(self, issns):
        self.issns = issns

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"terms" : {"index.issn.exact" : self.issns}}
                    ]
                }
            },
            "size" : 10000
        }

class ArticleStatsQuery(object):
    def __init__(self, issns):
        self.issns = issns

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"terms" : {"index.issn.exact" : self.issns}},
                        {"term" : {"admin.in_doaj" : True}}
                    ]
                }
            },
            "size" : 1,
            "_source" : {
                "include" : ["created_date"]
            },
            "sort" : [{"created_date" : {"order" : "desc"}}]
        }
