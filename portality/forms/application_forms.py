from portality.lib.formulaic import Formulaic, WTFormsBuilder

from wtforms import StringField, IntegerField, BooleanField, RadioField, SelectMultipleField, SelectField, Form, FormField
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
    InPublicDOAJ,
    DifferentTo
)

from portality.datasets import language_options, country_options
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
        "name" : "boai",
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
            {"required" : {"message" : "You must check this box to continue"}}
        ],
        "contexts" : {
            "editor" : {
                "disabled" : True
            },
            "associate_editor" : {
                "disabled" : True
            }
        },
        "asynchronous_warnings": [
            {"value_must_be" : {"value" : "y"}}
        ]
    }

    OA_STATEMENT_URL = {
        "name" : "oa_statement_url",
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
        "name" : "title",
        "label" : "Journal title",
        "input" : "text",
        "help" : {
            "long_help" : "The journal title must match what is displayed on the website and what is registered at the "
                            "ISSN Portal (https://portal.issn.org/).  For translated titles, you may add the "
                            "translation as an alternative title.",
            "doaj_criteria" : "Title in application form, title at ISSN and website must all match"
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
            "update_request" : {
                "disabled" : True
            }
        }
    }

    ALTERNATIVE_TITLE = {
        "name" : "alternative_title",
        "label" : "Alternative title (including translation of the title)",
        "input" : "text",
        "help" : {
            "long_help" : "The journal title must match what is displayed on the website and what is registered at the "
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
        "name" : "journal_url",
        "label" : "Link to the journal's homepage",
        "input" : "text",
        "validate": [
            "required",
            "is_url",
            "in_public_doaj"    # Check whether the journal url is already in a public DOAJ record
        ],
        "widgets" : [
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
            {"in_public_doaj" : {"field" : "bibjson.ref.journal.exact"}},   # check whether the journal url is already in a public DOAJ record
            {"rejected_application" : {"age" : "6 months"}},     # check that the journal does not have a rejection less than 6 months ago
            "active_application"    # Check that the URL is not related to an active application
        ]
    }

    PISSN = {
        "name" : "pissn",
        "label" : "ISSN (print)",
        "input" : "text",
        "help" : {
            "long_help" : "Must be a valid ISSN, fully registered and confirmed at the ISSN Portal (https://portal.issn.org/)"
                        "The ISSN must match what is given on the journal website.",
            "doaj_criteria" : "ISSN must be provided"
        },
        "validate" : [
            {"optional_if" : {"field" : "eissn", "message" : "You must provide one or both of an online ISSN or a print ISSN"}},
            "in_public_doaj",
            {"is_issn" : {"message" : "This is not a valid ISSN"}},
            {"different_to" : {"field" : "eissn"}}
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
            "in_public_doaj",  # check whether the journal url is already in a public DOAJ record
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
            "in_public_doaj",
            {"is_issn": {"message": "This is not a valid ISSN"}},
            {"different_to": {"field": "pissn"}}
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
            "in_public_doaj",  # check whether the journal url is already in a public DOAJ record
            {"rejected_application": {"age": "6 months"}},
            "active_application"  # Check that the ISSN is not related to an active application
        ]
    }

    KEYWORDS = {
        "name" : "keywords",
        "label" : "Up to six subject keywords in English",
        "input" : "taglist",
        "help": {
            "long_help": "Only 6 keywords are allowed. Choose words that describe the subject matter of the journal "
                         "and not the journal's qualities. Keywords must be in English and separated by a comma.",
        },
        "validate" : [
            "required",
            {"stop_words" : {"disallowed" : STOP_WORDS}},
            {"max_tags" : { "max" : 6 }}
        ],
        "postprocessing" : [
            "to_lower"  # FIXME: this might just be a feature of the crosswalk
        ],
        "widgets" : [
            {
                "taglist" : {
                    "maximumSelectionSize" : 6,
                    "stopWords" : STOP_WORDS
                }
            }
        ],
        "attr" : {
            "class" : "input-xlarge"
        },
        "contexts" : {
            "editor" : {
                "disabled" : True
            },
            "associate_editor" : {
                "disabled" : True
            }
        }
    }

    LANGUAGE = {
        "name" : "language",
        "label" : "Languages in which the journal accepts manuscripts",
        "input" : "select",
        "multiple" : True,
        "options_fn" : "iso_language_list",
        "validate" : [
            "required"
        ],
        "widgets" : [
            {"select" : {}}
        ],
        "attr" : {
            "class" : "input-xlarge"
        }
    }

    PUBLISHER = {
        "name" : "publisher",
        "label" : "Publisher",
        "input" : "group",
        "subfields" : [
            "publisher_name",
            "publisher_country"
        ],
        "template" : "application_form/_group.html"
    }

    PUBLISHER_NAME = {
        "subfield": True,
        "name" : "publisher_name",
        "label" : "Name",
        "input" : "text",
        "validate": [
            "required"
        ],
        "widgets" : [
            {"autocomplete" : {"field" : "publisher_name"}}
        ]
    }

    PUBLISHER_COUNTRY = {
        "subfield": True,
        "name": "publisher_country",
        "label": "Country",
        "input": "select",
        "options_fn": "iso_country_list",
        "help" : {
            "long_help" : "The country where the publisher carries out its business operations and is registered.",
            "doaj_criteria" : "You must provide a publisher country"
        },
        "validate": [
            "required"
        ],
        "widgets": [
            {"select": {}}
        ],
        "attr" : {
            "class" : "input-xlarge"
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
        ],
        "template" : "application_form/_group.html"
    }

    INSTITUTION_NAME = {
        "subfield": True,
        "name": "institution_name",
        "label": "Name",
        "input": "text",
        "widgets": [
            {"autocomplete": {"field": "institution_name"}}
        ]
    }

    INSTITUTION_COUNTRY = {
        "subfield": True,
        "name": "institution_country",
        "label": "Country",
        "input": "select",
        "options_fn": "iso_country_list",
        "help": {
            "short_help" : "The society or institution responsible for the journal",
            "long_help": "Some societies or institutions are linked to a journal in some way but are not responsible "
                        "for publishing it. The publisher can be a separate organisation. If your journal is linked to "
                        "a society or other type of institution, enter that here."
        },
        "widgets": [
            {"select": {}}
        ],
        "attr" : {
            "class" : "input-xlarge"
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
        "name" : "license",
        "label": "License(s) permitted by the journal",
        "input": "checkbox",
        "multiple" : True,
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
        "name" : "license_attributes",
        "label" : "Select all the attributes that your license has",
        "input" : "checkbox",
        "multiple" : True,
        "conditional" : [
            {"field" : "license", "value" : "Publisher's own license"}
        ],
        "options" : [
            {"display" : "Attribution", "value" : "BY"},
            {"display" : "Share Alike", "value" : "SA"},
            {"display" : "No Derivatives", "value" : "ND"},
            {"display" : "No Commercial Usage", "value" : "NC"}
        ],
        "help": {
            "doaj_criteria": "Content must be licenced"
        }
    }

    LICENSE_TERMS_URL = {
        "name" : "license_terms_url",
        "label" : "Link to the page where the license terms are stated",
        "input" : "text",
        "validate" : [
            "required",
            "is_url"
        ],
        "help": {
            "doaj_criteria": "You must provide a link to your license terms"
        },
        "widgets" : [
            "clickable_url"
        ]
    }

    LICENSE_DISPLAY = {
        "name" : "license_display",
        "label" : "Does the journal embed and/or display licensing information in its articles?",
        "input" : "checkbox",
        "multiple" : True,
        "help" : {
            "long_help" : "Licensing information must be displayed or embedded on every PDF or in the full text of the "
                        "HTML articles. We do not accept licensing information that is only displayed in other parts of "
                        "the site.",
            "seal_criteria" : "If the answer is Embed"
        },
        "options": [
            {"display": "Embed", "value": "Embed"},
            {"display": "Display", "value": "Display"},
            {"display": "No", "value": "No", "exclusive" : True}
        ],
        "validate" : [
            "required"
        ]
    }

    LICENSE_DISPLAY_EXAMPLE_URL = {
        "name" : "license_display_example_url",
        "label" : "Link to a recent article displaying or embedding a license in the full text",
        "input" : "text",
        "validate" : [
            "required",
            "is_url"
        ],
        "widgets" : [
            "clickable_url"
        ]
    }

    COPYRIGHT_AUTHOR_RETAINS = {
        "name" : "copyright_author_retains",
        "label" : "For all the licenses you have indicated above, do authors or their institutions retain the copyright "
                  "and full publishing rights without restrictions?",
        "input" : "checkbox",
        "validate" : [
            "required"
        ],
        "help" : {
            "seal_criteria" : "The author must retain the copyright"
        },
        "asynchronous_warnings" : [
            {"required_value" : {"value" : "y"}}
        ]
    }

    COPYRIGHT_URL = {
        "name" : "copyright_url",
        "label" : "Link to the journal's copyright terms",
        "input" : "text",
        "validate" : [
            "required",
            "is_url"
        ],
        "widgets" : [
            "clickable_url"
        ]
    }

    REVIEW_PROCESS = {
        "name" : "peer_review",
        "label": "DOAJ only accepts peer-reviewed journals."
                    "Which type(s) of peer review does this journal use?",
        "input": "checkbox",
        "multiple" : True,
        "options": [
            {"display": "Editorial review", "value": "editorial_review"},
            {"display": "Peer review", "value": "peer_review"},
            {"display": "Blind peer review", "value": "blind_peer_review"},
            {"display": "Double blind peer review", "value": "double_blind_peer_review"},
            {"display": "Post-publication peer review", "value": "post_publication_peer_review"},
            {"display": "Open peer review", "value": "open_peer_review"},
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
        "name" : "review_process_other",
        "subfield": True,
        "label" : "Other",
        "input": "text",
        "help": {
            "placeholder": "Other peer review"
        },
        "conditional": [{"field": "review_process", "value": "other"}],
        "validate" : [
            {"required_if" : {"field" : "review_process", "value" : "other"}}
        ],
        "asynchronous_warning": [
            {"warn_on_value": {"value": "None"}}
        ]
    }

    REVIEW_URL = {
        "name" : "review_url",
        "label" : "Link to the journal's peer review policy",
        "input" : "text",
        "help" : {
            "doaj_criteria" : "You must provide a URL"
        },
        "validate" : [
            "required",
            "is_url"
        ],
        "widgets" : [
            "clickable_url"
        ]
    }

    PLAGIARISM_DETECTION = {
        "name" : "plagiarism_detection",
        "label" : "Does the journal routinely screen article submissions for plagiarism?",
        "input" : "radio",
        "options" : [
            {"display" : "Yes", "value" : True},
            {"display" : "No", "value" : False}
        ],
        "validate" : [
            "required"
        ]
    }

    PLAGIARISM_URL = {
        "name" : "plagiarism_url",
        "label" : "Link to the journal's plagiarism policy",
        "input" : "text",
        "conditional": [{"field": "plagiarism_detection", "value": True}],
        "help": {
            "doaj_criteria": "You must provide a URL"
        },
        "validate" : [
            "required",
            "is_url"
        ],
        "widgets" : [
            "clickable_url"
        ]
    }


FIELDS = {
    FieldDefinitions.BOAI["name"] : FieldDefinitions.BOAI,
    FieldDefinitions.OA_STATEMENT_URL["name"] : FieldDefinitions.OA_STATEMENT_URL,

    FieldDefinitions.TITLE["name"] : FieldDefinitions.TITLE,
    FieldDefinitions.ALTERNATIVE_TITLE["name"] : FieldDefinitions.ALTERNATIVE_TITLE,
    FieldDefinitions.JOURNAL_URL["name"] : FieldDefinitions.JOURNAL_URL,
    FieldDefinitions.PISSN["name"] : FieldDefinitions.PISSN,
    FieldDefinitions.EISSN["name"] : FieldDefinitions.EISSN,
    FieldDefinitions.KEYWORDS["name"] : FieldDefinitions.KEYWORDS,
    FieldDefinitions.LANGUAGE["name"] : FieldDefinitions.LANGUAGE,
    FieldDefinitions.PUBLISHER["name"] : FieldDefinitions.PUBLISHER,
    FieldDefinitions.PUBLISHER_NAME["name"] : FieldDefinitions.PUBLISHER_NAME,
    FieldDefinitions.PUBLISHER_COUNTRY["name"] : FieldDefinitions.PUBLISHER_COUNTRY,
    FieldDefinitions.INSTITUTION["name"] : FieldDefinitions.INSTITUTION,
    FieldDefinitions.INSTITUTION_NAME["name"] : FieldDefinitions.INSTITUTION_NAME,
    FieldDefinitions.INSTITUTION_COUNTRY["name"] : FieldDefinitions.INSTITUTION_COUNTRY,

    FieldDefinitions.LICENSE["name"] : FieldDefinitions.LICENSE,
    FieldDefinitions.LICENSE_ATTRIBUTES["name"] : FieldDefinitions.LICENSE_ATTRIBUTES,
    FieldDefinitions.LICENSE_TERMS_URL["name"] : FieldDefinitions.LICENSE_TERMS_URL,
    FieldDefinitions.LICENSE_DISPLAY["name"] : FieldDefinitions.LICENSE_DISPLAY,
    FieldDefinitions.LICENSE_DISPLAY_EXAMPLE_URL["name"] : FieldDefinitions.LICENSE_DISPLAY_EXAMPLE_URL
}

##########################################################
# Define our fieldsets
##########################################################

class FieldSetDefinitions:
    BASIC_COMPLIANCE = {
        "name" : "basic_compliance",
        "label" : "Basic Compliance",
        "fields" : [
            FieldDefinitions.BOAI["name"],
            FieldDefinitions.OA_STATEMENT_URL["name"]
        ]
    }

    ABOUT_THE_JOURNAL = {
        "name" : "about_the_journal",
        "label" : "About the Journal",
        "fields" : [
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
        "name" : "licensing",
        "label" : "Licensing",
        "fields" : [
            FieldDefinitions.LICENSE["name"],
            FieldDefinitions.LICENSE_ATTRIBUTES["name"],
            FieldDefinitions.LICENSE_TERMS_URL["name"],
            FieldDefinitions.LICENSE_DISPLAY["name"],
            FieldDefinitions.LICENSE_DISPLAY_EXAMPLE_URL["name"]
        ]
    }


###########################################################
# Define our Contexts
###########################################################

class ContextDefinitions:
    PUBLIC = {
        "name" : "public",
        "fieldsets" : [
            FieldSetDefinitions.BASIC_COMPLIANCE["name"],
            FieldSetDefinitions.ABOUT_THE_JOURNAL["name"],
            FieldSetDefinitions.LICENSING["name"]
        ],
        "asynchronous_warnings": [
            "all_urls_the_same"
        ],
        "templates": {
            "form" : "application_form/public_application.html",
            "default_field" : "application_form/_field.html"
        },
        "crosswalks": {
            "obj2form" : ApplicationFormXWalk.obj2form,
            "form2obj" : ApplicationFormXWalk.form2obj
        },
        "processor": application_processors.PublicApplication,
    }


FORMS = {
    "contexts" : {
        ContextDefinitions.PUBLIC["name"] : ContextDefinitions.PUBLIC
    },
    "fieldsets" : {
        FieldSetDefinitions.BASIC_COMPLIANCE["name"] : FieldSetDefinitions.BASIC_COMPLIANCE,
        FieldSetDefinitions.ABOUT_THE_JOURNAL["name"] : FieldSetDefinitions.ABOUT_THE_JOURNAL,
        FieldSetDefinitions.LICENSING["name"] : FieldSetDefinitions.LICENSING
    },
    "fields" : FIELDS
}


_FORMS = {
    "contexts" : {
        "public" : {
            "fieldsets" : [
                "public_priority",
                "oac",
                "about",
                "editorial"
            ],
            "asynchronous_warnings" : [
                "all_urls_the_same"
            ],
            "template" : "application_form/public_application.html",
            "crosswalks" : {
                "obj2form" : "portality.formcontext.form_definitions.application_obj2form",
                "form2obj" : "portality.formcontext.form_definitions.application_form2obj"
            },
            "processor" : "portality.formcontext.formcontext.PublicApplication"
        }
    },
    "fieldsets": {
        "oac": {
            "label" : "Open access compliance",
            "fields" : [
                "boai",
                "oa_statement_url"
            ]
        },
        "about" : {
            "label" : "About the journal",
            "fields" : [
                "country",
                "keywords",
                "licensing"
            ]
        },
        "editorial" : {
            "label" : "Editorial",
            "fields" : [
                "submission_time",
                "peer_review",
                "peer_review_other"
            ]
        },
        "public_priority": {
            "label" : "Pre-Qualification Questions",
            "fields" : [
                "boai"
            ],
        }
    },
    "fields": {
        "boai": {
            "label": "DOAJ adheres to the BOAI [definition of open access LINK].  This means that users are"
                "permitted 'to read, download, copy, distribute, print, search, or link to the full texts of articles,"
                "or use them for any other lawful purpose, without financial, legal, or technical barriers other than"
                "those inseparable from gaining access to the internet itself.' Does the journal adhere to this"
                "definition of open access?",
            "input": "checkbox",
            "help": {
                "description": "",
                "tooltip": "For a journal to be indexed in DOAJ, it must fulfil the BOAI definition of open access",
                "doaj_criteria": "You must answer 'Yes'"
            },
            "validate": [
                {"required" : {"message" : "You must check this box to continue"}}
            ],
            "contexts" : {
                "editor" : {
                    "disabled" : True
                },
                "associate_editor" : {
                    "disabled" : True
                }
            }
        },
        "oa_statement_url" : {
            "label" : "What is the URL for the journal's open access statement?",
            "input" : "text",
            "conditional" : [{"field" : "boai", "value" : "y"}],
            "help": {
                "placeholder" : "OA Statement URL",
                "description": "Must start with https://, http://, or www.",
                "tooltip": "Here is an example of a suitable Open Access statement that meets our criteria: "
                        "This is an open access journal which means that all content is freely available without charge" 
                        "to the user or his/her institution. Users are allowed to read, download, copy, distribute," 
                        "print, search, or link to the full texts of the articles, or use them for any other lawful" 
                        "purpose, without asking prior permission from the publisher or the author. This is in accordance"
                        "with the BOAI definition of open access.",
                "doaj_criteria": "You must provide a URL"
            },
            "validate" : [
                "required",
                "is_url"
            ],
            "widgets" : [
                "clickable_url"
            ],
            "attr" : {
                "type" : "url"
            }
        },
        "country" : {
            "label" : "Country of Publisher",
            "input" : "select",
            "options_fn" : "iso_country_list",
            "multiple" : False,
            "help": {
                "description": "",
                "tooltip": """The country where the publisher carries out its business operations and is registered.""",
            },
            "validate" : [
                "required"
            ],
            "widgets" : [
                {"select" : {}}
            ],
            "contexts" : {
                "editor" : {
                    "disabled" : True
                },
                "associate_editor" : {
                    "disabled" : True
                }
            },
            "attr" : {
                "class" : "input-xlarge"
            }
        },
        "keywords" : {
            "label" : "Add 6 keywords that describe the subject matter of the journal",
            "input" : "taglist",
            "help": {
                "description": "Up to 6 keywords, separated with a comma; must be in English",
                "tooltip": "Only 6 keywords are allowed. Choose words that describe the subject matter of the"
                           "journal and not the journal's qualities. All keywords must be in English.",
            },
            "validate" : [
                "required",
                {"stop_words" : {"disallowed" : ["a", "and"]}},
                {"max_tags" : { "max" : 6 }}
            ],
            "postprocessing" : [
                "to_lower"
            ],
            "widgets" : [
                {
                    "taglist" : {
                        "maximumSelectionSize" : 6,
                        "stopWords" : ["a", "and"]
                    }
                }
            ],
            "attr" : {
                "class" : "input-xlarge"
            },
            "contexts" : {
                "editor" : {
                    "disabled" : True
                },
                "associate_editor" : {
                    "disabled" : True
                }
            }
        },
        "licensing" : {
            "label" : "Indicate which licenses may be applied to the journal content.",
            "input" : "checkbox",
            "options" : [
                {"display" : "CC BY", "value" : "CC BY"},
                {"display" : "CC BY-SA", "value" : "CC BY-SA"},
                {"display" : "CC BY-ND", "value" : "CC BY-ND"},
                {"display" : "CC BY-NC", "value" : "CC BY-NC"},
                {"display" : "CC BY-NC-SA", "value" : "CC BY-NC-SA"},
                {"display" : "CC BY-NC-ND", "value" : "CC BY-NC-ND"},
                {"display" : "CC0", "value" : "CC0"},
                {"display" : "Publisher's own license", "value" : "Publisher's own license", "exclusive" : True},
            ],
            "help": {
                "description": "Select all licenses permitted by this journal.",
                "tooltip": "The journal must use some form of licensing to be considered for indexing in DOAJ. "
                        "If Creative Commons licensing is not used, then select 'Publisher's own license' and enter "
                        "more details below.",
                "doaj_criteria" : "Content must be licenced",
                "seal_criteria" : "Yes: CC BY, CC BY-SA, CC BY-NC"
            },
            "validate" : [
                "required"
            ]
        },
        "submission_time" : {
            "label" : "Average number of weeks between article submission & publication",
            "input" : "number",
            "datatype" : "integer",
            "help": {
                "description": "Enter a number"
            },
            "validate" : [
                "required",
                {"int_range" : {"gte" : 1, "lte" : 100}}
            ],
            "asynchronous_warning" : [
                {"int_range" : {"lte" : 2}}
            ],
            "attr" : {
                "min" : "1",
                "max" : "100"
            }
        },
        "peer_review" : {
            "label" : "What type of peer review is used by the journal?",
            "input" : "checkbox",
            "options" : [
                {"display" : "Editorial review", "value" : "editorial_review"},
                {"display" : "Peer review", "value" : "peer_review"},
                {"display" : "Blind peer review", "value" : "blind_peer_review"},
                {"display" : "Double blind peer review", "value" : "double_blind_peer_review"},
                {"display" : "Post-publication peer review", "value" : "post_publication_peer_review"},
                {"display" : "Open peer review", "value" : "open_peer_review"},
                {"display" : "Other", "value" : "other", "subfields" : ["peer_review_other"]}
            ],
            "help": {
                "description": "Select all that apply",
                "tooltip": """'Editorial review' is only valid for journals in the Humanities""",
                "doaj_criteria" : "Peer review must be carried out"
            },
            "validate" : [
                "required"
            ]
        },
        "peer_review_other": {
            "subfield" : True,
            "input" : "text",
            "help" : {
                "placeholder" : "Other peer review"
            },
            "conditional" : [{"field" : "peer_review", "value" : "other"}],
            "asynchronous_warning" : [
                {"warn_on_value" : {"value" : "None"}}
            ]
        }
    }

}


#######################################################
# Options lists
#######################################################

def iso_country_list(field):
    cl = []
    for v, d in country_options:
        cl.append({"display" : d, "value" : v})
    return cl


def iso_language_list(field):
    cl = []
    for v, d in language_options:
        cl.append({"display" : d, "value" : v})
    return cl


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
        return validators.DataRequired(message=settings.get("message"))


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


class InPublicDOAJBuilder:
    @staticmethod
    def render(settings, html_attrs):
        # FIXME: not yet implemented in the front end, so setting here is speculative
        html_attrs["data-parsley-in-public-doaj"] = settings.get("field")

    @staticmethod
    def wtforms(field, settings):
        return InPublicDOAJ(settings.get("field"), message=settings.get("message"))

class OptionalIfBuilder:
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-optional-if"] = settings.get("field")

    @staticmethod
    def wtforms(field, settings):
        return OptionalIf(settings.get("field"))


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
        return DifferentTo(settings.get("field"))


#########################################################
# Crosswalks
#########################################################

PYTHON_FUNCTIONS = {
    "options" : {
        "iso_country_list" : iso_country_list,
        "iso_language_list" : iso_language_list,
    },
    "validate" : {
        "render" : {
            "required" : RequiredBuilder.render,
            "is_url" : IsURLBuilder.render,
            "int_range" : IntRangeBuilder.render,
            "in_public_doaj" : InPublicDOAJBuilder.render,
            "optional_if" : OptionalIfBuilder.render,
            "is_issn": IsISSNBuilder.render,
            "different_to" : DifferentToBuilder.render
        },
        "wtforms" : {
            "required" : RequiredBuilder.wtforms,
            "is_url" : IsURLBuilder.wtforms,
            "max_tags" : MaxTagsBuilder.wtforms,
            "int_range" : IntRangeBuilder.wtforms,
            "stop_words" : StopWordsBuilder.wtforms,
            "in_public_doaj" : InPublicDOAJBuilder.wtforms,
            "optional_if" : OptionalIfBuilder.wtforms,
            "is_issn" : IsISSNBuilder.wtforms,
            "different_to" : DifferentToBuilder.wtforms
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

    "clickable_url" : "formulaic.widgets.newClickableUrl",
    "select" : "formulaic.widgets.newSelect",
    "taglist" : "formulaic.widgets.newTagList"
}


##############################################################
## Additional WTForms bits, that will probably need to be
## moved out to the correct modules before wrapping up
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
                    html.append('<span class="{x}_container" {y}>'.format(x=sf.name, y=style))
                    html.append(sf.render_form_control())
                    html.append("</span>")

            html.append("</li>")

        html.append('</%s>' % self.html_tag)
        return HTMLString(''.join(html))


##########################################################
## Mapping from configurations to WTForms builders
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
        return field.get("input") == "select"

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
        return StringField(**wtfargs)


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
        return field.get("input") == "group"

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        fields = [formulaic_context.get(subfield) for subfield in field.get("subfields", [])]
        klazz = formulaic_context.make_wtform_class(fields)
        return FormField(klazz)


WTFORMS_BUILDERS = [
    RadioBuilder,
    MultiCheckboxBuilder,
    SingleCheckboxBuilder,
    SelectBuilder,
    MultiSelectBuilder,
    TextBuilder,
    TagListBuilder,
    IntegerBuilder,
    GroupBuilder
]

ApplicationFormFactory = Formulaic(FORMS, WTFORMS_BUILDERS, function_map=PYTHON_FUNCTIONS, javascript_functions=JAVASCRIPT_FUNCTIONS)
