from copy import deepcopy
from portality.lib.formulaic import Formulaic, WTFormsBuilder

from wtforms import StringField, IntegerField, BooleanField, RadioField, SelectMultipleField, SelectField, Form, FormField, FieldList
from wtforms import widgets, validators
from wtforms.widgets.core import html_params, HTMLString

from portality.formcontext.fields import TagListField
from portality.crosswalks.application_form import ApplicationFormXWalk
from portality.forms import application_processors
from portality.forms.validate import (
    URLOptionalScheme,
    OptionalIf,
    ExclusiveCheckbox,
    ExtraFieldRequiredIf,
    MaxLen,
    RegexpOnTagList,
    ReservedUsernames,
    StopWords,
    ISSNInPublicDOAJ,
    JournalURLInPublicDOAJ,
    DifferentTo,
    RequiredIfOtherValue
)

from portality.datasets import language_options, country_options, currency_options
from portality.regex import ISSN, ISSN_COMPILED

# Stop words used in the keywords field
STOP_WORDS = [
    "open access",
    "high quality",
    "peer-reviewed",
    "peer-review",
    "peer review",
    "quality",
    "multidisciplinary",
    "interdisciplinary",
    "journal",
    "scholarly journal",
    "open science",
    "impact factor",
    "scholarly",
    "research journal"
]

########################################################
# Define all our individual fields
########################################################

