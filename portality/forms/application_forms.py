from copy import deepcopy
from portality.lib.formulaic import Formulaic, WTFormsBuilder

from wtforms import StringField, IntegerField, BooleanField, RadioField, SelectMultipleField, SelectField, \
    FormField, FieldList
from wtforms import widgets, validators
from wtforms.widgets.core import html_params, HTMLString

from portality.formcontext.fields import TagListField
from portality.crosswalks.application_form import ApplicationFormXWalk
from portality.crosswalks.journal_form import JournalFormXWalk
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
    RequiredIfOtherValue,
    OnlyIf,
    NotIf,
    GroupMember
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
        "label": "Does the journal adhere to this definition of open access?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y"},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": ['This definition follows the definition of Libre Open Access formulated by Peter Suber <br>'
                          "<a href='http://nrs.harvard.edu/urn-3:HUL.InstRepos:4322580' target='_blank' >http://nrs.harvard.edu/urn-3:HUL.InstRepos:4322580</a>"],
            "doaj_criteria": "You must answer 'Yes'"
        },
        "validate": [
            {"required": {"message": "You must answer YES to continue"}},
            {"required_value" : {"value" : "y", "message" : "You must answer YES to continue"}}
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
        "label": "The journal website must display its open access statement. Where can we find this information?",
        "input": "text",
        "help": {
            "long_help": ["Here is an example of a suitable Open Access statement that meets our criteria:<blockquote>"
                          "This is an open access journal which means that all content is freely available without charge"
                          "to the user or his/her institution. Users are allowed to read, download, copy, distribute,"
                          "print, search, or link to the full texts of the articles, or use them for any other lawful"
                          "purpose, without asking prior permission from the publisher or the author. This is in accordance"
                          "with the BOAI definition of open access.</blockquote>"],
            "short_help": "Link to the journal’s open access statement",
            "placeholder": "https://www.my-journal.com/open-access"
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
            "long_help": ["The journal title must match what is displayed on the website and what is registered at the "
                          "<a href='https://portal.issn.org/' target='_blank'> ISSN Portal</a>.",
                          "For translated titles, you may add the "
                          "translation as an alternative title."],
            "placeholder": "Journal title",
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
        "optional": True,
        "help": {
            "long_help": ["The journal title must match what is displayed on the website and what is registered at the "
                          "<a href='https://portal.issn.org/' target='_blank' > ISSN Portal</a>.",
                          "For translated titles, you may add the "
                          "translation as an alternative title."],
            "placeholder": "Ma revue"
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
        "help": {
            "placeholder": "https://www.my-journal.com"
        },
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
        "label": "ISSN (print)",
        "input": "text",
        "help": {
            "long_help": ["Must be a valid ISSN, fully registered and confirmed at the "
                          "<a href='https://portal.issn.org/' target='_blank' > ISSN Portal.</a>",
                          "The ISSN must match what is given on the journal website."],
            "placeholder": "2049-3630",
            "doaj_criteria": "ISSN must be provided"
        },
        "validate": [
            {"optional_if": {"field": "eissn",
                             "message": "You must provide one or both of an online ISSN or a print ISSN"}},
            {"is_issn": {"message": "This is not a valid ISSN"}},
            {"different_to": {"field": "eissn", "message": "This field must contain a different value to 'ISSN ("
                                                           "online)'"}},
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
            "long_help": ["Must be a valid ISSN, fully registered and confirmed at the "
                          "<a href='https://portal.issn.org/' target='_blank' > ISSN Portal</a>",
                          "The ISSN must match what is given on the journal website."],
            "placeholder": "0378-5955",
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
        "label": "Up to 6 subject keywords in English",
        "input": "taglist",
        "help": {
            "long_help": ["Only 6 keywords are allowed. Choose words that describe the subject matter of the journal "
                          "and not the journal's qualities.", "Keywords must be in English and separated by a comma."],
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
                    "stopWords": STOP_WORDS,
                    "field": "bibjson.keywords"
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
        "default" : "",
        "options_fn": "iso_language_list",
        "repeatable": {
            "initial": 5
        },
        "validate": [
            "required"
        ],
        "widgets": [
            {"select": {}},
            "multiple_field"
        ],
        "attr": {
            "class": "input-xlarge"
        }
    }

    PUBLISHER_NAME = {
        "name": "publisher_name",
        "label": "Name",
        "input": "text",
        "validate": [
            "required"
        ],
        "widgets": [
            {"autocomplete": {"field": "bibjson.publisher.name.exact"}},
        ]
    }

    PUBLISHER_COUNTRY = {
        "name": "publisher_country",
        "label": "Country",
        "input": "select",
        "default": "",
        "options_fn": "iso_country_list",
        "help": {
            "long_help": ["The country where the publisher carries out its business operations and is registered."],
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

    INSTITUTION_NAME = {
        "name": "institution_name",
        "label": "Name",
        "input": "text",
        "optional": True,
        "help": {
            "short_help": "The society or institution responsible for the journal",
            "long_help": ["Some societies or institutions are linked to a journal in some way but are not responsible "
                          "for publishing it. The publisher can be a separate organisation. If your journal is linked to "
                          "a society or other type of institution, enter that here."]
        },
        "widgets": [
            {"autocomplete": {"field": "bibjson.institution.name.exact"}},
        ]
    }

    INSTITUTION_COUNTRY = {
        "name": "institution_country",
        "label": "Country",
        "input": "select",
        "default" : "",
        "options_fn": "iso_country_list",
        "help": {
            "short_help": "The country in which the society or institution is based",
            "optional": True
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
            {"display": "Publisher's own license", "value": "Publisher's own license", "exclusive": True, "subfields": ["license_attributes"]},
        ],
        "help": {
            "long_help": ["The journal must use some form of licensing to be considered for indexing in DOAJ. ",
                          "If Creative Commons licensing is not used, then select <i>Publisher's own license</i> and enter "
                          "more details below."],
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
        "label": "Where can we find this information?",
        "input": "text",
        "validate": [
            "required",
            "is_url"
        ],
        "placeholder": "https://www.my-journal.com/about#licensing",
        "help": {
            "short_help": "Link to the page where the license terms are stated",
            "doaj_criteria": "You must provide a link to your license terms"
        },
        "widgets": [
            "clickable_url"
        ]
    }

    LICENSE_DISPLAY = {
        "name": "license_display",
        "label": "Does the journal embed and/or display licensing information in its articles?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y", "subfields": ["license_display_example_url"]},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": ["Licensing information must be displayed or embedded on every PDF or in the full text of the "
                          "HTML articles.",
                          "We do not accept licensing information that is only displayed in other parts of "
                          "the site."],
            "seal_criteria": "If the answer is Embed"
        },
        "validate": [
            "required"
        ]
    }

    LICENSE_DISPLAY_EXAMPLE_URL = {
        "name": "license_display_example_url",
        "label": "Recent article displaying or embedding a license in the full text",
        "input": "text",
        "optional": True,
        "conditional": [
            {"field": "license_display", "value": "y"}
        ],
        "help": {
            "short_help": "Link to an example article"
        },
        "validate": [
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    COPYRIGHT_AUTHOR_RETAINS = {
        "name": "copyright_author_retains",
        "label": "For all the licenses you have indicated above, do authors or their institutions retain the copyright "
                 "<b>and</b> full publishing rights without restrictions?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y"},
            {"display": "No", "value": "n"}
        ],
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
        "label": "Where can we find this information?",
        "input": "text",
        "help": {
            "short_help": "Link to the journal's copyright terms"
        },
        "placeholder": "https://www.my-journal.com/about#licensing",
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
        "label": "DOAJ only accepts peer-reviewed journals. "
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
        "label": "Other peer review",
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
        "label": "Where can we find this information?",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL",
            "short_help": "Link to the journal's peer review policy"
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
            {"display": "Yes", "value": "y", "subfields": ["review_process_other"]},
            {"display": "No", "value": "n"}
        ],
        "validate": [
            "required"
        ]
    }

    PLAGIARISM_URL = {
        "name": "plagiarism_url",
        "label": "Where can we find this information?",
        "input": "text",
        "conditional": [{"field": "plagiarism_detection", "value": "y"}],
        "help": {
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/about#plagiarism",
            "short_help": "Link to the journal's plagiarism policy"
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
        "label": "Link to the journal's <b>Aims & Scope</b>",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/about#aims"
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
        "label": "Link to the journal's <b>Editorial board</b>",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/about#board"
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
        "label": "Link to the journal's <b>Instructions for Author</b>",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/for_authors"
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
            {"display": "Yes", "value": "y", "subfields": ["apc_charges"]},
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
        "label": "Where can we find this information?",
        "input": "text",
        "help": {
            "short_help": "Link to the page where this is stated. The page must declare <b>whether or not</b> APCs "
                          "are charged.",
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/about#apc"
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
        "label": "Highest APC charged",
        "repeatable" : {
            "initial" : 5
        },
        "conditional": [
            {"field": "apc", "value": "y"}
        ],
        "help": {
            "long_help": ["If the journal charges different APCs, you must enter the highest APC charged. If more than "
                          "one currency is used, add a new line"]
        },
        "subfields": [
            "apc_currency",
            "apc_max"
        ],
        "template" : "application_form/_list.html",
        "entry_template" : "application_form/_entry_group_horizontal.html",
        "widgets": [
            "multiple_field"
        ]
    }

    APC_CURRENCY = {
        "subfield": True,
        "group" : "apc_charges",
        "name": "apc_currency",
        "input": "select",
        "options_fn": "iso_currency_list",
        "default" : "",
        "help": {
            "placeholder": "Currency"
        },
        "widgets": [
            {"select": {}}
        ],
        "attr": {
            "class": "input-xlarge"
        }
    }

    APC_MAX = {
        "subfield": True,
        "group" : "apc_charges",
        "name": "apc_max",
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
            {"display": "Yes", "value": "y", "subfields": ["waiver_url"]},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": ["Answer Yes if the journal provides APC waivers for authors from low-income economies, "
                          "discounts for authors from lower middle-income economies, and/or waivers and discounts for "
                          "other authors with demonstrable needs. "]
        },
        "validate": [
            "required"
        ]
    }

    WAIVER_URL = {
        "name": "waiver_url",
        "label": "Where can we find this information?",
        "input": "text",
        "conditional": [
            {"field": "has_waiver", "value": "y"}
        ],
        "help": {
            "short_help": "Link to the journal's waiver information.",
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
            {"display": "Yes", "value": "y", "subfields": ["other_charges_url"]},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": ["Declare all other charges: editorial processing charges, colour charges, submission fees, "
                          "page charges, membership fees, print subscription costs, other supplementary charges"],
            "doaj_criteria": "You must declare any other charges if they exist"
        },
        "validate": [
            "required"
        ]
    }

    OTHER_CHARGES_URL = {
        "name": "other_charges_url",
        "label": "Where can we find this information?",
        "input": "text",
        "conditional": [
            {"field": "has_other_charges", "value": "y"}
        ],
        "help": {
            "short_help": "Link to the journal's fees information",
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
        "hint": "Select at least one:",
        "options": [
            {"display": "CINES", "value": "CINES", "subfields": ["preservation_service_url"]},
            {"display": "CLOCKSS", "value": "CLOCKSS", "subfields": ["preservation_service_url"]},
            {"display": "LOCKSS", "value": "LOCKSS", "subfields": ["preservation_service_url"]},
            {"display": "Internet Archive", "value": "Internet Archive", "subfields": ["preservation_service_url"]},
            {"display": "PKP PN", "value": "PKP PN", "subfields": ["preservation_service_url"]},
            {"display": "PubMed Central (PMC)", "value": "PMC", "subfields": ["preservation_service_url"]},
            {"display": "Portico", "value": "Portico", "subfields": ["preservation_service_url"]},
            {"display": "A national library", "value": "national_library", "subfields": ["preservation_service_library", "preservation_service_url"]},
            {"display": "The journal content isn't archived with a long-term preservation service",
             "value": "none", "exclusive": True},
            {"display": "Other", "value": "other", "subfields": ["preservation_service_other", "preservation_service_url"]}
        ],
        "help": {
            "long_help": [
                "Only active archiving is accepted; content must be actively deposited in each of the options "
                "you choose. If the journal is registered with a service but archiving is not yet active, "
                "choose <i>No</i>.", "PubMed Central covers PMC U.S.A., PMC Canada, and PMC Europe (Wellcome Trust)."]
        },
        "validate": [
            "required"
        ]
    }

    PRESERVATION_SERVICE_LIBRARY = {
        "name": "preservation_service_library",
        "label": "A national library:",
        "input": "text",
        "repeatable" : {
            "initial" : 2
        },
        "help": {
            "short_help": "Name of national library"
        },
        "conditional": [{"field": "preservation_service", "value": "national_library"}],
        "validate": [
            {"required_if": {"field": "preservation_service", "value": "national_library"}}
        ],
        "asynchronous_warning": [
            {"warn_on_value": {"value": "None"}}
        ],
        "widgets": [
            "multiple_field"
        ]
    }

    PRESERVATION_SERVICE_OTHER = {
        "name": "preservation_service_other",
        "label": "Other archiving policy:",
        "input": "text",
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
        "label": "Where can we find this information?",
        "input": "text",
        "help": {
            "short_help": "Link to the preservation and archiving information on the journal's site",
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/about#archiving"
        },
        "conditional": [
            {"field": "preservation_service", "value": "CINES"},
            {"field": "preservation_service", "value": "CLOCKSS"},
            {"field": "preservation_service", "value": "LOCKSS"},
            {"field": "preservation_service", "value": "Internet Archive"},
            {"field": "preservation_service", "value": "PKP PN"},
            {"field": "preservation_service", "value": "PMC"},
            {"field": "preservation_service", "value": "Portico"},
            {"field": "preservation_service", "value": "national_library"},
            {"field": "preservation_service", "value": "other"}
        ],
        "validate": [
            {"required_if": {"field": "preservation_service", "values": ["CINES"]}},
            {"required_if": {"field": "preservation_service", "values": ["CLOCKSS"]}},
            {"required_if": {"field": "preservation_service", "values": ["LOCKSS"]}},
            {"required_if": {"field": "preservation_service", "values": ["Internet Archive"]}},
            {"required_if": {"field": "preservation_service", "values": ["PKP PN"]}},
            {"required_if": {"field": "preservation_service", "values": ["PMC"]}},
            {"required_if": {"field": "preservation_service", "values": ["Portico"]}},
            {"required_if": {"field": "preservation_service", "values": ["national_library"]}},
            {"required_if": {"field": "preservation_service", "values": ["other"]}},
            "is_url"
        ],
        "widgets": [
            "clickable_url"
        ]
    }

    DEPOSIT_POLICY = {
        "name": "deposit_policy",
        "label": "Does the journal have a policy allowing authors to deposit versions of their work in an "
                 "institutional or other repository of their choice? Where is this policy recorded?",
        "input": "checkbox",
        "multiple": True,
        "options": [
            {"display": "Sherpa/Romeo", "value": "Sherpa/Romeo", "subfields": ["deposit_policy_url"]},
            {"display": "Dulcinea", "value": "Dulcinea", "subfields": ["deposit_policy_url"]},
            {"display": "Héloïse", "value": "Héloïse", "subfields": ["deposit_policy_url"]},
            {"display": "Diadorim", "value": "Diadorim", "subfields": ["deposit_policy_url"]},
            {"display": "The journal has no repository policy", "value": "none", "exclusive": True},
            {"display": "Other (including publisher's own site)", "value": "other", "subfields": ["deposit_policy_other"], "subfields": ["deposit_policy_url"]}
        ],
        "help": {
            "long_help": ["Many authors wish to deposit a copy of their paper in an institutional or other repository "
                          "of their choice. What is the journal's policy for this?",
                          "You should state your policy with regard to the different versions of the paper:"
                          "<ul style='list-style-type: none;'>"
                          "<li>Submitted version</li>"
                          "<li>Accepted version (Author Accepted Manuscript)</li>"
                          "<li>Published version (Version of Record)</li>"
                          "</ul>",
                          "For a journal to qualify for the DOAJ Seal, it must allow all versions to be deposited in an institutional or other repository of the author's choice without embargo.,"
                          ]},
        "validate": [
            "required"
        ]
    }

    DEPOSIT_POLICY_OTHER = {
        "name": "deposit_policy_other",
        "label": "Other repository",
        "input": "text",
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
        "label": "Where can we find this information?",
        "input": "text",
        "conditional": [{"field": "deposit_policy", "value": "Sherpa/Romeo"},
                        {"field": "deposit_policy", "value": "Dulcinea"},
                        {"field": "deposit_policy", "value": "Héloïse"},
                        {"field": "deposit_policy", "value": "Diadorim"},
                        {"field": "deposit_policy", "value": "other"}],
        "help": {
            "doaj_criteria": "You must provide a URL",
            "short_help": "Link to the policy on the journal's site",
            "placeholder": "https://www.my-journal.com/about#repository_policy"
        },
        "validate": [
            {"required_if": {"field": "deposit_policy", "value": "Sherpa/Romeo"}},
            {"required_if": {"field": "deposit_policy", "value": "Dulcinea"}},
            {"required_if": {"field": "deposit_policy", "value": "Héloïse"}},
            {"required_if": {"field": "deposit_policy", "value": "Diadorim"}},
            {"required_if": {"field": "deposit_policy", "value": "other"}},
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
        "hint": "Select at least one",
        "options": [
            {"display": "DOIs", "value": "DOI"},
            {"display": "ARKs", "value": "ARK"},
            {"display": "Handles", "value": "Handles"},
            {"display": "PURLs", "value": "PURL"},
            {"display": "The journal does not use persistent article identifiers", "value": "none", "exclusive": True},
            {"display": "Other", "value": "other", "subfields": ["persistent_identifiers_other"]}
        ],
        "help": {
            "long_help": ["A persistent article identifier (PID) is used to find the article no matter where it is "
                         "located. The most common type of PID is the digital object identifier (DOI). ",
                         "<a href='https://en.wikipedia.org/wiki/Persistent_identifier' target='_blank' >Read more about PIDs.</a>"],
        },
        "validate": [
            "required"
        ]
    }

    PERSISTENT_IDENTIFIERS_OTHER = {
        "name": "persistent_identifiers_other",
        "label": "Other identifier",
        "input": "text",
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
            "long_help": ["An <a href='https://orcid.org/'>ORCID</a> (Open Researcher and Contributor) iD is an alphanumeric code to uniquely identify "
                         "authors."],
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
            "long_help": ["The <a href='https://i4oc.org/#goals' target='_blank'>I4OC standards</a> ask that citations are structured, separable, and open. "],
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

    QUICK_REJECT = {
        "name": "quick_reject",
        "label": "Select the reason for rejection",
        "input": "select",
        "options_fn": "quick_reject"
    }

    QUICK_REJECT_DETAILS = {
        "name": "quick_reject_details",
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

    OWNER = {
        "name": "owner",
        "label": "DOAJ Account",
        "input": "text",
        "validate": [
            {"required" : {"message" : "You must confirm the account id"}}
        ],
        "widgets": [
            {"autocomplete": {"field": "account"}}
        ]
    }

    APPLICATION_STATUS = {
        "name": "application_status",
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

    EDITOR_GROUP = {
        "name": "editor_group",
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

    EDITOR = {
        "name": "editor",
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

    DISCONTINUED_DATE = {
        "name": "discontinued_date",
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

    CONTINUES = {
        "name": "continues",
        "label": "This journal continues an older journal with the ISSN(s)",
        "input": "taglist",
        "validate": [
            {"is_issn": {"message": "This is not a valid ISSN"}},   # FIXME: might have to think about how the validators work with a taglist
            {"different_to": {"field": "doaj_continued_by"}},       # FIXME: as above
            {"not_if" : { "fields" : [{"field" : "doaj_discontinued_date"}]}},
            "issn_in_public_doaj"                                   # FIXME: is this right?
        ]
    }

    CONTINUED_BY = {
        "name": "continued_by",
        "label": "This journal is continued by a newer version of the journal with the ISSN(s)",
        "input": "taglist",
        "validate": [
            {"is_issn": {"message": "This is not a valid ISSN"}}, # FIXME: might have to think about how the validators work with a taglist
            {"different_to": {"field": "doaj_continues"}},  # FIXME: as above
            {"not_if": {"fields": [{"field": "doaj_discontinued_date"}]}},
            "issn_in_public_doaj"  # FIXME: is this right?
        ]
    }

    SUBJECT = {
        "name": "subject",
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

    NOTES = {
        "name" : "notes",
        "input": "group",
        "label": "Note",
        "repeatable" : {
            "initial" : 1
        },
        "subfields": [
            "note",
            "note_date",
            "note_id"
        ],
        "widgets": [
            "multiple_field"
        ]
    }

    NOTE = {
        "subfield": True,
        "name": "note",
        "input": "text"
    }

    NOTE_DATE = {
        "subfield": True,
        "name" : "note_date",
        "input": "text"
    }

    NOTE_ID = {
        "subfield" : True,
        "name": "note_id",
        "input": "hidden"
    }

    OPTIONAL_VALIDATION = {
        "name" : "optional_validation",
        "input" : "checkbox",
        "widget" : {
            "optional_validation"
        }
    }


##########################################################
# Define our fieldsets
##########################################################

class FieldSetDefinitions:
    BASIC_COMPLIANCE = {
        "name": "basic_compliance",
        "label": "Open access compliance",
        "fields": [
            FieldDefinitions.BOAI["name"],
            FieldDefinitions.OA_STATEMENT_URL["name"]
        ]
    }

    ABOUT_THE_JOURNAL = {
        "name": "about_the_journal",
        "label": "About the journal",
        "fields": [
            FieldDefinitions.TITLE["name"],
            FieldDefinitions.ALTERNATIVE_TITLE["name"],
            FieldDefinitions.JOURNAL_URL["name"],
            FieldDefinitions.PISSN["name"],
            FieldDefinitions.EISSN["name"],
            FieldDefinitions.KEYWORDS["name"],
            FieldDefinitions.LANGUAGE["name"]
        ]
    }

    PUBLISHER = {
        "name": "publisher",
        "label": "Publisher",
        "fields": [
            FieldDefinitions.PUBLISHER_NAME["name"],
            FieldDefinitions.PUBLISHER_COUNTRY["name"],
        ]
    }

    SOCIETY_OR_INSTITUTION = {
        "name": "society_or_institution",
        "label": "Society or institution, if applicable",
        "fields": [
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
            FieldDefinitions.LICENSE_TERMS_URL["name"]
        ]
    }

    EMBEDDED_LICENSING = {
        "name": "embedded_licensing",
        "label": "Embedded licences",
        "fields": [
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
            FieldDefinitions.REVIEW_URL["name"]
        ]
    }

    PLAGIARISM = {
        "name": "plagiarism",
        "label": "Plagiarism",
        "fields": [
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

    APC = {
        "name": "apc",
        "label": "Article Processing Charges",
        "fields": [
            FieldDefinitions.APC["name"],
            FieldDefinitions.APC_URL["name"],
            FieldDefinitions.APC_CHARGES["name"],
            FieldDefinitions.APC_CURRENCY["name"],
            FieldDefinitions.APC_MAX["name"],
        ]
    }

    APC_WAIVERS = {
        "name": "apc_waivers",
        "label": "APC waivers",
        "fields": [
            FieldDefinitions.HAS_WAIVER["name"],
            FieldDefinitions.WAIVER_URL["name"],
        ]
    }

    OTHER_FEES = {
        "name": "other_fees",
        "label": "Other fees",
        "fields": [
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
        "label": "Unique Identifiers & structured Data",
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
            FieldDefinitions.QUICK_REJECT["name"],
            FieldDefinitions.QUICK_REJECT_DETAILS["name"]
        ]
    }

    REASSIGN = {
        "name": "reassign",
        "label": "Re-assign publisher account",
        "fields": [
            FieldDefinitions.OWNER["name"]
        ]
    }

    STATUS = {
        "name": "status",
        "label": "Status",
        "fields": [
            FieldDefinitions.APPLICATION_STATUS["name"]
        ]
    }

    REVIEWERS = {
        "name": "reviewers",
        "label": "Assign for review",
        "fields": [
            FieldDefinitions.EDITOR_GROUP["name"],
            FieldDefinitions.EDITOR["name"]
        ]
    }

    CONTINUATIONS = {
        "name": "continuations",
        "label": "Continuations",
        "fields": [
            FieldDefinitions.DISCONTINUED_DATE["name"],
            FieldDefinitions.CONTINUES["name"],
            FieldDefinitions.CONTINUED_BY["name"]
        ]
    }

    SUBJECT = {
        "name": "subject",
        "label": "Subject classification",
        "fields": [
            FieldDefinitions.SUBJECT["name"]
        ]
    }

    NOTES = {
        "name": "notes",
        "label": "Notes",
        "fields": [
            FieldDefinitions.NOTES["name"],
            FieldDefinitions.NOTE["name"],
            FieldDefinitions.NOTE_DATE["name"],
            FieldDefinitions.NOTE_ID["name"]
        ]
    }

    OPTIONAL_VALIDATION = {
        "name": "optional_validation",
        "label": "Allow save without validation",
        "fields" : [
            FieldDefinitions.OPTIONAL_VALIDATION["name"]
        ]
    }

    BULK_EDIT = {
        "name" : "bulk_edit",
        "label" : "Bulk Edit",
        "fields" : [
            FieldDefinitions.PUBLISHER_NAME["name"],
            FieldDefinitions.PUBLISHER_COUNTRY["name"],
            FieldDefinitions.DOAJ_SEAL["name"],
            FieldDefinitions.OWNER["name"]
        ]
    }


###########################################################
# Define our Contexts
###########################################################

class ApplicationContextDefinitions:
    PUBLIC = {
        "name": "public",
        "fieldsets": [
            FieldSetDefinitions.BASIC_COMPLIANCE["name"],
            FieldSetDefinitions.ABOUT_THE_JOURNAL["name"],
            FieldSetDefinitions.PUBLISHER["name"],
            FieldSetDefinitions.SOCIETY_OR_INSTITUTION["name"],
            FieldSetDefinitions.LICENSING["name"],
            FieldSetDefinitions.EMBEDDED_LICENSING["name"],
            FieldSetDefinitions.COPYRIGHT["name"],
            FieldSetDefinitions.PEER_REVIEW["name"],
            FieldSetDefinitions.PLAGIARISM["name"],
            FieldSetDefinitions.EDITORIAL["name"],
            FieldSetDefinitions.APC["name"],
            FieldSetDefinitions.APC_WAIVERS["name"],
            FieldSetDefinitions.OTHER_FEES["name"],
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

    UPDATE = deepcopy(PUBLIC)
    UPDATE["name"] = "update_request"
    UPDATE["processor"] = application_processors.NewApplication  # FIXME: enter the real processor
    UPDATE["templates"]["form"] = "application_form/update_request.html"

    ASSOCIATE = deepcopy(PUBLIC)
    ASSOCIATE["name"] = "associate_editor"
    ASSOCIATE["fieldsets"] += [
        FieldSetDefinitions.STATUS["name"],
        FieldSetDefinitions.NOTES["name"]
    ]
    ASSOCIATE["processor"] = application_processors.NewApplication  # FIXME: enter the real processor
    ASSOCIATE["templates"]["form"] = "application_form/assed_application.html"

    EDITOR = deepcopy(PUBLIC)
    EDITOR["name"] = "editor"
    EDITOR["fieldsets"] += [
        FieldSetDefinitions.STATUS["name"],
        FieldSetDefinitions.REVIEWERS["name"],
        FieldSetDefinitions.NOTES["name"]
    ]
    EDITOR["processor"] = application_processors.NewApplication  # FIXME: enter the real processor
    EDITOR["templates"]["form"] = "application_form/editor_application.html"

    MANED = deepcopy(PUBLIC)
    MANED["name"] = "admin"
    MANED["fieldsets"] += [
        FieldSetDefinitions.SEAL["name"],
        FieldSetDefinitions.QUICK_REJECT["name"],
        FieldSetDefinitions.REASSIGN["name"],
        FieldSetDefinitions.STATUS["name"],
        FieldSetDefinitions.REVIEWERS["name"],
        FieldSetDefinitions.CONTINUATIONS["name"],
        FieldSetDefinitions.SUBJECT["name"],
        FieldSetDefinitions.NOTES["name"]
    ]
    MANED["processor"] = application_processors.AdminApplication
    MANED["templates"]["form"] = "application_form/maned_application.html"


class JournalContextDefinitions:
    READ_ONLY = {
        "name": "read_only",
        "fieldsets": [
            FieldSetDefinitions.BASIC_COMPLIANCE["name"],
            FieldSetDefinitions.ABOUT_THE_JOURNAL["name"],
            FieldSetDefinitions.PUBLISHER["name"],
            FieldSetDefinitions.SOCIETY_OR_INSTITUTION["name"],
            FieldSetDefinitions.LICENSING["name"],
            FieldSetDefinitions.EMBEDDED_LICENSING["name"],
            FieldSetDefinitions.COPYRIGHT["name"],
            FieldSetDefinitions.PEER_REVIEW["name"],
            FieldSetDefinitions.PLAGIARISM["name"],
            FieldSetDefinitions.EDITORIAL["name"],
            FieldSetDefinitions.APC["name"],
            FieldSetDefinitions.APC_WAIVERS["name"],
            FieldSetDefinitions.OTHER_FEES["name"],
            FieldSetDefinitions.ARCHIVING_POLICY["name"],
            FieldSetDefinitions.REPOSITORY_POLICY["name"],
            FieldSetDefinitions.UNIQUE_IDENTIFIERS["name"],
            FieldSetDefinitions.SUBJECT["name"],
            FieldSetDefinitions.NOTES["name"]
        ],
        "templates": {
            "form" : "application_form/readonly_journal.html",
            "default_field" : "application_form/_field.html",
            "default_group" : "application_form/_group.html"#,
            #"default_list" : "application_form/_list.html"
        },
        "crosswalks": {
            "obj2form": JournalFormXWalk.obj2form,
            "form2obj": JournalFormXWalk.form2obj
        },
        "processor": application_processors.NewApplication # FIXME: enter the real processor
    }

    ASSOCIATE = deepcopy(READ_ONLY)
    ASSOCIATE["name"] = "associate_editor"
    ASSOCIATE["processor"] = application_processors.NewApplication  # FIXME: enter the real processor
    ASSOCIATE["templates"]["form"] = "application_form/assed_journal.html"

    EDITOR = deepcopy(READ_ONLY)
    EDITOR["name"] = "editor"
    EDITOR["fieldsets"] += [
        FieldSetDefinitions.REVIEWERS["name"]
    ]
    EDITOR["processor"] = application_processors.NewApplication  # FIXME: enter the real processor
    EDITOR["templates"]["form"] = "application_form/editor_journal.html"

    MANED = deepcopy(EDITOR)
    MANED["name"] = "admin"
    MANED["fieldsets"] += [
        FieldSetDefinitions.REVIEWERS["name"],
        FieldSetDefinitions.REASSIGN["name"],
        FieldSetDefinitions.OPTIONAL_VALIDATION["name"],
        FieldSetDefinitions.SEAL["name"],
        FieldSetDefinitions.CONTINUATIONS["name"]
    ]
    MANED["processor"] = application_processors.NewApplication  # FIXME: enter the real processor
    MANED["templates"]["form"] = "application_form/maned_journal.html"

    BULK_EDIT = {
        "name" : "bulk_edit",
        "fieldsets" : [
            FieldSetDefinitions.BULK_EDIT["name"]
        ],
        "templates": {
            "form" : "application_form/readonly_journal.html",
            "default_field" : "application_form/_field.html",
            "default_group" : "application_form/_group.html"#,
            #"default_list" : "application_form/_list.html"
        },
        "crosswalks": {
            "obj2form": JournalFormXWalk.obj2form,
            "form2obj": JournalFormXWalk.form2obj
        },
        "processor": application_processors.NewApplication # FIXME: enter the real processor
    }



#######################################################
# Gather all of our form information in one place
#######################################################

APPLICATION_FORMS = {
    "contexts": {
        ApplicationContextDefinitions.PUBLIC["name"]: ApplicationContextDefinitions.PUBLIC,
        ApplicationContextDefinitions.UPDATE["name"]: ApplicationContextDefinitions.UPDATE,
        ApplicationContextDefinitions.ASSOCIATE["name"]: ApplicationContextDefinitions.ASSOCIATE,
        ApplicationContextDefinitions.EDITOR["name"]: ApplicationContextDefinitions.EDITOR,
        ApplicationContextDefinitions.MANED["name"]: ApplicationContextDefinitions.MANED
    },
    "fieldsets": {v['name']: v for k, v in FieldSetDefinitions.__dict__.items() if not k.startswith('_')},
    "fields": {v['name']: v for k, v in FieldDefinitions.__dict__.items() if not k.startswith('_')}
}


JOURNAL_FORMS = {
    "contexts": {
        JournalContextDefinitions.READ_ONLY["name"]: JournalContextDefinitions.READ_ONLY,
        JournalContextDefinitions.BULK_EDIT["name"]: JournalContextDefinitions.BULK_EDIT,
        JournalContextDefinitions.ASSOCIATE["name"]: JournalContextDefinitions.ASSOCIATE,
        JournalContextDefinitions.EDITOR["name"]: JournalContextDefinitions.EDITOR,
        JournalContextDefinitions.MANED["name"]: JournalContextDefinitions.MANED
    },
    "fieldsets": APPLICATION_FORMS["fieldsets"],
    "fields": APPLICATION_FORMS["fields"]
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
        else:
            html_attrs["data-parsley-required-message"] = "This answer is required"
        html_attrs["data-parsley-validate-if-empty"] = "true"

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
        return URLOptionalScheme(message=settings.get('message'))


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
        html_attrs["data-parsley-validate-if-empty"] = "true"
        html_attrs["data-parsley-optional-if"] = settings.get("field")

    @staticmethod
    def wtforms(field, settings):
        return OptionalIf(settings.get("field") or field, settings.get("message"), settings.get("values", []))


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
        return DifferentTo(settings.get("field") or field, settings.get("ignore_empty", True), settings.get("message"))


class RequiredIfBuilder:
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-validate-if-empty"] = "true"
        html_attrs["data-parsley-required-if"] = settings.get("value")
        html_attrs["data-parsley-required-if-field"] = settings.get("field")

    @staticmethod
    def wtforms(field, settings):
        return RequiredIfOtherValue(settings.get("field") or field, settings.get("value"))


class OnlyIfBuilder:
    @staticmethod
    def render(settings, html_attrs):
        # FIXME: front end validator for this does not yet exist
        for f in settings.get('fields'):
            html_attrs["data-parsley-only-if-field"] = f['field']
            html_attrs["data-parsley-only-if-value"] = f.get('value', '')

    @staticmethod
    def wtforms(fields, settings):
        return OnlyIf(settings.get('fields') or fields, settings.get('message'))


class NotIfBuildier:
    @staticmethod
    def render(settings, html_attrs):
        # FIXME: front end validator for this does not yet exist
        for f in settings.get('fields'):
            html_attrs["data-parsley-not-if-field"] = f['field']
            html_attrs["data-parsley-not-if-value"] = f.get('value', '')

    @staticmethod
    def wtforms(fields, settings):
        return NotIf(settings.get('fields') or fields, settings.get('message'))


class GroupMemberBuilder:
    @staticmethod
    def render(settings, html_attrs):
        # FIXME: front end validator for this does not yet exist (do we have an existing one from formcontext?)
        html_attrs["data-parsley-group-member-field"] = settings.get("group_field")

    @staticmethod
    def wtforms(field, settings):
        return GroupMember(settings.get('group_field') or field)


class RequiredValueBuilder:
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-requiredvalue"] = settings.get("value")

    @staticmethod
    def wtforms(field, settings):
        RequiredValue(settings.get("value"), settings.get("message"))


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
            "not_if" : NotIfBuildier.render,
            "required_value" : RequiredValueBuilder.render,
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
            "not_if" : NotIfBuildier.wtforms,
            "required_value" : RequiredValueBuilder.wtforms
        }
    },

    # "all_urls_the_same" : "portality.formcontext.validators.all_urls_the_same",
    # "to_lower" : "portality.formcontext.postprocessing.to_lower",
    # "warn_on_value" : "portality.formcontext.validators.warn_on_value",
    # "clickable_url" : "portality.formcontext.widgets.clickable_url",
}

JAVASCRIPT_FUNCTIONS = {
    # "required_value" : "doaj.forms.validators.requiredValue",
    # "required" : "doaj.forms..validators.required",
    # "is_url" : "doaj.forms.validators.isUrl",
    # "max_tags" : "doaj.forms.validators.maxTags",
    # "stop_words" : "doaj.forms.validators.stopWords",
    # "int_range" : "doaj.forms.validators.intRange",
    # "autocomplete" : "doaj.forms.widgets.autocomplete",

    "clickable_url": "formulaic.widgets.newClickableUrl",
    "select": "formulaic.widgets.newSelect",
    "taglist": "formulaic.widgets.newTagList",
    "multiple_field": "formulaic.widgets.newMultipleField",
    "autocomplete": "formulaic.widgets.newAutocomplete"
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
        wtfargs["widget"] = ListWidgetWithSubfields()
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
        return field.get("input") == "checkbox" and len(field.get("options", [])) == 0 and field.get(
            "options_fn") is None

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        return BooleanField(**wtfargs)


class SelectBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "select" and not field.get("multiple", False)

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        sf = SelectField(**wtfargs)
        if "repeatable" in field:
            sf = FieldList(sf, min_entries=field.get("repeatable", {}).get("initial", 1))
        return sf


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


# TODO: multiple group doesn't work
class GroupBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "group" and field.get("repeatable") is None

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


ApplicationFormFactory = Formulaic(APPLICATION_FORMS, WTFORMS_BUILDERS, function_map=PYTHON_FUNCTIONS, javascript_functions=JAVASCRIPT_FUNCTIONS)
JournalFormFactory = Formulaic(JOURNAL_FORMS, WTFORMS_BUILDERS, function_map=PYTHON_FUNCTIONS, javascript_functions=JAVASCRIPT_FUNCTIONS)