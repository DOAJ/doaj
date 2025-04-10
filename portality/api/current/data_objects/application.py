import uuid
from datetime import datetime

from portality.api.current.data_objects.common import _check_for_script
from portality.lib import swagger, seamless, coerce, dates, dataobj
from portality import models
from copy import deepcopy

from portality.api.current.data_objects.common_journal_application import OutgoingCommonJournalApplication, _SHARED_STRUCT

# both incoming and outgoing applications share this struct
# "required" fields are only put on incoming applications
from portality.lib.coerce import COERCE_MAP
from portality.lib.seamless import SeamlessMixin
from portality.models import JournalLikeBibJSON
from portality.ui.messages import Messages

OUTGOING_APPLICATION_STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},                # Note that we'll leave these in for ease of use by the
        "created_date": {"coerce": "utcdatetime"},  # caller, but we'll need to ignore them on the conversion
        "last_updated": {"coerce": "utcdatetime"}, # to the real object
        "last_manual_update": {"coerce": "utcdatetime"}
    },
    "objects": ["admin", "bibjson"],
    "structs": {
        "admin" : {
            "fields" : {
                "application_status" : {"coerce" : "unicode"},
                "current_journal" : {"coerce" : "unicode"},
                "date_applied" : {"coerce" : "unicode"},
                "owner" : {"coerce" : "unicode"}
            }
        }
    }
}

INTERNAL_APPLICATION_STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},                # Note that we'll leave these in for ease of use by the
        "created_date": {"coerce": "utcdatetime"},  # caller, but we'll need to ignore them on the conversion
        "last_updated": {"coerce": "utcdatetime"}, # to the real object
        "last_manual_update": {"coerce": "utcdatetime"},
        "es_type": {"coerce": "unicode"}
    },
    "objects": ["admin", "bibjson"],
    "structs": {
        "admin" : {
            "fields" : {
                "related_journal" : {"coerce" : "unicode"},
                "editor_group" : {"coerce" : "unicode"},
                "editor" : {"coerce" : "unicode"},
                "owner" : {"coerce" : "unicode"}
            },
            "lists": {
                "notes" : {"contains" : "object"},
            }
        }
    }
}


INCOMING_APPLICATION_REQUIREMENTS = {
    "required" : ["admin", "bibjson"],

    "structs": {
        "bibjson": {
            "lists": {
                # override for lax language enforcement in the core, making it strict for incoming applications
                "language": {"contains": "field", "coerce": "isolang_2letter_strict"}
            },
            "required": [
                "copyright",
                "deposit_policy",
                "editorial",
                "eissn",
                "keywords",
                "language",
                "license",
                "ref",
                "pid_scheme",
                "pissn",
                "plagiarism",
                "preservation",
                "publication_time_weeks",
                "publisher",
                "oa_start",
                "other_charges",
                "waiver",
                "title"
            ],
            "structs": {
                "copyright": {
                    "required" : ["url"]
                },
                "editorial": {
                    "required" : ["review_process", "review_url"]
                },
                "plagiarism": {
                    "required": ["detection","url"]
                },
                "publisher": {
                    "required": ["name"]
                },
                "ref": {
                    "required" : ["journal"]
                },
                # override for lax currency code enforcement in the core, making it strict for incoming applications
                "apc" : {
                    "lists" : {
                        "max" : {"contains" : "object"}
                    },
                    "structs" : {
                        "max" : {
                            "fields" : {
                                "currency" : {"coerce" : "currency_code_strict"},
                                "price" : {"coerce" : "integer"}
                            }
                        }
                    }
                }
            }
        }
    }
}


