from portality.lib import swagger, seamless
from portality import models
from copy import deepcopy

from portality.api.v2.data_objects.common_journal_application import OutgoingCommonJournalApplication

# both incoming and outgoing applications share this struct
# "required" fields are only put on incoming applications
from portality.lib.coerce import COERCE_MAP
from portality.lib.seamless import SeamlessMixin

BASE_APPLICATION_STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},                # Note that we'll leave these in for ease of use by the
        "created_date": {"coerce": "utcdatetime"},  # caller, but we'll need to ignore them on the conversion
        "last_updated": {"coerce": "utcdatetime"}   # to the real object
    },
    "objects": ["admin", "bibjson"],
    "structs": {
        "admin" : {
            "fields" : {
                "application_status" : {"coerce" : "unicode"},
                "current_journal" : {"coerce" : "unicode"},
                "date_applied" : {"coerce" : "unicode"},
                "owner" : {"coerce" : "unicode"}
            },
            "objects" : [
                "applicant",
                "contact",
            ],
            "structs" : {
                "applicant" : {
                    "fields" : {
                        "name" : {"coerce" : "unicode"},
                        "email": {"coerce" : "unicode"}
                    }
                },
                "contact": {
                    "fields" : {
                        "name" : {"coerce" : "unicode"},
                        "email": {"coerce" : "unicode"}
                    }
                }
            }
        },
        "bibjson": {
            "fields": {
                "alternative_title": {"coerce": "unicode"},
                "boai": {"coerce": "bool"},
                "eissn":{"coerce": "unicode"},
                "pissn": {"coerce": "unicode"},
                "publication_time_weeks": {"coerce": "integer"},
                "title": {"coerce": "unicode"}
            },
            "lists": {
                "is_replaced_by" : {"coerce" : "issn", "contains" : "field"},
                "keywords": {"coerce": "unicode", "contains": "field"},
                "language": {"coerce": "isolang_2letter", "contains": "field"},
                "license": {"contains" : "object"},
                "subject": {"contains": "object"}
            },
            "objects": [
                "apc",
                "article",
                "copyright",
                "deposit_policy",
                "editorial",
                "institution",
                "other_charges",
                "pid_scheme",
                "plagiarism",
                "preservation",
                "publisher",
                "ref",
                "waiver"
            ],
            "structs": {
                "apc": {
                    "fields": {
                        "url": {"coerce": "url"},
                        "has_apc": {"coerce": "unicode"}
                    },
                    "lists": {
                        "max": {"contains": "object"}
                    },
                    "structs": {
                        "max": {
                            "fields": {
                                "currency": {"coerce": "unicode"},
                                "price": {"coerce": "integer"}
                            }
                        }
                    }
                },
                "article" : {
                    "fields" : {
                        "license_display_example_url" : {"coerce" : "url"},
                        "orcid" : {"coerce" : "bool"},
                        "i4oc_open_citations" : {"coerce" : "bool"}
                    },
                    "lists" : {
                        "license_display" : {"contains" : "field", "coerce" : "unicode", "allowed_values" : ["embed", "display", "no"]},
                    }
                },
                "copyright": {
                    "fields": {
                        "author_retains": {"coerce": "bool"},
                        "url": {"coerce": "url"},
                    }
                },
                "deposit_policy": {
                    "fields": {
                        "has_policy": {"coerce": "bool"},
                        "is_registered": {"coerce": "bool"}
                    },
                    "lists": {
                        "service": {"coerce": "unicode", "contains": "field"}
                    }
                },
                "editorial": {
                    "fields": {
                        "review_url": {"coerce": "url"},
                        "board_url": {"coerce": "unicode"}
                    },
                    "lists": {
                        "review_process": {"contains" : "field", "coerce": "unicode",
                                           #"allowed_values": ["Editorial review", "Peer review", "Blind peer review",
                                           #                   "Double blind peer review", "Open peer review", "None"]
                                           },
                    }
                },
                "institution": {
                    "fields": {
                        "name": {"coerce": "unicode"},
                        "country": {"coerce": "unicode"}
                    }
                },
                "license": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "url": {"coerce": "url"},
                        "BY": {"coerce": "bool"},
                        "NC": {"coerce": "bool"},
                        "ND": {"coerce": "bool"},
                        "SA": {"coerce": "bool"}
                    }
                },
                "other_charges": {
                    "fields": {
                        "has_other_charges": {"coerce": "bool"},
                        "url": {"coerce": "unicode"}
                    }
                },
                "pid_scheme": {
                    "fields": {
                        "has_pid_scheme": {"coerce": "bool"},
                        "scheme": {"coerce": "unicode"}
                    }
                },
                "plagiarism": {
                    "fields": {
                        "detection": {"coerce": "bool"},
                        "url": {"coerce": "url"},
                    }
                },
                "preservation": {
                    "fields": {
                        "has_preservation": {"coerce": "unicode"},
                        "national_library": {"coerce": "unicode"},
                        "url": {"coerce": "url"}
                    },
                    "lists": {
                        "service": {"coerce": "unicode", "contains": "field"},
                    }
                },
                "publisher": {
                    "fields": {
                        "name": {"coerce": "unicode"},
                        "country": {"coerce": "unicode"}
                    }
                },
                "ref": {
                    "fields": {
                        "license_terms": {"coerce": "unicode"},
                        "oa_statement": {"coerce": "unicode"},
                        "journal": {"coerce": "unicode"},
                        "aims_scope": {"coerce": "unicode"},
                        "author_instructions": {"coerce": "unicode"}

                    }
                },
                "subject": {
                    "fields": {
                        "code": {"coerce": "unicode"},
                        "scheme": {"coerce": "unicode"},
                        "term": {"coerce": "unicode"}
                    }
                },
                "waiver": {
                    "fields": {
                        "has_waiver": {"coerce": "unicode"},
                        "url": {"coerce": "url"}
                    }
                }
            }
        }
    }
}