class FieldDefinitions:
    BOAI = {
        "name": "boai",
        "label": "DOAJ adheres to the BOAI [definition of open access LINK].  This means that users are"
                 "permitted 'to read, download, copy, distribute, print, search, or link to the full texts of articles,"
                 "or use them for any other lawful purpose, without financial, legal, or technical barriers other than"
                 "those inseparable from gaining access to the internet itself.' Does the journal adhere to this"
                 "definition of open access?",
        "input": "checkbox",
        "help": {
            "doaj_criteria": "You must answer 'Yes'"
        },
        "validate": [
            {"required": {"message": "You must check this box to continue"}}
        ],
        "contexts": {
            "editor": {
                "disabled": True
            },
            "associate_editor": {
                "disabled": True
            }
        },
        "asynchronous_warnings": [
            {"value_must_be": {"value": "y"}}
        ]
    }

    OA_STATEMENT_URL = {
        "name": "oa_statement_url",
        "label": "Link to the journal's open access statement",
        "input": "text",
        "help": {
            "long_help": "Here is an example of a suitable Open Access statement that meets our criteria: "
                         "This is an open access journal which means that all content is freely available without charge"
                         "to the user or his/her institution. Users are allowed to read, download, copy, distribute,"
                         "print, search, or link to the full texts of the articles, or use them for any other lawful"
                         "purpose, without asking prior permission from the publisher or the author. This is in accordance"
                         "with the BOAI definition of open access.",
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            "required",
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ],
        "attr": {
            "type": "url"
        }
    }

    TITLE = {
        "name": "title",
        "label": "Journal title",
        "input": "text",
        "help": {
            "long_help": "The journal title must match what is displayed on the website and what is registered at the "
                         "ISSN Portal (https://portal.issn.org/).  For translated titles, you may add the "
                         "translation as an alternative title.",
            "doaj_criteria": "Title in application form, title at ISSN and website must all match"
        },
        "validate": [
            "required"
        ],
        "contexts": {
            "editor": {
                "disabled": True
            },
            "associate_editor": {
                "disabled": True
            },
            "update_request": {
                "disabled": True
            }
        }
    }

    ALTERNATIVE_TITLE = {
        "name": "alternative_title",
        "label": "Alternative title (including translation of the title)",
        "input": "text",
        "help": {
            "long_help": "The journal title must match what is displayed on the website and what is registered at the "
                         "ISSN Portal (https://portal.issn.org/).  For translated titles, you may add the "
                         "translation as an alternative title.",
        },
        "validate": [
            "required"
        ],
        "contexts": {
            "editor": {
                "disabled": True
            },
            "associate_editor": {
                "disabled": True
            }
        }
    }

    JOURNAL_URL = {
        "name": "journal_url",
        "label": "Link to the journal's homepage",
        "input": "text",
        "validate": [
            "required",
            "is_url",
            "journal_url_in_public_doaj"  # Check whether the journal url is already in a public DOAJ record
        ],
        "widgets": [
            "clickable_url"
        ],
        "contexts": {
            "editor": {
                "disabled": True
            },
            "associate_editor": {
                "disabled": True
            }
        },
        "asynchronous_warnings": [
            "journal_url_in_public_doaj",  # Check whether the journal url is already in a public DOAJ record
            {"rejected_application": {"age": "6 months"}},
            # check that the journal does not have a rejection less than 6 months ago
            "active_application"  # Check that the URL is not related to an active application
        ]
    }

    PISSN = {
        "name": "pissn",
        "input": "text",
        "help": {
            "long_help": "Must be a valid ISSN, fully registered and confirmed at the ISSN Portal (https://portal.issn.org/)"
                         "The ISSN must match what is given on the journal website.",
            "doaj_criteria": "ISSN must be provided"
        },
        "validate": [
            {"optional_if": {"field": "eissn",
                             "message": "You must provide one or both of an online ISSN or a print ISSN"}},
            {"is_issn": {"message": "This is not a valid ISSN"}},
            {"different_to": {"field": "eissn", "message" : "This field must contain a different value to 'ISSN (online)'"}},
            "issn_in_public_doaj"
        ],
        "contexts": {
            "editor": {
                "disabled": True
            },
            "associate_editor": {
                "disabled": True
            },
            "update_request": {
                "disabled": True
            }
        },
        "asynchronous_warnings": [
            "issn_in_public_doaj",  # check whether the journal url is already in a public DOAJ record
            {"rejected_application": {"age": "6 months"}},
            "active_application"  # Check that the ISSN is not related to an active application
        ]
    }

    EISSN = {
        "name": "eissn",
        "label": "ISSN (online)",
        "input": "text",
        "help": {
            "long_help": "Must be a valid ISSN, fully registered and confirmed at the ISSN Portal (https://portal.issn.org/)"
                         "The ISSN must match what is given on the journal website.",
            "doaj_criteria": "ISSN must be provided"
        },
        "validate": [
            {"optional_if": {"field": "pissn",
                             "message": "You must provide one or both of an online ISSN or a print ISSN"}},
            {"is_issn": {"message": "This is not a valid ISSN"}},
            {"different_to": {"field": "pissn", "message" : "This field must contain a different value to 'ISSN (print)'"}},
            "issn_in_public_doaj"
        ],
        "contexts": {
            "editor": {
                "disabled": True
            },
            "associate_editor": {
                "disabled": True
            },
            "update_request": {
                "disabled": True
            }
        },
        "asynchronous_warnings": [
            "issn_in_public_doaj",  # check whether the journal url is already in a public DOAJ record
            {"rejected_application": {"age": "6 months"}},
            "active_application"  # Check that the ISSN is not related to an active application
        ]
    }

    KEYWORDS = {
        "name": "keywords",
        "label": "Up to six subject keywords in English",
        "input": "taglist",
        "help": {
            "long_help": "Only 6 keywords are allowed. Choose words that describe the subject matter of the journal "
                         "and not the journal's qualities. Keywords must be in English and separated by a comma.",
        },
        "validate": [
            "required",
            {"stop_words": {"disallowed": STOP_WORDS}},
            {"max_tags": {"max": 6}}
        ],
        "postprocessing": [
            "to_lower"  # FIXME: this might just be a feature of the crosswalk
        ],
        "widgets": [
            {
                "taglist": {
                    "maximumSelectionSize": 6,
                    "stopWords": STOP_WORDS
                }
            }
        ],
        "attr": {
            "class": "input-xlarge"
        },
        "contexts": {
            "editor": {
                "disabled": True
            },
            "associate_editor": {
                "disabled": True
            }
        }
    }

    LANGUAGE = {
        "name": "language",
        "label": "Languages in which the journal accepts manuscripts",
        "input": "select",
        "multiple": True,
        "options_fn": "iso_language_list",
        "validate": [
            "required"
        ],
        "widgets": [
            {"select": {}}
        ],
        "attr": {
            "class": "input-xlarge"
        }
    }

    PUBLISHER = {
        "name": "publisher",
        "label": "Publisher",
        "input": "group",
        "subfields": [
            "publisher_name",
            "publisher_country"
        ]
    }

    PUBLISHER_NAME = {
        "subfield": True,
        "group": "publisher",
        "name": "publisher_name",
        "label": "Name",
        "input": "text",
        "validate": [
            "required"
        ],
        "widgets": [
            {"autocomplete": {"field": "publisher_name"}}
        ]
    }

    PUBLISHER_COUNTRY = {
        "subfield": True,
        "group": "publisher",
        "name": "publisher_country",
        "label": "Country",
        "input": "select",
        "default" : "",
        "options_fn": "iso_country_list",
        "help": {
            "long_help": "The country where the publisher carries out its business operations and is registered.",
            "doaj_criteria": "You must provide a publisher country"
        },
        "validate": [
            "required"
        ],
        "widgets": [
            {"select": {}}
        ],
        "attr": {
            "class": "input-xlarge"
        },
        "contexts": {
            "editor": {
                "disabled": True
            },
            "associate_editor": {
                "disabled": True
            }
        }
    }

    INSTITUTION = {
        "name": "institution",
        "label": "Society or institution, if applicable",
        "input": "group",
        "subfields": [
            "institution_name",
            "institution_country"
        ]
    }

    INSTITUTION_NAME = {
        "subfield": True,
        "group": "institution",
        "name": "institution_name",
        "label": "Name",
        "input": "text",
        "widgets": [
            {"autocomplete": {"field": "institution_name"}}
        ]
    }

    INSTITUTION_COUNTRY = {
        "subfield": True,
        "group": "institution",
        "name": "institution_country",
        "label": "Country",
        "input": "select",
        "default" : "",
        "options_fn": "iso_country_list",
        "help": {
            "short_help": "The society or institution responsible for the journal",
            "long_help": "Some societies or institutions are linked to a journal in some way but are not responsible "
                         "for publishing it. The publisher can be a separate organisation. If your journal is linked to "
                         "a society or other type of institution, enter that here."
        },
        "widgets": [
            {"select": {}}
        ],
        "attr": {
            "class": "input-xlarge"
        },
        "contexts": {
            "editor": {
                "disabled": True
            },
            "associate_editor": {
                "disabled": True
            }
        }
    }

    LICENSE = {
        "name": "license",
        "label": "License(s) permitted by the journal",
        "input": "checkbox",
        "multiple": True,
        "options": [
            {"display": "CC BY", "value": "CC BY"},
            {"display": "CC BY-SA", "value": "CC BY-SA"},
            {"display": "CC BY-ND", "value": "CC BY-ND"},
            {"display": "CC BY-NC", "value": "CC BY-NC"},
            {"display": "CC BY-NC-SA", "value": "CC BY-NC-SA"},
            {"display": "CC BY-NC-ND", "value": "CC BY-NC-ND"},
            {"display": "CC0", "value": "CC0"},
            {"display": "Public domain", "value": "Public domain"},
            {"display": "Publisher's own license", "value": "Publisher's own license", "exclusive": True},
        ],
        "help": {
            "long_help": "The journal must use some form of licensing to be considered for indexing in DOAJ. "
                         "If Creative Commons licensing is not used, then select 'Publisher's own license' and enter "
                         "more details below.",
            "doaj_criteria": "Content must be licenced",
            "seal_criteria": "Yes: CC BY, CC BY-SA, CC BY-NC"
        },
        "validate": [
            "required"
        ]
    }

    LICENSE_ATTRIBUTES = {
        "name": "license_attributes",
        "label": "Select all the attributes that your license has",
        "input": "checkbox",
        "multiple": True,
        "conditional": [
            {"field": "license", "value": "Publisher's own license"}
        ],
        "options": [
            {"display": "Attribution", "value": "BY"},
            {"display": "Share Alike", "value": "SA"},
            {"display": "No Derivatives", "value": "ND"},
            {"display": "No Commercial Usage", "value": "NC"}
        ],
        "help": {
            "doaj_criteria": "Content must be licenced"
        }
    }

    LICENSE_TERMS_URL = {
        "name": "license_terms_url",
        "label": "Link to the page where the license terms are stated",
        "input": "text",
        "validate": [
            "required",
            "is_url"
        ],
        "help": {
            "doaj_criteria": "You must provide a link to your license terms"
        },
        "widgets": [
            "clickable_url"
        ]
    }

    LICENSE_DISPLAY = {
        "name": "license_display",
        "label": "Does the journal embed and/or display licensing information in its articles?",
        "input": "checkbox",
        "multiple": True,
        "help": {
            "long_help": "Licensing information must be displayed or embedded on every PDF or in the full text of the "
                         "HTML articles. We do not accept licensing information that is only displayed in other parts of "
                         "the site.",
            "seal_criteria": "If the answer is Embed"
        },
        "options": [
            {"display": "Embed", "value": "Embed"},
            {"display": "Display", "value": "Display"},
            {"display": "No", "value": "No", "exclusive": True}
        ],
        "validate": [
            "required"
        ]
    }

    LICENSE_DISPLAY_EXAMPLE_URL = {
        "name": "license_display_example_url",
        "label": "Link to a recent article displaying or embedding a license in the full text",
        "input": "text",
        "validate": [
            "required",
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    COPYRIGHT_AUTHOR_RETAINS = {
        "name": "copyright_author_retains",
        "label": "For all the licenses you have indicated above, do authors or their institutions retain the copyright "
                 "and full publishing rights without restrictions?",
        "input": "checkbox",
        "validate": [
            "required"
        ],
        "help": {
            "seal_criteria": "The author must retain the copyright"
        },
        "asynchronous_warnings": [
            {"required_value": {"value": "y"}}
        ]
    }

    COPYRIGHT_URL = {
        "name": "copyright_url",
        "label": "Link to the journal's copyright terms",
        "input": "text",
        "validate": [
            "required",
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    REVIEW_PROCESS = {
        "name": "review_process",
        "label": "DOAJ only accepts peer-reviewed journals."
                 "Which type(s) of peer review does this journal use?",
        "input": "checkbox",
        "multiple": True,
        "options": [
            {"display": "Editorial review", "value": "Editorial review"},
            {"display": "Peer review", "value": "Peer review"},
            {"display": "Blind peer review", "value": "Blind peer review"},
            {"display": "Double blind peer review", "value": "Double blind peer review"},
            {"display": "Post-publication peer review", "value": "Post-publication peer review"},
            {"display": "Open peer review", "value": "Open peer review"},
            {"display": "Other", "value": "other", "subfields": ["review_process_other"]}
        ],
        "help": {
            "doaj_criteria": "Peer review must be carried out"
        },
        "validate": [
            "required"
        ]
    }

    REVIEW_PROCESS_OTHER = {
        "name": "review_process_other",
        "subfield": True,
        "label": "Other",
        "input": "text",
        "help": {
            "placeholder": "Other peer review"
        },
        "conditional": [{"field": "review_process", "value": "other"}],
        "validate": [
            {"required_if": {"field": "review_process", "value": "other"}}
        ],
        "asynchronous_warning": [
            {"warn_on_value": {"value": "None"}}
        ]
    }

    REVIEW_URL = {
        "name": "review_url",
        "label": "Link to the journal's peer review policy",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            "required",
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    PLAGIARISM_DETECTION = {
        "name": "plagiarism_detection",
        "label": "Does the journal routinely screen article submissions for plagiarism?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y"},
            {"display": "No", "value": "n"}
        ],
        "validate": [
            "required"
        ]
    }

    PLAGIARISM_URL = {
        "name": "plagiarism_url",
        "label": "Link to the journal's plagiarism policy",
        "input": "text",
        "conditional": [{"field": "plagiarism_detection", "value": "y"}],
        "help": {
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            {"required_if": {"field": "plagiarism_detection", "value": "y"}},
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    AIMS_SCOPE_URL = {
        "name": "aims_scope_url",
        "label": "Link to the journal's Aims & Scope",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            "required",
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    EDITORIAL_BOARD_URL = {
        "name": "editorial_board_url",
        "label": "Link to the journal's editorial board",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            "required",
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    AUTHOR_INSTRUCTIONS_URL = {
        "name": "author_instructions_url",
        "label": "Link to the journal's Instructions for Author",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            "required",
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    PUBLICATION_TIME_WEEKS = {
        "name": "publication_time_weeks",
        "label": "Average number of <strong>weeks</strong> between article submission & publication",
        "input": "number",
        "datatype": "integer",
        "validate": [
            "required",
            {"int_range": {"gte": 1, "lte": 52}}
        ],
        "asynchronous_warning": [
            {"int_range": {"lte": 2}}
        ],
        "attr": {
            "min": "1",
            "max": "100"
        }
    }

    APC = {
        "name": "apc",
        "label": "Does the journal require payment of article processing charges (APCs)?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y"},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "doaj_criteria": "You must tell us about any APCs"
        },
        "validate": [
            "required"
        ]
    }

    APC_URL = {
        "name": "apc_url",
        "label": "Link to the page where this is stated",
        "input": "text",
        "help": {
            "short_help": "The page must declare whether or not APCs are charged.",
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            "required",
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    APC_CHARGES = {
        "name": "apc_charges",
        "input": "group",
        "repeatable" : {
            "initial" : 5
        },
        "help": {
            "long_help": "If the journal charges different APCs, you must enter the highest APC charged. If more than "
                         "one currency is used, add a new line"
        },
        "conditional": [
            {"field": "apc", "value": "y"}
        ],
        "subfields": [
            "apc_currency",
            "apc_max"
        ],
        "template" : "application_form/_list.html",
        "entry_template" : "application_form/_entry_group_horizontal.html"
    }

    APC_CURRENCY = {
        "subfield": True,
        "group": "apc_charges",
        "name": "apc_currency",
        "input": "select",
        "options_fn": "iso_currency_list",
        "default" : "",
        "widgets": [
            {"select": {}}
        ],
        "attr": {
            "class": "input-xlarge"
        }
    }

    APC_MAX = {
        "subfield": True,
        "group": "apc_charges",
        "name": "apc_max",
        "label": "Highest APC Charged",
        "input": "number",
        "datatype": "integer",
        "help" : {
            "placeholder" : "Highest APC Charged"
        }
    }

    HAS_WAIVER = {
        "name": "has_waiver",
        "label": "Does the journal provide APC waivers or discounts for authors?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y"},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": "Answer Yes if the journal provides APC waivers for authors from low-income economies, "
                         "discounts for authors from lower middle-income economies, and/or waivers and discounts for "
                         "other authors with demonstrable needs. "
        },
        "validate": [
            "required"
        ]
    }

    WAIVER_URL = {
        "name": "waiver_url",
        "label": "Link to the journal's waiver information",
        "input": "text",
        "conditional": [
            {"field": "has_waiver", "value": "y"}
        ],
        "help": {
            "short_help": "The page must declare whether or not APCs are charged.",
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            {"required_if": {"field": "has_waiver", "value": "y"}},
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    HAS_OTHER_CHARGES = {
        "name": "has_other_charges",
        "label": "Does the journal charge any other fees to authors?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y"},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": "Declare all other charges: editorial processing charges, colour charges, submission fees, "
                         "page charges, membership fees, print subscription costs, other supplementary charges",
            "doaj_criteria": "You must declare any other charges if they exist"
        },
        "validate": [
            "required"
        ]
    }

    OTHER_CHARGES_URL = {
        "name": "other_charges_url",
        "label": "Link to the journal's fees information",
        "input": "text",
        "conditional": [
            {"field": "has_other_charges", "value": "y"}
        ],
        "help": {
            "short_help": "The page must declare whether or not APCs are charged.",
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            {"required_if": {"field": "has_other_charges", "value": "y"}},
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    PRESERVATION_SERVICE = {
        "name": "preservation_service",
        "label": "Long-term preservation service(s) with which the journal is currently archived",
        "input": "checkbox",
        "multiple": True,
        "options": [
            {"display": "CINES", "value": "CINES"},
            {"display": "CLOCKSS", "value": "CLOCKSS"},
            {"display": "LOCKSS", "value": "LOCKSS"},
            {"display": "Internet Archive", "value": "Internet Archive"},
            {"display": "PKP PN", "value": "PKP PN"},
            {"display": "PubMed Central (PMC)", "value": "PMC"},
            {"display": "Portico", "value": "Portico"},
            {"display": "A national library", "value": "national_library", "subfields": ["preservation_service_library"]},
            {"display": "The journal content isn't archived with a long-term preservation service",
             "value": "none", "exclusive": True},
            {"display": "Other", "value": "other", "subfields": ["preservation_service_other"]}
        ],
        "help": {
            "short_help": "Select at least one",
            "long_help": "Only active archiving is accepted; content must be actively deposited in each of the options "
                         "you choose. If the journal is registered with a service but archiving is not yet active, "
                         "choose 'No'.\n\nPubMed Central covers PMC U.S.A., PMC Canada, and PMC Europe (Wellcome Trust)."
        },
        "validate": [
            "required"
        ]
    }

    PRESERVATION_SERVICE_LIBRARY = {
        "name": "preservation_service_library",
        "subfield": True,
        "label": "A national library",
        "input": "text",
        "repeatable" : {
            "initial" : 2
        },
        "help": {
            "placeholder": "A national library"
        },
        "conditional": [{"field": "preservation_service", "value": "national_library"}],
        "validate": [
            {"required_if": {"field": "preservation_service", "value": "national_library"}}
        ],
        "asynchronous_warning": [
            {"warn_on_value": {"value": "None"}}
        ]
    }

    PRESERVATION_SERVICE_OTHER = {
        "name": "preservation_service_other",
        "subfield": True,
        "label": "Other",
        "input": "text",
        "help": {
            "placeholder": "Other archiving policy"
        },
        "conditional": [{"field": "preservation_service", "value": "other"}],
        "validate": [
            {"required_if": {"field": "preservation_service", "value": "other"}}
        ],
        "asynchronous_warning": [
            {"warn_on_value": {"value": "None"}}
        ]
    }

    PRESERVATION_SERVICE_URL = {
        "name": "preservation_service_url",
        "label": "Link to the preservation and archiving information on the journal's site",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            {"optional_if": {"field": "preservation_service", "values": ["none"]}},
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    DEPOSIT_POLICY = {
        "name": "deposit_policy",
        "label": "Where is the journal's policy allowing authors to deposit the AAM or VOR registered?",
        "input": "checkbox",
        "multiple": True,
        "options": [
            {"display": "Sherpa/Romeo", "value": "Sherpa/Romeo"},
            {"display": "Dulcinea", "value": "Dulcinea"},
            {"display": "Héloïse", "value": "Héloïse"},
            {"display": "Diadorim", "value": "Diadorim"},
            {"display": "The journal has a policy but it isn't registered anywhere", "value": "Unregistered", "exclusive" : True},
            {"display": "The journal has no repository policy", "value": "none", "exclusive": True},
            {"display": "Other", "value": "other", "subfields": ["deposit_policy_other"]}
        ],
        "help": {
            "short_help": "Select at least one",
            "long_help": "AAM stands for Author Accepted Manuscript. VOR is the Version of Record.\n\n"
                         "This questions ask whether or not the journal allows authors to deposit a copy of their "
                         "work in an institutional repository.\n\n If the journal allows authors to do this, "
                         "is that policy registered in a policy directory?"
        },
        "validate": [
            "required"
        ]
    }

    DEPOSIT_POLICY_OTHER = {
        "name": "deposit_policy_other",
        "subfield": True,
        "label": "Other",
        "input": "text",
        "help": {
            "placeholder": "Other repository policy"
        },
        "conditional": [{"field": "deposit_policy", "value": "other"}],
        "validate": [
            {"required_if": {"field": "deposit_policy", "value": "other"}}
        ],
        "asynchronous_warning": [
            {"warn_on_value": {"value": "None"}}
        ]
    }

    DEPOSIT_POLICY_URL = {
        "name": "deposit_policy_url",
        "label": "Link to the policy on the journal's site",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            {"required_if": {"field": "deposit_policy", "value": "unregistered"}},
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    PERSISTENT_IDENTIFIERS = {
        "name": "persistent_identifiers",
        "label": "Persistent article identifiers used by the journal",
        "input": "checkbox",
        "multiple": True,
        "options": [
            {"display": "DOIs", "value": "DOI"},
            {"display": "ARKs", "value": "ARK"},
            {"display": "Handles", "value": "Handles"},
            {"display": "PURLs", "value": "PURL"},
            {"display": "The journal does not use persistent article identifiers", "value": "none", "exclusive": True},
            {"display": "Other", "value": "other", "subfields": ["persistent_identifiers_other"]}
        ],
        "help": {
            "short_help": "Select at least one",
            "long_help": "A persistent article identifier (PID) is used to find the article no matter where it is "
                         "located. The most common type of PID is the digital object identifier (DOI). "
                         "Read more about PIDs. [Link https://en.wikipedia.org/wiki/Persistent_identifier]"
        },
        "validate": [
            "required"
        ]
    }

    PERSISTENT_IDENTIFIERS_OTHER = {
        "name": "persistent_identifiers_other",
        "subfield": True,
        # "label": "Other",
        "input": "text",
        "help": {
            "placeholder": "Other persistent identifier"
        },
        "conditional": [{"field": "persistent_identifiers", "value": "other"}],
        "validate": [
            {"required_if": {"field": "persistent_identifiers", "value": "other"}}
        ],
        "asynchronous_warning": [
            {"warn_on_value": {"value": "None"}}
        ]
    }

    ORCID_IDS = {
        "name": "orcid_ids",
        "label": "Does the journal allow for ORCID iDs to be present in article metadata?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y"},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": "An ORCID (Open Researcher and Contributor) iD is an alphanumeric code to uniquely identify "
                         "authors. [link https://orcid.org/]",
        },
        "validate": [
            "required"
        ]
    }

    OPEN_CITATIONS = {
        "name": "open_citations",
        "label": "Does the journal comply with I4OC standards for open citations?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y"},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": "The I4OC standards ask that citations are structured, separable, and open. "
                         "https://i4oc.org/#goals",
        },
        "validate": [
            "required"
        ]
    }

    #######################################
    ## Ediorial fields

    DOAJ_SEAL = {
        "name": "doaj_seal",
        "label": "The journal has fulfilled all the criteria for the Seal. Award the Seal?",
        "input": "checkbox",
        "validate": [
            {
                "only_if" : {"fields" : [
                    {"field" : "license_display", "value" : "Embed"},
                    {"field" : "copyright_author_retains", "value" : "y"},
                    {"field" : "preservation_service", "not" : "none"},
                    {"field" : "preservation_service_url", "not" : ""},
                    {"field" : "deposit_policy", "not" : "none"},
                    {"field" : "persistent_identifiers", "value" : "DOI"}
                ]}
            }
        ]
    }

    DOAJ_QUICK_REJECT = {
        "name": "doaj_quick_reject",
        "label": "Select the reason for rejection",
        "input": "select",
        "options_fn": "quick_reject"
    }

    DOAJ_QUICK_REJECT_DETAILS = {
        "name": "doaj_quick_reject_details",
        "label": "Enter additional information to be sent to the publisher",
        "input": "text",
        "help": {
            "long_help": "The selected reason for rejection, and any additional information you include, "
                         "are sent to the journal contact with the rejection email."
        },
        "validate": [
            {"required_if": {"field": "doaj_quick_reject", "value": "other"}}
        ],
    }

    DOAJ_OWNER = {
        "name": "doaj_owner",
        "label": "DOAJ Account",
        "input": "text",
        "validate": [
            {"required" : {"message" : "You must confirm the account id"}}
        ],
        "widgets": [
            {"autocomplete": {"field": "account"}}
        ]
    }

    DOAJ_STATUS = {
        "name": "doaj_status",
        "label": "Select status",
        "input": "select",
        "options_fn": "application_statuses",
        "validate": [
            "required"
        ],
        "contexts" : {
            "associate_editor" : {
                "help" : {
                    "short_help" : "Set the status to 'In Progress' to signal to the applicant that you have started your review."
                                    "Set the status to 'Ready' to alert the Editor that you have completed your review."
                }
            },
            "editor" : {
                "help" : {
                    "short_help" : "Revert the status to 'In Progress' to signal to the Associate Editor that further work is needed."
                                    "Set the status to 'Completed' to alert the Managing Editor that you have completed your review."
                }
            }
        },
        "widgets" : [
            # When Accepted selected display. 'This journal is currently assigned to its applicant account XXXXXX. Is this the correct account for this journal?'
            "owner_review"
        ]
    }

    DOAJ_EDITOR_GROUP = {
        "name": "doaj_editor_group",
        "label": "Assign to editor group",
        "input": "text",
        "widgets": [
            {"autocomplete": {"field": "editor_group"}}
        ],
        "contexts" : {
            "editor" : {
                "disabled" : True
            }
        }
    }

    DOAJ_EDITOR = {
        "name": "doaj_editor",
        "label": "Assign to individual",
        "input": "select",
        "options": [],
        "validate" : [
            { "group_member" : {"group_field" : "doaj_editor_group"}}
        ],
        "widgets" : [
            # show the members of the selected editor group
            # clear the field if the group is changed
            { "editor_select" : {"group_field" : "doaj_editor_group"}}
        ]
    }

    DOAJ_DISCONTINUED_DATE = {
        "name": "doaj_discontinued_date",
        "label": "This journal was discontinued on",
        "input": "text",
        "validate" : [
            "bigenddate",
            {
                "not_if" : {
                    "fields" : [
                        {"field" : "doaj_continues"},
                        {"field" : "doaj_continued_by"}
                    ],
                    "message" : "You cannot enter a discontinued date and continuation information."
                }
            }
        ],
        "help" : {
            "short_help" : "If the day of the month is not known, please use '01'"
        },
        "widgets" : [
            "datepicker"
        ]
    }

    DOAJ_CONTINUES = {
        "name": "doaj_continues",
        "label": "This journal continues an older journal with the ISSN(s)",
        "input": "taglist",
        "validate": [
            {"is_issn": {"message": "This is not a valid ISSN"}},   # FIXME: might have to think about how the validators work with a taglist
            {"different_to": {"field": "doaj_continued_by"}},       # FIXME: as above
            {"not_if" : { "fields" : {"field" : "doaj_discontinued_date"}}},
            "issn_in_public_doaj"                                   # FIXME: is this right?
        ]
    }

    DOAJ_CONTINUED_BY = {
        "name": "doaj_continued_by",
        "label": "This journal is continued by a newer version of the journal with the ISSN(s)",
        "input": "taglist",
        "validate": [
            {"is_issn": {"message": "This is not a valid ISSN"}}, # FIXME: might have to think about how the validators work with a taglist
            {"different_to": {"field": "doaj_continues"}},  # FIXME: as above
            {"not_if": {"fields": {"field": "doaj_discontinued_date"}}},
            "issn_in_public_doaj"  # FIXME: is this right?
        ]
    }

    DOAJ_SUBJECT = {
        "name": "doaj_subject",
        "label": "Assign one or a maximum of two subject classifications",
        "input": "text",
        "help": {
            "short_help": "Selecting a subject will not automatically select its sub-categories"
        },
        "validate": [
            "required",
            {"max_tags": {"max": 2, "message" : "You have chosen too many"}}        # required and max 2 should mean [min 1 max 2] to as per spec
        ],
        "widget": [
            "subject_tree"
        ]
    }


##########################################################
# Define our fieldsets
##########################################################

class FieldSetDefinitions:
    BASIC_COMPLIANCE = {
        "name": "basic_compliance",
        "label": "Basic Compliance",
        "fields": [
            FieldDefinitions.BOAI["name"],
            FieldDefinitions.OA_STATEMENT_URL["name"]
        ]
    }

    ABOUT_THE_JOURNAL = {
        "name": "about_the_journal",
        "label": "About the Journal",
        "fields": [
            FieldDefinitions.TITLE["name"],
            FieldDefinitions.ALTERNATIVE_TITLE["name"],
            FieldDefinitions.JOURNAL_URL["name"],
            FieldDefinitions.PISSN["name"],
            FieldDefinitions.EISSN["name"],
            FieldDefinitions.KEYWORDS["name"],
            FieldDefinitions.LANGUAGE["name"],
            FieldDefinitions.PUBLISHER["name"],
            FieldDefinitions.PUBLISHER_NAME["name"],
            FieldDefinitions.PUBLISHER_COUNTRY["name"],
            FieldDefinitions.INSTITUTION["name"],
            FieldDefinitions.INSTITUTION_NAME["name"],
            FieldDefinitions.INSTITUTION_COUNTRY["name"]
        ]
    }

    LICENSING = {
        "name": "licensing",
        "label": "Licensing",
        "fields": [
            FieldDefinitions.LICENSE["name"],
            FieldDefinitions.LICENSE_ATTRIBUTES["name"],
            FieldDefinitions.LICENSE_TERMS_URL["name"],
            FieldDefinitions.LICENSE_DISPLAY["name"],
            FieldDefinitions.LICENSE_DISPLAY_EXAMPLE_URL["name"]
        ]
    }

    COPYRIGHT = {
        "name": "copyright",
        "label": "Copyright",
        "fields": [
            FieldDefinitions.COPYRIGHT_AUTHOR_RETAINS["name"],
            FieldDefinitions.COPYRIGHT_URL["name"]
        ]
    }

    PEER_REVIEW = {
        "name": "peer_review",
        "label": "Peer Review",
        "fields": [
            FieldDefinitions.REVIEW_PROCESS["name"],
            FieldDefinitions.REVIEW_PROCESS_OTHER["name"],
            FieldDefinitions.REVIEW_URL["name"],
            FieldDefinitions.PLAGIARISM_DETECTION["name"],
            FieldDefinitions.PLAGIARISM_URL["name"]
        ]
    }

    EDITORIAL = {
        "name": "editorial",
        "label": "Editorial",
        "fields": [
            FieldDefinitions.AIMS_SCOPE_URL["name"],
            FieldDefinitions.EDITORIAL_BOARD_URL["name"],
            FieldDefinitions.AUTHOR_INSTRUCTIONS_URL["name"],
            FieldDefinitions.PUBLICATION_TIME_WEEKS["name"]
        ]
    }

    BUSINESS_MODEL = {
        "name": "business_model",
        "label": "Business Model",
        "fields": [
            FieldDefinitions.APC["name"],
            FieldDefinitions.APC_URL["name"],
            FieldDefinitions.APC_CHARGES["name"],
            FieldDefinitions.APC_CURRENCY["name"],
            FieldDefinitions.APC_MAX["name"],
            FieldDefinitions.HAS_WAIVER["name"],
            FieldDefinitions.WAIVER_URL["name"],
            FieldDefinitions.HAS_OTHER_CHARGES["name"],
            FieldDefinitions.OTHER_CHARGES_URL["name"]
        ]
    }

    ARCHIVING_POLICY = {
        "name": "archiving_policy",
        "label": "Archiving Policy",
        "fields": [
            FieldDefinitions.PRESERVATION_SERVICE["name"],
            FieldDefinitions.PRESERVATION_SERVICE_LIBRARY["name"],
            FieldDefinitions.PRESERVATION_SERVICE_OTHER["name"],
            FieldDefinitions.PRESERVATION_SERVICE_URL["name"]
        ]
    }

    REPOSITORY_POLICY = {
        "name": "deposit_policy",
        "label": "Repository Policy",
        "fields": [
            FieldDefinitions.DEPOSIT_POLICY["name"],
            FieldDefinitions.DEPOSIT_POLICY_OTHER["name"],
            FieldDefinitions.DEPOSIT_POLICY_URL["name"]
        ]
    }

    UNIQUE_IDENTIFIERS = {
        "name": "unique_identifiers",
        "label": "Unique Identifiers & Structured Data",
        "fields": [
            FieldDefinitions.PERSISTENT_IDENTIFIERS["name"],
            FieldDefinitions.PERSISTENT_IDENTIFIERS_OTHER["name"],
            FieldDefinitions.ORCID_IDS["name"],
            FieldDefinitions.OPEN_CITATIONS["name"]
        ]
    }

    SEAL = {
        "name": "seal",
        "label": "DOAJ Seal",
        "fields": [
            FieldDefinitions.DOAJ_SEAL["name"]
        ]
    }

    QUICK_REJECT = {
        "name": "quick_reject",
        "label": "Quick Reject",
        "fields": [
            FieldDefinitions.DOAJ_QUICK_REJECT["name"],
            FieldDefinitions.DOAJ_QUICK_REJECT_DETAILS["name"]
        ]
    }

    REASSIGN = {
        "name": "reassign",
        "label": "Re-assign publisher account",
        "fields": [
            FieldDefinitions.DOAJ_OWNER["name"]
        ]
    }

    STATUS = {
        "name": "status",
        "label": "Status",
        "fields": [
            FieldDefinitions.DOAJ_STATUS["name"]
        ]
    }

    REVIEWERS = {
        "name": "reviewers",
        "label": "Assign for review",
        "fields": [
            FieldDefinitions.DOAJ_EDITOR_GROUP["name"],
            FieldDefinitions.DOAJ_EDITOR["name"]
        ]
    }

    CONTINUATIONS = {
        "name": "continuations",
        "label": "Continuations",
        "fields": [
            FieldDefinitions.DOAJ_DISCONTINUED_DATE["name"],
            FieldDefinitions.DOAJ_CONTINUES["name"],
            FieldDefinitions.DOAJ_CONTINUED_BY["name"]
        ]
    }

    SUBJECT = {
        "name": "subject",
        "label": "Subject classification",
        "fields": [
            FieldDefinitions.DOAJ_SUBJECT["name"]
        ]
    }


###########################################################
# Define our Contexts
###########################################################

class ContextDefinitions:
    PUBLIC = {
        "name": "public",
        "fieldsets": [
            FieldSetDefinitions.BASIC_COMPLIANCE["name"],
            FieldSetDefinitions.ABOUT_THE_JOURNAL["name"],
            FieldSetDefinitions.LICENSING["name"],
            FieldSetDefinitions.COPYRIGHT["name"],
            FieldSetDefinitions.PEER_REVIEW["name"],
            FieldSetDefinitions.EDITORIAL["name"],
            FieldSetDefinitions.BUSINESS_MODEL["name"],
            FieldSetDefinitions.ARCHIVING_POLICY["name"],
            FieldSetDefinitions.REPOSITORY_POLICY["name"],
            FieldSetDefinitions.UNIQUE_IDENTIFIERS["name"]
        ],
        "asynchronous_warnings": [
            "all_urls_the_same"
        ],
        "templates": {
            "form" : "application_form/public_application.html",
            "default_field" : "application_form/_field.html",
            "default_group" : "application_form/_group.html"#,
            #"default_list" : "application_form/_list.html"
        },
        "crosswalks": {
            "obj2form": ApplicationFormXWalk.obj2form,
            "form2obj": ApplicationFormXWalk.form2obj
        },
        "processor": application_processors.NewApplication,
    }

    # TODO - define the update request context
    UPDATE = deepcopy(PUBLIC)
    UPDATE["name"] = "update_request"

    ASSOCIATE = deepcopy(PUBLIC)
    ASSOCIATE["name"] = "associate_editor"
    ASSOCIATE["fieldsets"] += [
        FieldSetDefinitions.STATUS["name"]
    ]

    EDITOR = deepcopy(PUBLIC)
    EDITOR["name"] = "editor"
    EDITOR["fieldsets"] += [
        FieldSetDefinitions.STATUS["name"],
        FieldSetDefinitions.REASSIGN["name"],
    ]

    MANED = deepcopy(PUBLIC)
    MANED["name"] = "admin"
    MANED["fieldsets"] += [
        FieldSetDefinitions.SEAL["name"],
        FieldSetDefinitions.QUICK_REJECT["name"],
        FieldSetDefinitions.REASSIGN["name"],
        FieldSetDefinitions.STATUS["name"],
        FieldSetDefinitions.REASSIGN["name"],
        FieldSetDefinitions.CONTINUATIONS["name"],
        FieldSetDefinitions.SUBJECT["name"]
    ]
    MANED["processor"] = application_processors.NewApplication  # FIXME: enter the real processor


#######################################################
# Gather all of our form information in one place
#######################################################

FORMS = {
    "contexts": {
        ContextDefinitions.PUBLIC["name"]: ContextDefinitions.PUBLIC,
        ContextDefinitions.MANED["name"]: ContextDefinitions.MANED
    },
    "fieldsets": {v['name']: v for k, v in FieldSetDefinitions.__dict__.items() if not k.startswith('_')},
    "fields": {v['name']: v for k, v in FieldDefinitions.__dict__.items() if not k.startswith('_')}
}


#######################################################
# Options lists
#######################################################

def iso_country_list(field):
    cl = []
    for v, d in country_options:
        cl.append({"display": d, "value": v})
    return cl


def iso_language_list(field):
    cl = []
    for v, d in language_options:
        cl.append({"display": d, "value": v})
    return cl


def iso_currency_list(field):
    cl = [{"display" : "Currency", "value" : ""}]
    for v, d in currency_options:
        cl.append({"display": d, "value": v})
    return cl


def quick_reject(field):
    raise NotImplementedError()


def application_statuses(field):
    raise NotImplementedError()


#######################################################
# Validation features
#######################################################

class RequiredBuilder:
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["required"] = ""
        if "message" in settings:
            html_attrs["data-parsley-required-message"] = settings["message"]

    @staticmethod
    def wtforms(field, settings):
        return validators.InputRequired(message=settings.get("message"))


class IsURLBuilder:
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["type"] = "url"

    @staticmethod
    def wtforms(field, settings):
        # FIXME: do we want the scheme to be optional?
        return URLOptionalScheme()


class IntRangeBuilder:
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-type"] = "digits"
        if "gte" in settings:
            html_attrs["data-parsley-min"] = settings.get("gte")
        if "lte" in settings:
            html_attrs["data-parsley-max"] = settings.get("lte")

    @staticmethod
    def wtforms(field, settings):
        min = settings.get("gte")
        max = settings.get("lte")
        kwargs = {}
        if min is not None:
            kwargs["min"] = min
        if max is not None:
            kwargs["max"] = max
        return validators.NumberRange(**kwargs)


class MaxTagsBuilder:
    @staticmethod
    def wtforms(field, settings):
        max = settings.get("max")
        message = settings.get("message") if "message" in settings else 'You can only enter up to {x} keywords.'.format(x=max)
        return MaxLen(max, message=message)


class StopWordsBuilder:
    @staticmethod
    def wtforms(field, settings):
        stopwords = settings.get("disallowed", [])
        return StopWords(stopwords)


class ISSNInPublicDOAJBuilder:
    @staticmethod
    def render(settings, html_attrs):
        # FIXME: not yet implemented in the front end, so setting here is speculative
        html_attrs["data-parsley-issn-in-public-doaj"] = ""

    @staticmethod
    def wtforms(field, settings):
        return ISSNInPublicDOAJ(message=settings.get("message"))


class JournalURLInPublicDOAJBuilder:
    @staticmethod
    def render(settings, html_attrs):
        # FIXME: not yet implemented in the front end, so setting here is speculative
        html_attrs["data-parsley-journal-url-in-public-doaj"] = ""

    @staticmethod
    def wtforms(field, settings):
        return JournalURLInPublicDOAJ(message=settings.get("message"))


class OptionalIfBuilder:
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-optional-if"] = settings.get("field")

    @staticmethod
    def wtforms(field, settings):
        return OptionalIf(settings.get("field"), settings.get("message"), settings.get("values", []))


class IsISSNBuilder:
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["pattern"] = ISSN
        html_attrs["data-parsley-pattern"] = ISSN

    @staticmethod
    def wtforms(field, settings):
        return validators.Regexp(regex=ISSN_COMPILED, message=settings.get("message"))


class DifferentToBuilder:
    @staticmethod
    def render(settings, html_attrs):
        # FIXME: front end validator for this does not yet exist
        html_attrs["data-parsley-different-to"] = settings.get("field")

    @staticmethod
    def wtforms(field, settings):
        return DifferentTo(settings.get("field"), settings.get("ignore_empty", True), settings.get("message"))


class RequiredIfBuilder:
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-required-if-field"] = settings.get("field")
        html_attrs["data-parsley-required-if-value"] = settings.get("value")

    @staticmethod
    def wtforms(field, settings):
        return RequiredIfOtherValue(settings.get("field"), settings.get("value"))


class OnlyIfBuilder:
    @staticmethod
    def render(settings, html_attrs):
        raise NotImplementedError()

    @staticmethod
    def wtforms(field, settings):
        raise NotImplementedError()


class GroupMemberBuilder:
    @staticmethod
    def render(settings, html_attrs):
        raise NotImplementedError()

    @staticmethod
    def wtforms(field, settings):
        raise NotImplementedError()

class NotIfBuildier:
    @staticmethod
    def render(settings, html_attrs):
        raise NotImplementedError()

    @staticmethod
    def wtforms(field, settings):
        raise NotImplementedError()


#########################################################
# Crosswalks
#########################################################

PYTHON_FUNCTIONS = {
    "options": {
        "iso_country_list": iso_country_list,
        "iso_language_list": iso_language_list,
        "iso_currency_list": iso_currency_list,
        "quick_reject" : quick_reject,
        "application_statuses" : application_statuses
    },
    "validate": {
        "render": {
            "required": RequiredBuilder.render,
            "is_url": IsURLBuilder.render,
            "int_range": IntRangeBuilder.render,
            "issn_in_public_doaj": ISSNInPublicDOAJBuilder.render,
            "journal_url_in_public_doaj" : JournalURLInPublicDOAJBuilder.render,
            "optional_if": OptionalIfBuilder.render,
            "is_issn": IsISSNBuilder.render,
            "different_to": DifferentToBuilder.render,
            "required_if": RequiredIfBuilder.render,
            "only_if" : OnlyIfBuilder.render,
            "group_member" : GroupMemberBuilder.render,
            "not_if" : NotIfBuildier.render
        },
        "wtforms": {
            "required": RequiredBuilder.wtforms,
            "is_url": IsURLBuilder.wtforms,
            "max_tags": MaxTagsBuilder.wtforms,
            "int_range": IntRangeBuilder.wtforms,
            "stop_words": StopWordsBuilder.wtforms,
            "issn_in_public_doaj": ISSNInPublicDOAJBuilder.wtforms,
            "journal_url_in_public_doaj" : JournalURLInPublicDOAJBuilder.wtforms,
            "optional_if": OptionalIfBuilder.wtforms,
            "is_issn": IsISSNBuilder.wtforms,
            "different_to": DifferentToBuilder.wtforms,
            "required_if": RequiredIfBuilder.wtforms,
            "only_if" : OnlyIfBuilder.wtforms,
            "group_member" : GroupMemberBuilder.wtforms,
            "not_if" : NotIfBuildier.wtforms
        }
    },


    #"all_urls_the_same" : "portality.formcontext.validators.all_urls_the_same",
    #"to_lower" : "portality.formcontext.postprocessing.to_lower",
    #"warn_on_value" : "portality.formcontext.validators.warn_on_value",
    #"clickable_url" : "portality.formcontext.widgets.clickable_url",
}


JAVASCRIPT_FUNCTIONS = {
    #"required_value" : "doaj.forms.validators.requiredValue",
    #"required" : "doaj.forms..validators.required",
    #"is_url" : "doaj.forms.validators.isUrl",
    #"max_tags" : "doaj.forms.validators.maxTags",
    #"stop_words" : "doaj.forms.validators.stopWords",
    #"int_range" : "doaj.forms.validators.intRange",
    #"autocomplete" : "doaj.forms.widgets.autocomplete",

    "clickable_url": "formulaic.widgets.newClickableUrl",
    "select": "formulaic.widgets.newSelect",
    "taglist": "formulaic.widgets.newTagList"
}


##############################################################
# Additional WTForms bits, that will probably need to be
# moved out to the correct modules before wrapping up
##############################################################

class NumberWidget(widgets.Input):
    input_type = 'number'


class ListWidgetWithSubfields(object):
    """
    Renders a list of fields as a `ul` or `ol` list.

    This is used for fields which encapsulate many inner fields as subfields.
    The widget will try to iterate the field to get access to the subfields and
    call them to render them.

    If `prefix_label` is set, the subfield's label is printed before the field,
    otherwise afterwards. The latter is useful for iterating radios or
    checkboxes.
    """
    def __init__(self, html_tag='ul', prefix_label=False):
        assert html_tag in ('ol', 'ul')
        self.html_tag = html_tag
        self.prefix_label = prefix_label

    def __call__(self, field, **kwargs):
        # kwargs.setdefault('id', field.id)
        fl = kwargs.pop("formulaic", None)
        html = ['<%s %s>' % (self.html_tag, html_params(**kwargs))]
        for subfield in field:
            if self.prefix_label:
                html.append('<li>%s %s' % (subfield.label, subfield(**kwargs)))
            else:
                html.append('<li>%s %s' % (subfield(**kwargs), subfield.label))

            if fl is not None:
                sfs = fl.get_subfields(subfield._value())
                for sf in sfs:
                    style = ""
                    if sf.has_conditional:
                        style = " style=display:none "
                    html.append('<span class="{x}__container" {y}>'.format(x=sf.name, y=style))
                    html.append(sf.render_form_control())
                    html.append("</span>")

            html.append("</li>")

        html.append('</%s>' % self.html_tag)
        return HTMLString(''.join(html))


##########################################################
# Mapping from configurations to WTForms builders
##########################################################

class RadioBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "radio"

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        return RadioField(**wtfargs)


class MultiCheckboxBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "checkbox" and \
               (len(field.get("options", [])) > 0 or field.get("options_fn") is not None)

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        wtfargs["option_widget"] = widgets.CheckboxInput()
        wtfargs["widget"] = ListWidgetWithSubfields()
        return SelectMultipleField(**wtfargs)


class SingleCheckboxBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "checkbox" and len(field.get("options", [])) == 0 and field.get("options_fn") is None

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        return BooleanField(**wtfargs)


class SelectBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "select" and not field.get("multiple", False)

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        return SelectField(**wtfargs)


class MultiSelectBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "select" and field.get("multiple", False)

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        return SelectMultipleField(**wtfargs)


class TextBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "text"

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        sf = StringField(**wtfargs)
        if "repeatable" in field:
            sf = FieldList(sf, min_entries=field.get("repeatable", {}).get("initial", 1))
        return sf


class TagListBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "taglist"

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        return TagListField(**wtfargs)


class IntegerBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "number" and field.get("datatype") == "integer"

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        wtfargs["widget"] = NumberWidget()
        return IntegerField(**wtfargs)


class GroupBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "group" and not field.get("repeatable", False)

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        fields = [formulaic_context.get(subfield) for subfield in field.get("subfields", [])]
        klazz = formulaic_context.make_wtform_class(fields)
        return FormField(klazz)


class GroupListBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "group" and field.get("repeatable") is not None

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        ff = GroupBuilder.wtform(formulaic_context, field, wtfargs)
        repeat_cfg = field.get("repeatable", {})
        return FieldList(ff, min_entries=repeat_cfg.get("initial", 1))


WTFORMS_BUILDERS = [
    RadioBuilder,
    MultiCheckboxBuilder,
    SingleCheckboxBuilder,
    SelectBuilder,
    MultiSelectBuilder,
    TextBuilder,
    TagListBuilder,
    IntegerBuilder,
    GroupBuilder,
    GroupListBuilder
]

ApplicationFormFactory = Formulaic(FORMS, WTFORMS_BUILDERS, function_map=PYTHON_FUNCTIONS, javascript_functions=JAVASCRIPT_FUNCTIONS)
