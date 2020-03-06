from portality.lib import dataobj, swagger
from portality import models
from portality.formcontext import choices
from copy import deepcopy

from portality.api.v1.data_objects.common_journal_application import OutgoingCommonJournalApplication

# both incoming and outgoing applications share this struct
# "required" fields are only put on incoming applications
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
                        "url": {"coerce": "unicode"},
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
                "article": {
                    "fields": {
                        "embedded_license": {"coerce": "bool"},
                        "embedded_license_url": {"coerce": "unicode"},
                        "orcid": {"coerce": "unicode"},
                        "i4oc_open_citations": {"coerce": "unicode"}
                    }
                },
                "copyright": {
                    "fields": {
                        "author_retains": {"coerce": "bool"},
                        "url": {"coerce": "unicode"},
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
                        "review_url": {"coerce": "unicode"},
                        "board_url": {"coerce": "unicode"}
                    },
                    "lists": {
                        "review_process": {"contains" : "field", "coerce": "unicode",
                                           "allowed_values": ["Editorial review", "Peer review", "Blind peer review",
                                                              "Double blind peer review", "Open peer review", "None"]},
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
                        "type": {"coerce": "license"},
                        "url": {"coerce": "unicode"},
                        "BY": {"coerce": "bool"},
                        "NC": {"coerce": "bool"},
                        "ND": {"coerce": "bool"},
                        "SA": {"coerce": "bool"}
                    }
                },
                "other_charges": {
                    "fields": {
                        "has_other_charges": {"coerce", "bool"},
                    },
                    "lists": {
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
                        "url": {"coerce": "unicode"},
                    }
                },
                "preservation": {
                    "fields": {
                        "has_preservation": {"coerce": "unicode"},
                        "national_library": {"coerce": "unicode"},
                        "url": {"coerce": "unicode"}
                    },
                    "lists": {
                        "service": {"coerce": "unicode", "contains": "object"},
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
                        "url": {"coerce": "unicode"}
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
                "keywords",
                "language",
                "license",
                "ref",
                "pid_scheme",
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


class IncomingApplication(dataobj.DataObj, swagger.SwaggerSupport):
    def __init__(self, raw=None):
        self._add_struct(BASE_APPLICATION_STRUCT)
        self._add_struct(INCOMING_APPLICATION_REQUIREMENTS)
        super(IncomingApplication, self).__init__(raw, construct_silent_prune=False, expose_data=True)

    def custom_validate(self):
        # only attempt to validate if this is not a blank object
        if len(list(self.data.keys())) == 0:
            return


        # extract the p/e-issn identifier objects
        pissn = self.bibjson.pissn
        eissn = self.bibjson.eissn

        # check that at least one of them appears and if they are different
        if pissn is None and eissn is None or pissn == eissn:
            raise dataobj.DataStructureException("You must specify at least one of P-ISSN or E-ISSN in bibjson.identifier")

        # normalise the ids
        if pissn is not None:
            pissn.id = self._normalise_issn(pissn.id)
        if eissn is not None:
            eissn.id = self._normalise_issn(eissn.id)

        # check they are not the same
        if pissn is not None and eissn is not None:
            if pissn.id == eissn.id:
                raise dataobj.DataStructureException("P-ISSN and E-ISSN should be different")

        # A link to the journal homepage is required
        #
        if self.bibjson.ref.journal is None:
            raise dataobj.DataStructureException("You must specify the journal homepage in bibjson.link@type='homepage'")

        # if plagiarism detection is done, then the url is a required field
        if self.bibjson.plagiarism.detection is True:
            url = self.bibjson.plagiarism.url
            if url is None:
                raise dataobj.DataStructureException("In this context bibjson.plagiarism_detection.url is required")

        # if licence.embedded is true, then the url is a required field
        lic = self.bibjson.article.embedded_license
        if lic and lic.embedded_example_url is None:
            raise dataobj.DataStructureException("In this context bibjson.license.embedded_example_url is required")

        # if the author does not hold the copyright the url is optional, otherwise it is required
        if self.bibjson.copyright.author_retains is not False:
            if self.bibjson.copyright.url is None:
                raise dataobj.DataStructureException("In this context bibjson.author_copyright.url is required")


        # if the archiving policy has no "domain" set, then the policy must be from one of an allowed list
        # if the archiving policy does have "domain" set, then the domain must be from one of an allowed list
        # for ap in self.bibjson.archiving_policy.policy:
        #     if ap.domain is not None:
        #         # domain is in allowed list
        #         opts = choices.Choices.digital_archiving_policy_list("optional")
        #         if ap.domain not in opts:
        #             raise dataobj.DataStructureException("bibjson.archiving_policy.policy.domain must be one of {x}".format(x=" or ".join(opts)))
        #     else:
        #         # policy name is in allowed list
        #         opts = choices.Choices.digital_archiving_policy_list("named")
        #         if ap.name not in opts:
        #             raise dataobj.DataStructureException("bibjson.archiving_policy.policy.name must be one of '{x}' when 'domain' is not also set".format(x=", ".join(opts)))

        # check the number of keywords is no more than 6
        if len(self.bibjson.keywords) > 6:
            raise dataobj.DataStructureException("bibjson.keywords may only contain a maximum of 6 keywords")

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
            nnd = dataobj.merge_outside_construct(self._struct, nd, existing.data)
            return models.Suggestion(**nnd)

class OutgoingApplication(OutgoingCommonJournalApplication):
    def __init__(self, raw=None):
        self._add_struct(BASE_APPLICATION_STRUCT)
        super(OutgoingApplication, self).__init__(raw, construct_silent_prune=True, expose_data=True)

    @classmethod
    def from_model(cls, application):
        assert isinstance(application, models.Suggestion)
        return super(OutgoingApplication, cls).from_model(application)
