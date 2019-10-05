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
    "objects": ["admin", "bibjson", "suggestion"],

    "structs": {
        "admin" : {
            "fields" : {
                "application_status" : {"coerce" : "unicode"},   # note we don't limit this to the allowed values, as this just gives us maintenance requirements
                "owner" : {"coerce" : "unicode"},
                "current_journal" : {"coerce" : "unicode"}
            },

            "lists" : {
                "contact" : {"contains" : "object"}
            },

            "structs" : {
                "contact": {
                    "fields" : {
                        "email" : {"coerce" : "unicode"},
                        "name" : {"coerce" : "unicode"}
                    }
                }
            }
        },

        "bibjson": {
            "fields": {
                "allows_fulltext_indexing": {"coerce": "bool"},
                "alternative_title": {"coerce": "unicode"},
                "apc_url": {"coerce": "url"},
                "country": {"coerce": "country_code"},
                "institution": {"coerce": "unicode"},
                "provider": {"coerce": "unicode"},
                "publication_time": {"coerce": "integer"},
                "publisher": {"coerce": "unicode"},
                "submission_charges_url": {"coerce": "url"},
                "title": {"coerce": "unicode"},
            },
            "lists": {
                "deposit_policy": {"coerce": "deposit_policy", "contains": "field"},
                "format": {"coerce": "format", "contains": "field"},
                "identifier": {"contains": "object"},
                "keywords": {"coerce": "unicode", "contains": "field"},
                "language": {"coerce": "isolang_2letter", "contains": "field"},
                "license": {"contains": "object"},
                "link": {"contains": "object"},
                "persistent_identifier_scheme": {"coerce": "persistent_identifier_scheme", "contains": "field"},
                "subject": {"contains": "object"}
            },
            "objects": [
                "apc",
                "archiving_policy",
                "article_statistics",
                "author_copyright",
                "author_publishing_rights",
                "editorial_review",
                "oa_start",
                "plagiarism_detection",
                "submission_charges",
            ],

            "structs": {
                "apc": {
                    "fields": {
                        "currency": {"coerce": "currency_code"},
                        "average_price": {"coerce": "integer"}
                    }
                },

                "archiving_policy": {               # NOTE: this is not the same as the storage model, so beware when working with this
                    "fields": {
                        "url": {"coerce": "url"},
                    },
                    "lists": {
                        "policy": {"contains": "object"},
                    },

                    "structs" : {
                        "policy" : {
                            "fields" : {
                                "name" : {"coerce": "unicode"},
                                "domain" : {"coerce" : "unicode"}
                            }
                        }
                    }
                },

                "article_statistics": {
                    "fields": {
                        "statistics": {"coerce": "bool"},
                        "url": {"coerce": "url"},
                    }
                },

                "author_copyright": {
                    "fields": {
                        "copyright": {"coerce": "unicode"},
                        "url": {"coerce": "url"},
                    }
                },

                "author_publishing_rights": {
                    "fields": {
                        "publishing_rights": {"coerce": "unicode"},
                        "url": {"coerce": "url"},
                    }
                },

                "editorial_review": {
                    "fields": {
                        "process": {"coerce": "unicode", "allowed_values" : ["Editorial review", "Peer review", "Blind peer review", "Double blind peer review", "Open peer review", "None"]},
                        "url": {"coerce": "url"},
                    }
                },

                "identifier": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "id": {"coerce": "unicode"},
                    }
                },

                "license": {
                    "fields": {
                        "title": {"coerce": "license"},
                        "type": {"coerce": "license"},
                        "url": {"coerce": "url"},
                        "version": {"coerce": "unicode"},
                        "open_access": {"coerce": "bool"},
                        "BY": {"coerce": "bool"},
                        "NC": {"coerce": "bool"},
                        "ND": {"coerce": "bool"},
                        "SA": {"coerce": "bool"},
                        "embedded": {"coerce": "bool"},
                        "embedded_example_url": {"coerce": "url"},
                    }
                },

                "link": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "url": {"coerce": "url"},
                    }
                },

                "oa_start": {
                    "fields": {
                        "year": {"coerce": "integer"}
                    }
                },

                "plagiarism_detection": {
                    "fields": {
                        "detection": {"coerce": "bool"},
                        "url": {"coerce": "url"},
                    }
                },

                "submission_charges": {
                    "fields": {
                        "currency": {"coerce": "currency_code"},
                        "average_price": {"coerce": "integer"}
                    }
                },
                "subject": {
                    "fields": {
                        "scheme": {"coerce": "unicode"},
                        "term": {"coerce": "unicode"},
                        "code": {"coerce": "unicode"},
                    }
                }
            }
        },

        "suggestion" : {
            "fields" : {
                "article_metadata" : {"coerce" : "bool"},
                "suggested_on" : {"coerce" : "utcdatetime"}
            },
            "objects" : [
                "articles_last_year",
                "suggester"
            ],

            "structs" : {
                "articles_last_year" : {
                    "fields" : {
                        "count" : {"coerce" : "integer"},
                        "url" : {"coerce" : "url"}
                    }
                },
                "suggester" : {
                    "fields" : {
                        "name" : {"coerce" : "unicode"},
                        "email" : {"coerce" : "unicode"}
                    }
                }
            }
        },
    }
}