class IncomingApplication(SeamlessMixin, swagger.SwaggerSupport):
    """
    ~~APIIncomingApplication:Model->Seamless:Library~~
    """
    __type__ = "application"
    __SEAMLESS_COERCE__ = dict(COERCE_MAP)
    __SEAMLESS_STRUCT__ = [
        # FIXME: Struct merge isn't an OVERRIDE, so we apply the strict checks first since they'll persist
        # FIXME: can we live without specifying required fields, since the form validation will handle this?
        INCOMING_APPLICATION_REQUIREMENTS,
        OUTGOING_APPLICATION_STRUCT,
        # FIXME: should this be here? It looks like it allows users to send administrative data to the system
        # I have removed it as it was exposing incorrect data in the auto-generated documentation
        # INTERNAL_APPLICATION_STRUCT,
        _SHARED_STRUCT
    ]

    def __init__(self, raw=None, **kwargs):
        if raw is None:
            super(IncomingApplication, self).__init__(silent_prune=False, check_required_on_init=False, **kwargs)
        else:
            super(IncomingApplication, self).__init__(raw=raw, silent_prune=False, **kwargs)

    @property
    def data(self):
        return self.__seamless__.data

    def custom_validate(self):
        # only attempt to validate if this is not a blank object
        if len(list(self.__seamless__.data.keys())) == 0:
            return

        if _check_for_script(self.data):
            raise dataobj.ScriptTagFoundException(Messages.EXCEPTION_SCRIPT_TAG_FOUND)

        # extract the p/e-issn identifier objects
        pissn = self.data["bibjson"]["pissn"]
        eissn = self.data["bibjson"]["eissn"]

        # check that at least one of them appears and if they are different
        if pissn is None and eissn is None or pissn == eissn:
            raise seamless.SeamlessException("You must specify at least one of bibjson.pissn and bibjson.eissn, and they must be different")

        # normalise the ids
        if pissn is not None:
            pissn = self._normalise_issn(pissn)
        if eissn is not None:
            eissn = self._normalise_issn(eissn)

        # check they are not the same
        if pissn is not None and eissn is not None:
            if pissn == eissn:
                raise seamless.SeamlessException("Print ISSN and Online ISSN should be different")

        # A link to the journal homepage is required
        #
        if self.data["bibjson"]["ref"]["journal"] is None or self.data["bibjson"]["ref"]["journal"] == "":
            raise seamless.SeamlessException("You must specify the journal homepage in bibjson.ref.journal")

        # if plagiarism detection is done, then the url is a required field
        if self.data["bibjson"]["plagiarism"]["detection"] is True:
            url = self.data["bibjson"]["plagiarism"]["url"]
            if url is None:
                raise seamless.SeamlessException("In this context bibjson.plagiarism.url is required")

        # if licence_display is "embed", then the url is a required field   #TODO: what with "display"
        art = self.data["bibjson"]["article"]
        if "embed" in art["license_display"] or "display" in art["license_display"]:
            if art["license_display_example_url"] is None or art["license_display_example_url"] ==  "":
                raise seamless.SeamlessException("In this context bibjson.article.license_display_example_url is required")

        # if the author does not hold the copyright the url is optional, otherwise it is required
        if self.data["bibjson"]["copyright"]["author_retains"] is not False:
            if self.data["bibjson"]["copyright"]["url"] is None or self.data["bibjson"]["copyright"]["url"] == "":
                raise seamless.SeamlessException("In this context bibjson.copyright.url is required")

        # check the number of keywords is no more than 6
        if len(self.data["bibjson"]["keywords"]) > 6:
            raise seamless.SeamlessException("bibjson.keywords may only contain a maximum of 6 keywords")

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

    def to_application_model(self, existing=None):
        nd = deepcopy(self.data)

        if existing is None:
            return models.Suggestion(**nd)
        else:
            nnd = seamless.SeamlessMixin.extend_struct(self._struct, nd)
            return models.Suggestion(**nnd)

    @property
    def id(self):
        return self.__seamless__.get_single("id")

    def set_id(self, id=None):
        if id is None:
            id = self.makeid()
        self.__seamless__.set_with_struct("id", id)

    def set_created(self, date=None):
        if date is None:
            date = dates.now_str()
        self.__seamless__.set_with_struct("created_date", date)

    @property
    def created_date(self):
        return self.__seamless__.get_single("created_date")

    @property
    def created_timestamp(self):
        return self.__seamless__.get_single("created_date", coerce=coerce.to_datestamp())

    def set_last_updated(self, date=None):
        if date is None:
            date = dates.now_str()
        self.__seamless__.set_with_struct("last_updated", date)

    @property
    def last_updated(self):
        return self.__seamless__.get_single("last_updated")

    @property
    def last_updated_timestamp(self):
        return self.__seamless__.get_single("last_updated", coerce=coerce.to_datestamp())

    def set_last_manual_update(self, date=None):
        if date is None:
            date = dates.now_str()
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

    def add_note(self, note, date=None, id=None, author_id=None,):
        if date is None:
            date = dates.now_str()
        obj = {"date": date, "note": note, "id": id, "author_id": author_id}
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


class OutgoingApplication(OutgoingCommonJournalApplication):
    """
    ~~APIOutgoingApplication:Model->APIOutgoingCommonJournalApplication:Model~~
    ~~->Seamless:Library~~
    """
    __SEAMLESS_COERCE__ = dict(COERCE_MAP)
    __SEAMLESS_STRUCT__ = [
        OUTGOING_APPLICATION_STRUCT,
        _SHARED_STRUCT
    ]

    def __init__(self, raw=None, **kwargs):
        super(OutgoingApplication, self).__init__(raw, silent_prune=True, **kwargs)

    @classmethod
    def from_model(cls, application):
        assert isinstance(application, models.Suggestion)
        return super(OutgoingApplication, cls).from_model(application)

    @property
    def data(self):
        return self.__seamless__.data