INCOMING_APPLICATION_REQUIREMENTS = {
    "required" : ["admin", "bibjson"],

    "structs": {
        "admin" : {
            "required" : ["contact"],
            "structs" : {
                "contact": {
                    "required" : ["name", "email"]
                }
            }
        },

        "bibjson": {
            "required": [
                "apc",
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
                "ref",
                "other_charges",
                "waiver",
                "title"
            ],
            "structs": {
                "apc": {
                    "required" : ["has_apc"]
                },
                "copyright": {
                    "required" : ["url"]
                },
                "deposit_policy": {
                    "required" : ["has_policy"]
                },
                "editorial": {
                    "required" : ["review_process", "review_url"]
                },
                "pid_scheme": {
                    "required" : ["has_pid_scheme"]
                },
                "plagiarism": {
                    "required": ["detection","url"]
                },
                "preservation": {
                    "required": ["has_preservation"]
                },
                "publisher": {
                    "required": ["name"]
                },
                "ref": {
                    "required" : ["journal"]
                },
                "other_charges": {
                    "required": ["has_other_charges"]
                },
                "waiver": {
                    "requred": ["has_waiver"]
                },
            }
        }
    }
}


class IncomingApplication(SeamlessMixin, swagger.SwaggerSupport):
    __type__ = "application"
    __SEAMLESS_COERCE__ = COERCE_MAP
    __SEAMLESS_STRUCT__ = [
        BASE_APPLICATION_STRUCT,
        INCOMING_APPLICATION_REQUIREMENTS
    ]

    def __init__(self, raw=None, **kwargs):
        if raw is None:
            super(IncomingApplication, self).__init__(silent_prune=False, check_required_on_init=False)
        else:
            super(IncomingApplication, self).__init__(raw=raw, silent_prune=False, **kwargs)

    @property
    def data(self):
        return self.__seamless__.data

    def custom_validate(self):
        # only attempt to validate if this is not a blank object
        if len(list(self.__seamless__.data.keys())) == 0:
            return


        # extract the p/e-issn identifier objects
        pissn = self.data["bibjson"]["pissn"]
        eissn = self.data["bibjson"]["eissn"]

        # check that at least one of them appears and if they are different
        if pissn is None and eissn is None or pissn == eissn:
            raise seamless.SeamlessException("You must specify at least one of P-ISSN or E-ISSN in bibjson.identifier")

        # normalise the ids
        if pissn is not None:
            pissn = self._normalise_issn(pissn)
        if eissn is not None:
            eissn = self._normalise_issn(eissn)

        # check they are not the same
        if pissn is not None and eissn is not None:
            if pissn == eissn:
                raise seamless.SeamlessException("P-ISSN and E-ISSN should be different")

        # A link to the journal homepage is required
        #
        if self.data["bibjson"]["ref"]["journal"] is None or self.data["bibjson"]["ref"]["journal"] == "":
            raise seamless.SeamlessException("You must specify the journal homepage in bibjson.link@type='homepage'")

        # if plagiarism detection is done, then the url is a required field
        if self.data["bibjson"]["plagiarism"]["detection"] is True:
            url = self.data["bibjson"]["plagiarism"]["url"]
            if url is None:
                raise seamless.SeamlessException("In this context bibjson.plagiarism_detection.url is required")

        # if licence_display is "embed", then the url is a required field   #TODO: what with "display"
        art = self.data["bibjson"]["article"]
        if "embed" in art["license_display"] or "display" in art["license_display"]:
            if art["license_display_example_url"] is None or art["license_display_example_url"] ==  "":
                raise seamless.SeamlessException("In this context bibjson.license.license_display_example_url is required")

        # if the author does not hold the copyright the url is optional, otherwise it is required
        if self.data["bibjson"]["copyright"]["author_retains"] is not False:
            if self.data["bibjson"]["copyright"]["url"] is None or self.data["bibjson"]["copyright"]["url"] == "":
                raise seamless.SeamlessException("In this context bibjson.author_copyright.url is required")

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
            #nnd = dataobj.merge_outside_construct(self._struct, nd, existing.data)
            nnd = seamless.SeamlessMixin.extend_struct(self._struct, nd)
            return models.Suggestion(**nnd)

class OutgoingApplication(OutgoingCommonJournalApplication):

    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, raw=None):
        super(OutgoingApplication, self).__init__(raw, struct=BASE_APPLICATION_STRUCT, construct_silent_prune=True)

    @classmethod
    def from_model(cls, application):
        assert isinstance(application, models.Suggestion)
        return super(OutgoingApplication, cls).from_model(application)