INCOMING_APPLICATION_REQUIREMENTS = {
    "required" : ["admin", "bibjson", "suggestion"],

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
                "allows_fulltext_indexing",
                "apc_url",
                "archiving_policy",
                "article_statistics",
                "author_copyright",
                "author_publishing_rights",
                "country",
                "deposit_policy",
                "editorial_review",
                "format",
                "identifier",
                "keywords",
                "language",
                "license",
                "link",
                "oa_start",
                "persistent_identifier_scheme",
                "plagiarism_detection",
                "publication_time",
                "publisher",
                "submission_charges_url",
                "title"
            ],

            "structs": {
                "archiving_policy": {
                    "required" : ["url", "policy"],
                    "structs" : {
                        "policy" : {
                            "required" : ["name"]
                        }
                    }
                },

                "article_statistics": {
                    "required" : ["statistics"]
                },

                "author_copyright": {
                    "required" : ["copyright"]
                },

                "author_publishing_rights": {
                    "required" : ["publishing_rights"]
                },

                "editorial_review": {
                    "required" : ["process", "url"]
                },

                "identifier": {
                    "required" : ["type", "id"]
                },

                "license": {
                    "required" : [
                        "embedded",
                        "title",
                        "type",
                        "open_access"
                    ]
                },

                "link": {
                    "required" : ["type", "url"]
                },

                "oa_start": {
                    "required" : ["year"]
                },

                "plagiarism_detection": {
                    "required" : ["detection", "url"]
                }
            }
        },

        "suggestion" : {
            "required" : ["article_metadata", "articles_last_year"],
            "structs" : {
                "articles_last_year" : {
                    "required" : ["count", "url"]
                }
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
        if len(self.data.keys()) == 0:
            return

        # at least one of print issn / e-issn, and they must be different
        #
        # check that there are identifiers at all
        identifiers = self.bibjson.identifier
        if identifiers is None or len(identifiers) == 0:
            raise dataobj.DataStructureException("You must specify at least one of P-ISSN or E-ISSN in bibjson.identifier")

        # extract the p/e-issn identifier objects
        pissn = None
        eissn = None
        for ident in identifiers:
            if ident.type == "pissn":
                pissn = ident
            elif ident.type == "eissn":
                eissn = ident

        # check that at least one of them appears
        if pissn is None and eissn is None:
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
        # check that there are links at all
        links = self.bibjson.link
        if links is None or len(links) == 0:
            raise dataobj.DataStructureException("You must specify the journal homepage in bibjson.link@type='homepage'")
        found = False
        for l in links:
            if l.type == "homepage":
                found = True
                break
        if not found:
            raise dataobj.DataStructureException("You must specify the journal homepage in bibjson.link@type='homepage'")

        # if plagiarism detection is done, then the url is a required field
        if self.bibjson.plagiarism_detection.detection is True:
            url = self.bibjson.plagiarism_detection.url
            if url is None:
                raise dataobj.DataStructureException("In this context bibjson.plagiarism_detection.url is required")

        # if licence.embedded is true, then the url is a required field
        lic = self.bibjson.license
        if lic is not None and len(lic) > 0:
            lic = lic[0]
            if lic.embedded:
                if lic.embedded_example_url is None:
                    raise dataobj.DataStructureException("In this context bibjson.license.embedded_example_url is required")

        # if the author does not hold the copyright the url is optional, otherwise it is required
        if self.bibjson.author_copyright.copyright is not False:
            if self.bibjson.author_copyright.url is None:
                raise dataobj.DataStructureException("In this context bibjson.author_copyright.url is required")

        # if the author does not hold the publishing rights the url is optional, otherwise it is required
        if self.bibjson.author_publishing_rights.publishing_rights is not False:
            if self.bibjson.author_publishing_rights.url is None:
                raise dataobj.DataStructureException("In this context bibjson.author_publishing_rights.url is required")

        # if the archiving policy has no "domain" set, then the policy must be from one of an allowed list
        # if the archiving policy does have "domain" set, then the domain must be from one of an allowed list
        for ap in self.bibjson.archiving_policy.policy:
            if ap.domain is not None:
                # domain is in allowed list
                opts = choices.Choices.digital_archiving_policy_list("optional")
                if ap.domain not in opts:
                    raise dataobj.DataStructureException("bibjson.archiving_policy.policy.domain must be one of {x}".format(x=" or ".join(opts)))
            else:
                # policy name is in allowed list
                opts = choices.Choices.digital_archiving_policy_list("named")
                if ap.name not in opts:
                    raise dataobj.DataStructureException("bibjson.archiving_policy.policy.name must be one of '{x}' when 'domain' is not also set".format(x=", ".join(opts)))

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

        # we need to re-write the archiving policy section
        ap = nd.get("bibjson", {}).get("archiving_policy")
        if ap is not None:
            nap = {}
            if "url" in ap:
                nap["url"] = ap["url"]
            if "policy" in ap:
                known = []
                for pol in ap["policy"]:
                    if "domain" in pol:
                        if pol.get("domain").lower() == "other":
                            nap["other"] = pol.get("name")
                        elif pol.get("domain").lower() == "a national library":
                            nap["nat_lib"] = pol.get("name")
                    else:
                        known.append(pol.get("name"))
                if len(known) > 0:
                    nap["known"] = known
            nd["bibjson"]["archiving_policy"] = nap

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
