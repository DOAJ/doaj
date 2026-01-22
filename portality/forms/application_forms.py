"""
~~ApplicationForm:Feature~~
"""
from copy import deepcopy

from wtforms import StringField, TextAreaField, IntegerField, BooleanField, SelectMultipleField, \
    SelectField, \
    FormField, FieldList, HiddenField, DateField
from wtforms import widgets, validators
from wtforms.widgets.core import html_params, HTMLString

from portality import constants
from portality import regex
from portality.core import app
from portality.crosswalks.application_form import ApplicationFormXWalk
from portality.crosswalks.journal_form import JournalFormXWalk
from portality.datasets import language_options, country_options, currency_options
from portality.forms import application_processors
from portality.forms.fields import TagListField, NestedFormField, UnconstrainedRadioField
from portality.forms.validate import (
    HTTPURL,
    OptionalIf,
    MaxLen,
    RegexpOnTagList,
    StopWords,
    ISSNInPublicDOAJ,
    JournalURLInPublicDOAJ,
    DifferentTo,
    RequiredIfOtherValue,
    OnlyIf,
    OnlyIfExists,
    NotIf,
    GroupMember,
    RequiredValue,
    BigEndDate,
    ReservedUsernames,
    CustomRequired,
    OwnerExists,
    NoScriptTag,
    Year,
    CurrentISOCurrency,
    CurrentISOLanguage,
    DateInThePast
)
from portality.lib import dates
from portality.lib.formulaic import Formulaic, WTFormsBuilder, FormulaicContext, FormulaicField
from portality.models import EditorGroup
from portality.regex import ISSN, ISSN_COMPILED
from portality.ui.messages import Messages
from portality.ui import templates

# Stop words used in the keywords field
STOP_WORDS = [
    "open access",
    "high quality",
    "peer-reviewed",
    "peer-review",
    "peer review",
    "peer reviewed",
    "quality",
    "medical journal",
    "multidisciplinary",
    "multi-disciplinary",
    "multi-disciplinary journal",
    "interdisciplinary",
    "inter disciplinary",
    "inter disciplinary research",
    "international journal",
    "journal",
    "scholarly journal",
    "open science",
    "impact factor",
    "scholarly",
    "research",
    "research journal"
]


########################################################
# Define all our individual fields
########################################################

class FieldDefinitions:
    # ~~->$ BOAI:FormField~~
    BOAI = {
        "name": "boai",
        "label": "Does the journal adhere to DOAJ’s definition of open access?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y"},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": ["See <a href='https://blog.doaj.org/2020/11/17/"
                          "what-does-doaj-define-as-open-access/' "
                          "target='_blank' rel='noopener'>"
                          "DOAJ’s definition of open access explained "
                          "in full</a>."],
            "doaj_criteria": "You must answer 'Yes'"
        },
        "validate": [
            {"required": {"message": "You must answer <strong>Yes</strong> to continue"}},
            {"required_value": {"value": "y"}}
        ],
        "contexts": {
            "admin": {
                "validate": []
            },
            "editor": {
                "validate": [],
                "disabled": True
            },
            "associate_editor": {
                "validate": [],
                "disabled": True
            }
        }
    }

    # ~~->$ OAStatementURL:FormField~~
    OA_STATEMENT_URL = {
        "name": "oa_statement_url",
        "label": "The journal website must display its open access statement. Where can we find this information?",
        "input": "text",
        "help": {
            "long_help": ["Here is an example of a suitable Open Access "
                          "statement that meets our criteria: <blockquote>This"
                          " is an open access journal, which means that all "
                          "content is freely available without charge to the "
                          "user or his/her institution. Users are allowed to "
                          "read, download, copy, distribute, print, search, or"
                          " link to the full texts of the articles, or use "
                          "them for any other lawful purpose, without asking "
                          "prior permission from the publisher or the author. "
                          "This is in accordance with the BOAI definition of "
                          "open access.</blockquote>"],
            "short_help": "Link to the journal’s open access statement",
            "placeholder": "https://www.my-journal.com/open-access"
        },
        "validate": [
            {"required": {"message": "Enter the URL for the journal’s Open Access statement page"}},
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ],
        "attr": {
            "type": "url"
        }
    }

    # ~~->$ Title:FormField~~
    TITLE = {
        "name": "title",
        "label": "Journal title",
        "input": "text",
        "help": {
            "long_help": ["The journal title must match what is displayed on the website and what is registered at the "
                          "<a href='https://portal.issn.org/' target='_blank' rel='noopener'> ISSN Portal</a>.",
                          "For translated titles, you may add the "
                          "translation as an alternative title."],
            "placeholder": "Journal title",
            "doaj_criteria": "Title in application form, title at ISSN and website must all match"
        },
        "validate": [
            {"required": {"message": "Enter the journal’s name"}},
            "no_script_tag"  # ~~^-> NoScriptTag:FormValidator
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "full_contents"  # ~~^->FullContents:FormWidget~~
        ],
        "contexts": {
            "admin": {
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            },
            "editor": {
                "disabled": True,
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            },
            "associate_editor": {
                "disabled": True,
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            },
            "update_request": {
                "disabled": True
            }
        }
    }

    # ~~->$ AlternativeTitle:FormField~~
    ALTERNATIVE_TITLE = {
        "name": "alternative_title",
        "label": "Alternative title (including translation of the title)",
        "input": "text",
        "optional": True,
        "help": {
            "placeholder": "Ma revue"
        },
        "validate": [
            "no_script_tag"  # ~~^-> NoScriptTag:FormValidator
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            {"full_contents": {"empty_disabled": "[The journal has no alternative title]"}}
            # ~~^->FullContents:FormWidget~~
        ],
        "contexts": {
            "update_request": {
                "disabled": True
            },
            "admin": {
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            },
            "associate_editor": {
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            },
            "editor": {
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            }
        }
    }

    # ~~->$ JournalURL:FormField~~
    JOURNAL_URL = {
        "name": "journal_url",
        "label": "Link to the journal’s homepage",
        "input": "text",
        "validate": [
            "required",
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ],
        "help": {
            "placeholder": "https://www.my-journal.com"
        },
        "contexts": {
            "public": {
                "validate": [
                    {"required": {"message": "Enter the URL for the journal’s <strong>homepage</strong>"}},
                    "is_url",  # ~~^->IsURL:FormValidator~~
                    "journal_url_in_public_doaj"  # ~~^-> JournalURLInPublicDOAJ:FormValidator~~
                ],
            }
        }
    }

    # ~~->$ PISSN:FormField~~
    PISSN = {
        "name": "pissn",
        "label": "ISSN (print)",
        "input": "text",
        "help": {
            "long_help": ["Must be a valid ISSN, fully registered and confirmed at the "
                          "<a href='https://portal.issn.org/' target='_blank' rel='noopener'> ISSN Portal</a>.",
                          "Use the link under the ISSN you provided to check it.",
                          "The ISSN must match what is given on the journal website."],
            "short_help": "For example, 2049-3630",
            "doaj_criteria": "ISSN must be provided"
        },
        "validate": [
            {"optional_if": {"field": "eissn",  # ~~^-> OptionalIf:FormValidator~~
                             "message": "You must provide <strong>one or both</strong> an online ISSN or a print ISSN"}},
            {"is_issn": {"message": "This is not a valid ISSN"}},  # ~~^-> IsISSN:FormValidator~~
            {"different_to": {"field": "eissn", "message": "This field must contain a different value to 'ISSN ("
                                                           "online)'"}}  # ~~^-> DifferetTo:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "full_contents",  # ~~^->FullContents:FormWidget~~
            "issn_link"  # ~~^->IssnLink:FormWidget~~
        ],
        "contexts": {
            "public": {
                "validate": [
                    {"optional_if": {"field": "eissn",  # ~~^-> OptionalIf:FormValidator~~
                                     "message": "You must provide <strong>one or both</strong> an online ISSN or a print ISSN"}},
                    {"is_issn": {"message": "This is not a valid ISSN"}},  # ~~^-> IsISSN:FormValidator~~
                    {"different_to": {"field": "eissn",
                                      "message": "This field must contain a different value to 'ISSN ("
                                                 "online)'"}},  # ~~^-> DifferetTo:FormValidator~~
                    "issn_in_public_doaj"
                ],
            },
            "admin": {
                "help": {
                    "long_help": ["Must be a valid ISSN, fully registered and confirmed at the "
                                  "<a href='https://portal.issn.org/' target='_blank' rel='noopener'> ISSN Portal</a>.",
                                  "The ISSN must match what is given on the journal website."],
                    "placeholder": "",
                    "doaj_criteria": "ISSN must be provided"
                },
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    "autocheck",  # ~~^-> Autocheck:FormWidget~~
                    "issn_link"  # ~~^->IssnLink:FormWidget~~
                ]
            },
            "editor": {
                "disabled": True,
                "help": {
                    "long_help": ["Must be a valid ISSN, fully registered and confirmed at the "
                                  "<a href='https://portal.issn.org/' target='_blank' rel='noopener'> ISSN Portal</a>.",
                                  "The ISSN must match what is given on the journal website."],
                    "placeholder": "",
                    "doaj_criteria": "ISSN must be provided"
                },
            },
            "associate_editor": {
                "disabled": True,
                "help": {
                    "long_help": ["Must be a valid ISSN, fully registered and confirmed at the "
                                  "<a href='https://portal.issn.org/' target='_blank' rel='noopener'> ISSN Portal</a>.",
                                  "The ISSN must match what is given on the journal website."],
                    "placeholder": "",
                    "doaj_criteria": "ISSN must be provided"
                }
            },
            "update_request": {
                "disabled": True
            }
        }
    }

    # ~~->$ EISSN:FormField~~
    EISSN = {
        "name": "eissn",
        "label": "ISSN (online)",
        "input": "text",
        "help": {
            "long_help": ["Must be a valid ISSN, fully registered and confirmed at the "
                          "<a href='https://portal.issn.org/' target='_blank' rel='noopener'> ISSN Portal</a>.",
                          "Use the link under the ISSN you provided to check it.",
                          "The ISSN must match what is given on the journal website."],
            "short_help": "For example, 0378-5955",
            "doaj_criteria": "ISSN must be provided"
        },
        "validate": [
            {"optional_if": {"field": "pissn",  # ~~^-> OptionalIf:FormValidator~~
                             "message": "You must provide <strong>one or both</strong> an online ISSN or a print ISSN"}},
            {"is_issn": {"message": "This is not a valid ISSN"}},  # ~~^-> IsISSN:FormValidator~~
            {"different_to": {"field": "pissn",
                              "message": "This field must contain a different value to 'ISSN (print)'"}}
            # ~~^-> DifferetTo:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "full_contents",  # ~~^->FullContents:FormWidget~~
            "issn_link"  # ~~^->IssnLink:FormWidget~~
        ],
        "contexts": {
            "public": {
                "validate": [
                    {"optional_if": {"field": "pissn",  # ~~^-> OptionalIf:FormValidator~~
                                     "message": "You must provide <strong>one or both</strong> an online ISSN or a print ISSN"}},
                    {"is_issn": {"message": "This is not a valid ISSN"}},  # ~~^-> IsISSN:FormValidator~~
                    {"different_to": {"field": "pissn",
                                      "message": "This field must contain a different value to 'ISSN (print)'"}},
                    # ~~^-> DifferetTo:FormValidator~~
                    "issn_in_public_doaj"
                ]
            },
            "admin": {
                "help": {
                    "long_help": ["Must be a valid ISSN, fully registered and confirmed at the "
                                  "<a href='https://portal.issn.org/' target='_blank' rel='noopener'> ISSN Portal</a>.",
                                  "The ISSN must match what is given on the journal website."],
                    "placeholder": "",
                    "doaj_criteria": "ISSN must be provided"
                },
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    "autocheck",  # ~~^-> Autocheck:FormWidget~~
                    "issn_link"  # ~~^->IssnLink:FormWidget~~
                ]
            },
            "editor": {
                "disabled": True,
                "help": {
                    "long_help": ["Must be a valid ISSN, fully registered and confirmed at the "
                                  "<a href='https://portal.issn.org/' target='_blank' rel='noopener'> ISSN Portal</a>.",
                                  "The ISSN must match what is given on the journal website."],
                    "placeholder": "",
                    "doaj_criteria": "ISSN must be provided"
                },
            },
            "associate_editor": {
                "disabled": True,
                "help": {
                    "long_help": ["Must be a valid ISSN, fully registered and confirmed at the "
                                  "<a href='https://portal.issn.org/' target='_blank' rel='noopener'> ISSN Portal</a>.",
                                  "The ISSN must match what is given on the journal website."],
                    "placeholder": "",
                    "doaj_criteria": "ISSN must be provided"
                }
            },
            "update_request": {
                "disabled": True,
                "validate": [
                    {"optional_if": {"field": "pissn",  # ~~^-> OptionalIf:FormValidator~~
                                     "message": "You must provide <strong>one or both</strong> an online ISSN or a print ISSN"}},
                    {"is_issn": {"message": "This is not a valid ISSN"}},  # ~~^-> IsISSN:FormValidator~~
                    {"different_to": {"field": "pissn",  # ~~^-> DifferetTo:FormValidator~~
                                      "message": "This field must contain a different value to 'ISSN (print)'"}}
                ]
            }
        }
    }

    # ~~->$ Keywords:FormField~~
    KEYWORDS = {
        "name": "keywords",
        "label": "Up to 6 subject keywords in English",
        "input": "taglist",
        "help": {
            "long_help": ["Choose up to 6 keywords that describe the journal's subject matter. "
                          "Keywords must be in English.", "Use single words or short phrases (2 to 3 words) "
                                                          "that describe the journal's main topic.",
                          "Do not add acronyms, abbreviations or descriptive sentences.",
                          "Note that the keywords may be edited by DOAJ editorial staff."],
        },
        "validate": [
            {"required": {"message": "Enter at least <strong>one subject keyword</strong> in English"}},
            {"stop_words": {"disallowed": STOP_WORDS}},  # ~~^->StopWords:FormValidator~~
            {"max_tags": {"max": 6}}
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
        }
    }

    # ~~->$ Language:FormField~~
    LANGUAGE = {
        "name": "language",
        "label": "Languages in which the journal accepts manuscripts",
        "input": "select",
        "default": "",
        "options_fn": "iso_language_list",
        "repeatable": {
            "minimum": 1,
            "initial": 5
        },
        "validate": [
            {"required": {"message": "Enter <strong>at least one</strong> language"}},
            "current_iso_language"
        ],
        "widgets": [
            {"select": {}},
            "multiple_field"
        ],
        "help": {
            "placeholder": "Type or select the language"
        },
        "attr": {
            "class": "input-xlarge unstyled-list"
        }
    }

    # ~~->$ PublisherName:FormField~~
    PUBLISHER_NAME = {
        "name": "publisher_name",
        "label": "Publisher's name",
        "input": "text",
        "validate": [
            {"required": {"message": "Enter the name of the journal's publisher"}},
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            {"autocomplete": {"type": "journal", "field": "bibjson.publisher.name.exact"}},
            # ~~^-> Autocomplete:FormWidget~~
            "full_contents"  # ~~^->FullContents:FormWidget~~
        ],
        "help": {
            "placeholder": "Type or select the publisher's name"
        },
        "contexts": {
            "bulk_edit": {
                "validate": []
            },
            "admin": {
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    {"autocomplete": {"type": "journal", "field": "bibjson.publisher.name.exact"}},
                    # ~~^-> Autocomplete:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            },
            "public": {
                "validate": [
                    {"required": {"message": "Enter the name of the journal's publisher"}},
                    {"different_to": {"field": "institution_name",
                                      "message": "The Publisher's name and Other organisation's name cannot be the same."}}
                ]
                # ~~^-> DifferetTo:FormValidator~~

            },
            "update_request": {
                "validate": [
                    {"required": {"message": "Enter the name of the journal's publisher"}},
                    {"different_to": {"field": "institution_name",
                                      "message": "The Publisher's name and Other organisation's name cannot be the same."}}
                ]
                # ~~^-> DifferetTo:FormValidator~~

            },
            "associate_editor": {
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    {"autocomplete": {"type": "journal", "field": "bibjson.publisher.name.exact"}},
                    # ~~^-> Autocomplete:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            },
            "editor": {
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    {"autocomplete": {"type": "journal", "field": "bibjson.publisher.name.exact"}},
                    # ~~^-> Autocomplete:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            }
        }
    }

    # ~~->$ PublisherCountry:FormField~~
    PUBLISHER_COUNTRY = {
        "name": "publisher_country",
        "label": "Publisher's country",
        "input": "select",
        "default": "",
        "options_fn": "iso_country_list",
        "help": {
            "long_help": ["The country where the publisher carries out its business operations and is registered."],
            "doaj_criteria": "You must provide a publisher country",
            "placeholder": "Type or select the country"
        },
        "validate": [
            {"required": {
                "message": "Enter the <strong>country</strong> where the publisher carries out its business operations and is registered"}}
        ],
        "widgets": [
            {"select": {}}
        ],
        "attr": {
            "class": "input-xlarge"
        },
        "contexts": {
            "associate_editor": {
                "disabled": True
            },
            "bulk_edit": {
                "validate": []
            }
        }
    }

    # ~~->$ InstitutionName:FormField~~
    INSTITUTION_NAME = {
        "name": "institution_name",
        "label": "Other organisation's name",
        "input": "text",
        "optional": True,
        "help": {
            "short_help": "Any other organisation associated with the journal",
            "long_help": [
                "The journal may be owned, funded, sponsored, or supported by another organisation that is not "
                "the publisher. If your journal is linked to "
                "a second organisation, enter its name here."],
            "placeholder": "Type or select the other organisation's name"
        },
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            {"autocomplete": {"type": "journal", "field": "bibjson.institution.name.exact"}},
            # ~~^-> Autocomplete:FormWidget~~
            "full_contents"  # ~~^->FullContents:FormWidget~~
        ],
        "contexts": {
            "public": {
                "validate": [{"different_to": {"field": "publisher_name",
                                               "message": "The Publisher's name and Other organisation's name cannot be the same."}}]
                # ~~^-> DifferetTo:FormValidator~~

            },
            "update_request": {
                "validate": [{"different_to": {"field": "publisher_name",
                                               "message": "The Publisher's name and Other organisation's name cannot be the same."}}]
                # ~~^-> DifferetTo:FormValidator~~

            },
            "admin": {
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    {"autocomplete": {"type": "journal", "field": "bibjson.institution.name.exact"}},
                    # ~~^-> Autocomplete:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            },
            "associate_editor": {
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    {"autocomplete": {"type": "journal", "field": "bibjson.institution.name.exact"}},
                    # ~~^-> Autocomplete:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            },
            "editor": {
                "widgets": [
                    "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
                    {"autocomplete": {"type": "journal", "field": "bibjson.institution.name.exact"}},
                    # ~~^-> Autocomplete:FormWidget~~
                    "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
                ]
            }
        }
    }

    # ~~->$ InstitutionCountry:FormField~~
    INSTITUTION_COUNTRY = {
        "name": "institution_country",
        "label": "Other organisation's country",
        "input": "select",
        "default": "",
        "options_fn": "iso_country_list",
        "optional": True,
        "help": {
            "short_help": "The country in which the other organisation is based",
            "placeholder": "Type or select the country"
        },
        "widgets": [
            {"select": {"allow_clear": True}}
        ],
        "contexts": {
            "public": {
                "validate": [
                    {
                        "only_if_exists": {
                            "fields":
                                [{"field": "institution_name"}],
                            "message": "'You must provide the other organization's name. You cannot provide just the country.",
                        }
                    }
                ]
            },
            "update_request": {
                "validate": [
                    {
                        "only_if_exists": {
                            "fields":
                                [{"field": "institution_name"}],
                            "message": "'You must provide the other organization's name. You cannot provide just the country.",
                        }
                    }
                ]
            },
        },
        "attr": {
            "class": "input-xlarge"
        }
    }

    # ~~->$ License:FormField~~
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
            {"display": "Publisher's own license", "value": "Publisher's own license",
             "subfields": ["license_attributes"]},
        ],
        "help": {
            "long_help": ["The journal must use some form of licensing to be considered for indexing in DOAJ. ",
                          "If Creative Commons licensing is not used, then select <em>Publisher's own license</em> and enter "
                          "more details below.",
                          "More information on CC licenses: <br/>"
                          "<a href='https://creativecommons.org/licenses/by/4.0/"
                          "' target='_blank' 'rel='noopener'>CC BY</a> <br/>"
                          "<a href='https://creativecommons.org/licenses/by-sa/4.0/"
                          "' target='_blank' 'rel='noopener'>CC BY-SA</a> <br/>"
                          "<a href='https://creativecommons.org/licenses/by-nd/4.0/"
                          "' target='_blank' 'rel='noopener'>CC BY-ND</a> <br/>"
                          "<a href='https://creativecommons.org/licenses/by-nc/4.0/"
                          "' target='_blank' 'rel='noopener'>CC BY-NC</a> <br/>"
                          "<a href='https://creativecommons.org/licenses/by-nc-sa/4.0/"
                          "' target='_blank' 'rel='noopener'>CC BY-NC-SA</a> <br/>"
                          "<a href='https://creativecommons.org/licenses/by-nc-nd/4.0/"
                          "' target='_blank' 'rel='noopener'>CC BY-NC-ND</a>",
                          "<a href='https://wiki.creativecommons.org/wiki/CC0_"
                          "FAQ#What_is_the_difference_between_CC0_and_the_Publ"
                          "ic_Domain_Mark_.28.22PDM.22.29.3F' target='_blank' "
                          "rel='noopener'>What is the difference between CC0 "
                          "and the Public Domain Mark (\"PDM\")?</a>"],
            "doaj_criteria": "Content must be licensed"
        },
        "validate": [
            {"required": {"message": "Select <strong>at least one</strong> type of license"}}
        ]
    }

    # ~~->$ LicenseAttributes:FormField~~
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
            "doaj_criteria": "Content must be licensed"
        }
    }

    # ~~->$ LicenseTermsURL:FormField~~
    LICENSE_TERMS_URL = {
        "name": "license_terms_url",
        "label": "Where can we find this information?",
        "input": "text",
        "diff_table_context": "License terms",
        "validate": [
            {"required": {"message": "Enter the URL for the journal’s <strong>license terms</strong> page"}},
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "help": {
            "short_help": "Link to the page where the license terms are stated on your site.",
            "doaj_criteria": "You must provide a link to your license terms",
            "placeholder": "https://www.my-journal.com/about#licensing",
        },
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ]
    }

    # ~~->$ LicenseDisplay:FormField~~
    LICENSE_DISPLAY = {
        "name": "license_display",
        "label": "Does the journal embed and/or display licensing information in its articles?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y", "subfields": ["license_display_example_url"]},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": ["It is recommended that licensing information is included in full-text articles "
                          "but it is not required for inclusion. "
                          "Answer <strong>Yes</strong> if licensing is displayed or "
                          "embedded in all versions of each article."]
        },
        "validate": [
            {"required": {"message": "Select Yes or No"}}
        ]
    }

    # ~~->$ LicenseDisplayExampleUrl:FormField~~
    LICENSE_DISPLAY_EXAMPLE_URL = {
        "name": "license_display_example_url",
        "label": "Recent article displaying or embedding a license in the full text",
        "input": "text",
        "conditional": [
            {"field": "license_display", "value": "y"}
        ],
        "help": {
            "short_help": "Link to an example article",
            "placeholder": "https://www.my-journal.com/articles/article-page"
        },
        "validate": [
            {"required_if": {
                "field": "license_display",
                "value": "y",
                "message": "Enter the URL for any recent article that displays or embeds a license"
            }
            },
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ]
    }

    # ~~->$ CopyrightAuthorRetails:FormField~~
    COPYRIGHT_AUTHOR_RETAINS = {
        "name": "copyright_author_retains",
        "label": "For all the licenses you have indicated above, do authors retain the copyright "
                 "<b>and</b> full publishing rights without restrictions?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y"},
            {"display": "No", "value": "n"}
        ],
        "validate": [
            {"required": {"message": "Select Yes or No"}}
        ],
        "help": {
            "long_help": ["Answer <strong>No</strong> if authors transfer "
                          "copyright or assign exclusive rights to the publisher"
                          " (including commercial rights). <br/><br/> Answer "
                          "<strong>Yes</strong> only if authors publishing "
                          "under any license allowed by the journal "
                          "retain all rights."]
        }
    }

    # ~~->$ CopyrightURL:FormField~~
    COPYRIGHT_URL = {
        "name": "copyright_url",
        "label": "Where can we find this information?",
        "input": "text",
        "diff_table_context": "Copyright terms",
        "help": {
            "short_help": "Link to the journal’s copyright terms"
        },
        "placeholder": "https://www.my-journal.com/about#licensing",
        "validate": [
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ],
        "contexts": {
            "public": {
                "validate": [
                    {"required": {"message": "Enter the URL for the journal’s <strong>copyright terms</strong> page"}},
                    "is_url"  # ~~^->IsURL:FormValidator~~
                ]
            },
            "update_request": {
                "validate": [
                    "required",
                    "is_url"  # ~~^->IsURL:FormValidator~~
                ]
            }
        }
    }

    # ~~->$ ReviewProcess:FormField~~
    REVIEW_PROCESS = {
        "name": "review_process",
        "label": "DOAJ only accepts peer-reviewed journals. "
                 "Which type(s) of peer review does this journal use?",
        "input": "checkbox",
        "multiple": True,
        "options": [
            {"display": "Editorial review", "value": "Editorial review"},
            {"display": "Peer review", "value": "Peer review"},
            {"display": "Anonymous peer review", "value": "Anonymous peer review"},
            {"display": "Double anonymous peer review", "value": "Double anonymous peer review"},
            {"display": "Post-publication peer review", "value": "Post-publication peer review"},
            {"display": "Open peer review", "value": "Open peer review"},
            {"display": "Other", "value": "other", "subfields": ["review_process_other"]}
        ],
        "help": {
            "long_help": ["Enter all types of review used by the journal for "
                          "research articles. Note that editorial review is "
                          "only accepted for <a href='https://doaj.org/apply/guide/#arts-and-humanities-journals' target='_blank' rel='nofollow'>arts and humanities journals</a>."
                          "For a detailed description of the peer review types, "
                          "see <a href='https://docs.google.com/document/d/1ADiVPR7tY8a9JKr2VjFEXbNG7FIpz22nOPDDPfRzJxA/edit?tab=t.0' target='_blank' rel='nofollow'>this summary</a>."],
            "doaj_criteria": "Peer review must be carried out"
        },
        "validate": [
            {"required": {"message": "Select <strong>at least one</strong> type of review process"}}
        ]
    }

    # ~~->$ ReviewProcessOther:FormField~~
    REVIEW_PROCESS_OTHER = {
        "name": "review_process_other",
        "label": "Other peer review",
        "input": "text",
        "help": {
            "placeholder": "Other peer review"
        },
        "conditional": [{"field": "review_process", "value": "other"}],
        "validate": [
            {"required_if": {
                "field": "review_process",
                "value": "other",
                "message": "Enter the name of another type of peer review"
            }
            }
        ],
        "widgets": [
            "trim_whitespace"  # ~~^-> TrimWhitespace:FormWidget~~
        ],
        "asynchronous_warning": [
            {"warn_on_value": {"value": "None"}}
        ]
    }

    # ~~->$ ReviewURL:FormField~~
    REVIEW_URL = {
        "name": "review_url",
        "label": "Where can we find this information?",
        "input": "text",
        "diff_table_context": "Peer review policy",
        "help": {
            "doaj_criteria": "You must provide a URL",
            "short_help": "Link to the journal’s peer review policy"
        },
        "validate": [
            {"required": {"message": "Enter the URL for the journal’s <strong>peer review policy</strong> page"}},
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ]
    }

    # ~~->$ OAStart:FormField~~
    OA_START = {
        "name": "oa_start",
        "label": "When did the journal start to publish all content using an open license?",
        "input": "number",
        "datatype": "integer",
        "help": {
            "long_help": [
                "Please enter the year that the journal started to publish all content as true open access, according to DOAJ's <a href='https://blog.doaj.org/2020/11/17/what-does-doaj-define-as-open-access/' target='_blank' rel='nofollow'>definition</a>.",
                "For journals that have flipped to open access, enter the year that the journal flipped, not the original launch date of the journal.",
                "For journals that have made digitised backfiles freely available, enter the year that the journal started publishing as a fully open access title, not the date of the earliest free content."]
        },
        "validate": [
            {"required": {"message": "Enter the Year (YYYY)."}},
            {"int_range": {"gte": app.config.get('MINIMAL_OA_START_DATE', 1900), "lte": dates.now().year}},
            {"year": {
                "message": "OA Start Date must be a year in the 4-digit format (eg. 1987) and must be greater than {}".format(
                    app.config.get('MINIMAL_OA_START_DATE', 1900))}}
        ],
        "attr": {
            "min": app.config.get('MINIMAL_OA_START_DATE', 1900),
            "max": dates.now().year
        }
    }

    # ~~->$ PlagiarismDetection:FormField~~
    PLAGIARISM_DETECTION = {
        "name": "plagiarism_detection",
        "label": "Does the journal routinely screen article submissions for plagiarism?",
        "input": "radio",
        "help": {
            "long_help": ["Screening for plagiarism is recommended, but is not"
                          " a requirement for inclusion in DOAJ. If the "
                          "journal does screen for plagiarism, state the "
                          "services(s) used on your website."],
        },
        "options": [
            {"display": "Yes", "value": "y", "subfields": ["review_process_other"]},
            {"display": "No", "value": "n"}
        ],
        "validate": [
            {"required": {"message": "Select Yes or No"}}
        ]
    }

    # ~~->$ PlagiarismURL:FormField~~
    PLAGIARISM_URL = {
        "name": "plagiarism_url",
        "label": "Where can we find this information?",
        "diff_table_context": "Plagiarism screening",
        "input": "text",
        "conditional": [{"field": "plagiarism_detection", "value": "y"}],
        "help": {
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/about#plagiarism",
            "short_help": "Link to the journal’s plagiarism policy",
            "long_help": ["The page should state that the journal actively checks for plagiarism and explain how this "
                          "is done (including the name of any software or service used)."]
        },
        "validate": [
            {"required_if": {
                "field": "plagiarism_detection",
                "value": "y",
                "message": "Enter the URL for the journal’s <strong>plagiarism policy</strong> page"
            }
            },
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ]
    }

    # ~~->$ AimsScopeURL:FormField~~
    AIMS_SCOPE_URL = {
        "name": "aims_scope_url",
        "label": "Link to the journal’s <b>Aims & Scope</b>",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/about#aims"
        },
        "validate": [
            {"required": {"message": "Enter the URL for the journal’s <strong>Aims & Scope</strong> page"}},
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ]
    }

    # ~~->$ EditorialBoardURL:FormField~~
    EDITORIAL_BOARD_URL = {
        "name": "editorial_board_url",
        "label": "Link to the journal’s <b>Editorial Board</b>",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/about#board"
        },
        "validate": [
            {"required": {"message": "Enter the URL for the journal’s <strong>Editorial Board</strong> page"}},
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ]
    }

    # ~~->$ AuthorInstructionsURL:FormField~~
    AUTHOR_INSTRUCTIONS_URL = {
        "name": "author_instructions_url",
        "label": "Link to the journal’s <b>Instructions for Authors</b>",
        "input": "text",
        "help": {
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/for_authors"
        },
        "validate": [
            {"required": {"message": "Enter the URL for the journal’s <strong>Instructions for Authors</strong> page"}},
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ]
    }

    # ~~->$ PublicationTimeWeeks:FormField~~
    PUBLICATION_TIME_WEEKS = {
        "name": "publication_time_weeks",
        "label": "Average number of <strong>weeks</strong> between article submission & publication",
        "input": "number",
        "datatype": "integer",
        "validate": [
            {"required": {"message": "Enter an average number of weeks"}},
            {"int_range": {"gte": 1, "lte": 100}}
        ],
        "attr": {
            "min": "1",
            "max": "100"
        }
    }

    # ~~->$ APC:FormField~~
    APC = {
        "name": "apc",
        "label": "Does the journal charge fees for publishing an article (APCs)?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y", "subfields": ["apc_charges"]},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": ["Publication fees are sometimes called "
                          "article processing charges (APCs). You should answer"
                          " Yes if any fee is required from the author for "
                          "publishing their paper."],
            "doaj_criteria": "You must tell us about any APCs"
        },
        "validate": [
            {"required": {"message": "Select Yes or No"}}
        ]
    }

    # ~~->$ APCCharges:FormField~~
    APC_CHARGES = {
        "name": "apc_charges",
        "input": "group",
        "label": "Highest fee charged",
        "repeatable": {
            "minimum": 1,
            "initial": 5
        },
        "conditional": [
            {"field": "apc", "value": "y"}
        ],
        "help": {
            "long_help": [" If the journal charges a range of fees for "
                          "the publication of an article, enter the highest fee. "
                          "If the fee can be paid in more than one currency, "
                          "you may list them here."]
        },
        "subfields": [
            "apc_currency",
            "apc_max"
        ],
        "template": templates.AF_LIST,
        "entry_template": templates.AF_ENTRY_GROUP_HORIZONTAL,
        "widgets": [
            "multiple_field"
        ]
    }

    # ~~->$ APCCurrency:FormField~~
    APC_CURRENCY = {
        "subfield": True,
        "group": "apc_charges",
        "name": "apc_currency",
        "input": "select",
        "options_fn": "iso_currency_list",
        "default": "",
        "help": {
            "placeholder": "Currency"
        },
        "widgets": [
            {"select": {}}
        ],
        "attr": {
            "class": "input-xlarge"
        },
        "validate": [
            {
                "required_if": {
                    "field": "apc",
                    "value": "y",
                    "message": "Enter the currency or currencies for the journal’s publishing fees"
                }
            },
            "current_iso_currency"
        ]
    }

    # ~~->$ APCMax:FormField~~
    APC_MAX = {
        "subfield": True,
        "group": "apc_charges",
        "name": "apc_max",
        "input": "number",
        "datatype": "integer",
        "help": {
            "placeholder": "Highest fee charged"
        },
        "validate": [
            {
                "required_if": {
                    "field": "apc",
                    "value": "y",
                    "message": "Enter the value of the highest publishing fee the journal has charged"
                }
            }
        ],
        "attr": {
            "min": "1"
        }
    }

    # ~~->$ APCURL:FormField~~
    APC_URL = {
        "name": "apc_url",
        "label": "Where can we find this information?",
        "diff_table_context": "Publication fees",
        "input": "text",
        "help": {
            "short_help": "Link to the page where this is stated. The page "
                          "must declare <b>whether or not</b> there is a fee "
                          "to publish an article in the journal.",
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/about#apc"
        },
        "validate": [
            {"required": {
                "message": "Enter the URL for the journal’s <strong>publication fees</strong> information page"}},
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ]
    }

    # ~~->$ HasWaiver:FormField~~
    HAS_WAIVER = {
        "name": "has_waiver",
        "label": "Does the journal provide a waiver or discount "
                 "on publication fees for authors?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y", "subfields": ["waiver_url"]},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": ["Answer <strong>Yes</strong> if the journal provides"
                          " publication fee waivers for authors from "
                          "low-income economies, discounts for authors from "
                          "lower middle-income economies, and/or waivers and "
                          "discounts for other authors with "
                          "demonstrable needs."]
        },
        "validate": [
            {"required": {"message": "Select Yes or No"}}
        ]
    }

    # ~~->$ WaiverURL:FormField~~
    WAIVER_URL = {
        "name": "waiver_url",
        "label": "Where can we find this information?",
        "input": "text",
        "diff_table_context": "Publication fee waiver",
        "conditional": [
            {"field": "has_waiver", "value": "y"}
        ],
        "help": {
            "short_help": "Link to the journal’s waiver information.",
            "doaj_criteria": "You must provide a URL",
            "placeholder": "https://www.my-journal.com/about#waiver"
        },
        "validate": [
            {"required_if": {
                "field": "has_waiver",
                "value": "y",
                "message": "Enter the URL for the journal’s <strong>waiver information</strong> page"
            }
            },
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ]
    }

    # ~~->$ HasOtherCharges:FormField~~
    HAS_OTHER_CHARGES = {
        "name": "has_other_charges",
        "label": "Does the journal charge any other fees to authors?",
        "input": "radio",
        "options": [
            {"display": "Yes", "value": "y", "subfields": ["other_charges_url"]},
            {"display": "No", "value": "n"}
        ],
        "help": {
            "long_help": ["Declare all other charges: editorial processing charges, language editing fees, "
                          "colour charges, submission fees, page charges, membership fees, print subscription costs, "
                          "other supplementary charges"],
            "doaj_criteria": "You must declare any other charges if they exist"
        },
        "validate": [
            {"required": {"message": "Select Yes or No"}}
        ]
    }

    # ~~->$ OtherChargesURL:FormField~~
    OTHER_CHARGES_URL = {
        "name": "other_charges_url",
        "label": "Where can we find this information?",
        "input": "text",
        "diff_table_context": "Other fees",
        "conditional": [
            {"field": "has_other_charges", "value": "y"}
        ],
        "help": {
            "short_help": "Link to the journal’s fees information",
            "doaj_criteria": "You must provide a URL"
        },
        "validate": [
            {"required_if": {
                "field": "has_other_charges",
                "value": "y",
                "message": "Enter the URL for the journal’s <strong>fees<strong> information page"
            }
            },
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ]
    }

    # ~~->$ PreservationService:FormField~~
    PRESERVATION_SERVICE = {
        "name": "preservation_service",
        "label": "Long-term preservation service(s) where the journal is currently archived",
        "input": "checkbox",
        "multiple": True,
        "options": [
            {"display": "CINES", "value": "CINES", "subfields": ["preservation_service_url"]},
            {"display": "CLOCKSS", "value": "CLOCKSS", "subfields": ["preservation_service_url"]},
            {"display": "LOCKSS", "value": "LOCKSS", "subfields": ["preservation_service_url"]},
            {"display": "Internet Archive", "value": "Internet Archive", "subfields": ["preservation_service_url"]},
            {"display": "PKP PN", "value": "PKP PN", "subfields": ["preservation_service_url"]},
            {"display": "PubMed Central (PMC)", "value": "PMC", "subfields": ["preservation_service_url"]},
            {"display": "Portico", "value": "Portico", "subfields": ["preservation_service_url"]},
            {"display": "A national library", "value": "national_library",
             "subfields": ["preservation_service_library", "preservation_service_url"]},
            {"display": "Other", "value": "other",
             "subfields": ["preservation_service_other", "preservation_service_url"]},
            {"display": HTMLString("<em>The journal content isn’t archived with a long-term preservation service</em>"),
             "value": "none", "exclusive": True}
        ],
        "help": {
            "long_help": [
                "Content must be actively deposited in each of the options you choose. "
                "If the journal is registered with a service but archiving is not yet active,"
                " choose <em>The journal content isn’t archived with a long-term preservation service</em>.",
                "PubMed Central covers PMC U.S.A. and EuropePMC(Wellcome Trust)."]
        },
        "validate": [
            {"required": {"message": "Select <strong>at least one</strong> option"}}
        ],
        "contexts": {
            "admin": {
                "widgets": [
                    "autocheck",  # ~~^-> Autocheck:FormWidget~~
                ]
            }
        }
    }

    # ~~->$ PreservationServiceLibrary:FormField~~
    PRESERVATION_SERVICE_LIBRARY = {
        "name": "preservation_service_library",
        "label": "A national library",
        "input": "text",
        "repeatable": {
            "minimum": 1,
            "initial": 2
        },
        "help": {
            "short_help": "Name of national library"
        },
        "conditional": [{"field": "preservation_service", "value": "national_library"}],
        "validate": [
            {"required_if": {
                "field": "preservation_service",
                "value": "national_library",
                "message": "Enter the name(s) of the national library or libraries where the journal is archived"
            }
            }
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "multiple_field"
        ],
        "attr": {
            "class": "input-xlarge unstyled-list"
        }
    }

    # ~~->$ PreservationServiceOther:FormField~~
    PRESERVATION_SERVICE_OTHER = {
        "name": "preservation_service_other",
        "label": "Other archiving policy:",
        "input": "text",
        "conditional": [{"field": "preservation_service", "value": "other"}],
        "validate": [
            {"required_if": {
                "field": "preservation_service",
                "value": "other",
                "message": "Enter the name of another archiving policy"
            }
            }
        ],
        "asynchronous_warning": [
            {"warn_on_value": {"value": "None"}}
        ],
        "widgets": [
            "trim_whitespace"  # ~~^-> TrimWhitespace:FormWidget~~
        ]
    }

    # ~~->$ PreservationServiceURL:FormField~~
    PRESERVATION_SERVICE_URL = {
        "name": "preservation_service_url",
        "label": "Where can we find this information?",
        "input": "text",
        "diff_table_context": "Archiving policy",
        "help": {
            "short_help": "Link to the preservation and archiving information",
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
            {
                "required_if": {
                    "field": "preservation_service",
                    "value": [
                        "CINES",
                        "CLOCKSS",
                        "LOCKSS",
                        "Internet Archive",
                        "PKP PN",
                        "PMC",
                        "Portico",
                        "national_library",
                        "other"
                    ]
                }
            },
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url"  # ~~^-> ClickableURL:FormWidget~~
        ]
    }

    # ~~->$ DepositPolicy:FormField~~
    DEPOSIT_POLICY = {
        "name": "deposit_policy",
        "label": "Does the journal have a policy allowing authors to deposit versions of their work in an "
                 "institutional or other repository of their choice? Where is this policy recorded?",
        "input": "checkbox",
        "multiple": True,
        "options": [
            {"display": "Diadorim", "value": "Diadorim", "subfields": ["deposit_policy_url"]},
            {"display": "Dulcinea", "value": "Dulcinea", "subfields": ["deposit_policy_url"]},
            {"display": "Mir@bel", "value": "Mir@bel", "subfields": ["deposit_policy_url"]},
            {"display": "Open Policy Finder", "value": "Open Policy Finder", "subfields": ["deposit_policy_url"]},
            {"display": "Other (including publisher’s own site)", "value": "other",
             "subfields": ["deposit_policy_other", "deposit_policy_url"]},
            {"display": HTMLString("<em>The journal has no repository policy</em>"), "value": "none", "exclusive": True}
        ],
        "help": {
            "long_help": ["Many authors wish to deposit a copy of their paper in an institutional or other repository "
                          "of their choice. What is the journal’s policy for this?",
                          "You should state your policy about the different versions of the paper:"
                          "<ul style='list-style-type: none;'>"
                          "<li>Submitted version</li>"
                          "<li>Accepted version (Author Accepted Manuscript)</li>"
                          "<li>Published version (Version of Record)</li>"
                          "</ul>"
                          ]},
        "validate": [
            {"required": {"message": "Select <strong>at least one</strong> option"}}
        ]
    }

    # ~~->$ DepositPolicyOther:FormField~~
    DEPOSIT_POLICY_OTHER = {
        "name": "deposit_policy_other",
        "label": "Name of other website where policy is registered",
        "input": "text",
        "conditional": [{"field": "deposit_policy", "value": "other"}],
        "validate": [
            {"required_if": {
                "field": "deposit_policy",
                "value": "other",
                "message": "Enter the name of another repository policy"
            }
            }
        ],
        "asynchronous_warning": [
            {"warn_on_value": {"value": "None"}}
        ],
        "widgets": [
            "trim_whitespace"  # ~~^-> TrimWhitespace:FormWidget~~
        ]
    }

    # ~~->$ DepositPolicyURL:FormField~~
    DEPOSIT_POLICY_URL = {
        "name": "deposit_policy_url",
        "label": "Where can we find this information?",
        "input": "text",
        "diff_table_context": "Repository policy",
        "conditional": [{"field": "deposit_policy", "value": "Diadorim"},
                        {"field": "deposit_policy", "value": "Dulcinea"},
                        {"field": "deposit_policy", "value": "Mir@bel"},
                        {"field": "deposit_policy", "value": "Open Policy Finder"},
                        {"field": "deposit_policy", "value": "other"}],
        "help": {
            "doaj_criteria": "You must provide a URL",
            "short_help": "Provide the link to the policy in the selected directory. Or select 'Other' and provide a link to the information on your website.",
            "placeholder": "https://www.my-journal.com/about#repository_policy"
        },
        "validate": [
            "is_url"  # ~~^->IsURL:FormValidator~~
        ],
        "widgets": [
            "trim_whitespace",  # ~~^-> TrimWhitespace:FormWidget~~
            "clickable_url",  # ~~^-> ClickableURL:FormWidget~~
        ],
        "contexts": {
            "public": {
                "validate": [
                    {
                        "required_if": {
                            "field": "deposit_policy",
                            "value": [
                                "Diadorim",
                                "Dulcinea",
                                "Mir@bel",
                                "Open Policy Finder",
                                "other"
                            ]
                        }
                    },
                    "is_url"  # ~~^->IsURL:FormValidator~~
                ]
            },
            "update_request": {
                "validate": [
                    {
                        "required_if": {
                            "field": "deposit_policy",
                            "value": [
                                "Diadorim",
                                "Dulcinea",
                                "Mir@bel",
                                "Open Policy Finder",
                                "other"
                            ]
                        }
                    },
                    "is_url"  # ~~^->IsURL:FormValidator~~
                ]
            }
        }
    }

    # ~~->$ PersistentIdentifiers:FormField~~
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
            {"display": "Other", "value": "other", "subfields": ["persistent_identifiers_other"]},
            {"display": HTMLString("<em>The journal does not use persistent article identifiers</em>"), "value": "none",
             "exclusive": True}
        ],
        "help": {
            "long_help": ["A persistent article identifier (PID) is used to find the article no matter where it is "
                          "located. The most common type of PID is the digital object identifier (DOI). ",
                          "<a href='https://en.wikipedia.org/wiki/Persistent_identifier' target='_blank' rel='noopener'>Read more about PIDs.</a>"],
        },
        "validate": [
            {"required": {"message": "Select <strong>at least one</strong> option"}}
        ]
    }

    # ~~->$ PersistentIdentifiersOther:FormField~~
    PERSISTENT_IDENTIFIERS_OTHER = {
        "name": "persistent_identifiers_other",
        "label": "Other identifier",
        "input": "text",
        "conditional": [{"field": "persistent_identifiers", "value": "other"}],
        "validate": [
            {"required_if": {
                "field": "persistent_identifiers",
                "value": "other",
                "message": "Enter the name of another type of identifier"
            }
            }
        ],
        "asynchronous_warning": [
            {"warn_on_value": {"value": "None"}}
        ],
        "widgets": [
            "trim_whitespace"  # ~~^-> TrimWhitespace:FormWidget~~
        ]
    }

    #######################################
    ## Editorial fields

    S2O = {
        "name": "s2o",
        "label": "Subscribe to Open",
        "input": "checkbox",
        "help": {
            "long_help": [
                "Is the journal part of the <a href='https://subscribetoopencommunity.org/' target='_blank' rel='noopener'>"
                "Subscribe to Open</a> initiative?"],
        }
    }

    MIRROR = {
        "name": "mirror",
        "label": "Mirror Journal",
        "input": "checkbox",
        "help": {
            "long_help": ["Is the journal a Mirror Journal?"]
        }
    }

    OJC = {
        "name": "ojc",
        "label": "Open Journals Collective",
        "input": "checkbox",
        "help": {
            "long_help": [
                "Is the journal part of the <a href='https://openjournalscollective.org/' target='_blank' rel='noopener'>"
                "Open Journals Collective</a>?"],
        }
    }

    # FIXME: this probably shouldn't be in the admin form fieldsets, rather its own separate form
    # ~~->$ QuickReject:FormField~~
    QUICK_REJECT = {
        "name": "quick_reject",
        "label": "Reason for rejection",
        "input": "select",
        "options_fn": "quick_reject"
    }

    # ~~->$ QuickRejectDetails:FormField~~
    QUICK_REJECT_DETAILS = {
        "name": "quick_reject_details",
        "label": "Additional info",
        "input": "textarea",
        "help": {
            "long_help": ["The selected reason for rejection, and any additional information you include, "
                          "are sent to the journal contact with the rejection email."]
        },
        "validate": [
            {"required_if": {"field": "quick_reject", "value": "other"}}
        ],
    }

    # ~~->$ Owner:FormField~~
    OWNER = {
        "name": "owner",
        "label": "DOAJ Account",
        "input": "text",
        "validate": [
            "reserved_usernames",
            "owner_exists"
        ],
        "widgets": [
            {"autocomplete": {"type": "account", "field": "id", "include": False}},  # ~~^-> Autocomplete:FormWidget~~
            "clickable_owner"
        ],
        "contexts": {
            "associate_editor": {
                "validate": [
                    {"required": {"message": "You must confirm the account id"}},
                    "reserved_usernames",
                    "owner_exists"
                ]
            }
        }
    }

    # ~~->$ ApplicationStatus:FormField~~
    APPLICATION_STATUS = {
        "name": "application_status",
        "label": "Change status",
        "input": "select",
        "options_fn": "application_statuses",
        "validate": [
            "required"
        ],
        "help": {
            "update_requests_diff": False,
            "render_error_box": False
        },
        "disabled": "application_status_disabled",
        "contexts": {
            "associate_editor": {
                "help": {
                    "render_error_box": False,
                    "short_help": "Set the status to 'In Progress' to signal to the applicant that you have started your review."
                                  "Set the status to 'Completed' to alert the Editor that you have completed your review.",
                    "update_requests_diff": False
                }
            },
            "editor": {
                "help": {
                    "render_error_box": False,
                    "short_help": "Revert the status to 'In Progress' to signal to the Associate Editor that further work is needed."
                                  "Set the status to 'Ready' to alert the Managing Editor that you have completed your review.",
                    "update_requests_diff": False
                }
            }
        },
        "widgets": [
            # When Accepted selected display. 'This journal is currently assigned to its applicant account XXXXXX. Is this the correct account for this journal?'
            "owner_review"
        ]
    }

    # ~~->$ EditorGroup:FormField~~
    EDITOR_GROUP = {
        "name": "editor_group",
        "label": "Group",
        "input": "text",
        "widgets": [
            {"autocomplete": {"type": "editor_group", "field": "name", "include": False}}
            # ~~^-> Autocomplete:FormWidget~~
        ],
        "contexts": {
            "editor": {
                "disabled": True
            },
            "admin": {
                "widgets": [
                    {"autocomplete": {"type": "editor_group", "field": "name", "include": False}},
                    # ~~^-> Autocomplete:FormWidget~~
                    {"load_editors": {"field": "editor"}}
                ]
            }
        }
    }

    # ~~->$ Editor:FormField~~
    EDITOR = {
        "name": "editor",
        "label": "Individual",
        "input": "select",
        "options_fn": "editor_choices",
        "default": "",
        "validate": [
            {"group_member": {"group_field": "editor_group"}}
        ],
        "help": {
            "render_error_box": False
        }
    }

    # ~~->$ DiscontinuedDate:FormField~~
    DISCONTINUED_DATE = {
        "name": "discontinued_date",
        "label": "Discontinued on",
        "input": "text",
        "validate": [
            {"bigenddate": {"message": "Date must be a big-end formatted date (e.g. 2020-11-23)"}},
            {
                "not_if": {
                    "fields": [
                        {"field": "continues"},
                        {"field": "continued_by"}
                    ],
                    "message": "You cannot enter both a discontinued date and continuation information."
                }
            }
        ],
        "help": {
            "short_help": "Please enter the discontinued date in the form YYYY-MM-DD (e.g. 2020-11-23).  "
                          "If the day of the month is not known, please use '01' (e.g. 2020-11-01)",
            "render_error_box": False
        }
    }

    # ~~->$ Continues:FormField~~
    CONTINUES = {
        "name": "continues",
        "label": "Continues an <strong>older</strong> journal with the ISSN(s)",
        "input": "taglist",
        "validate": [
            {"is_issn_list": {"message": "This is not a valid ISSN"}},  # ~~^-> IsISSN:FormValidator~~
            {"different_to": {"field": "continued_by",
                              "message": "The ISSN provided in both fields must be different. Please make sure to enter the ISSN of an older journal for the first field and the ISSN of a newer journal for the second field. They cannot be the same."}},
            # ~~^-> DifferetTo:FormValidator~~
            {
                "not_if": {
                    "fields": [{"field": "discontinued_date"}],
                    "message": "You cannot enter both continuation information and a discontinued date"
                }
            }
        ],
        "widgets": [
            "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
            "full_contents",  # ~~^->FullContents:FormWidget~~
            "tagentry"  # ~~-> TagEntry:FormWidget~~
        ],
        "help": {
            "short_help": "Enter the ISSN(s) of the previous title(s) of this journal.",
            "render_error_box": False
        }
    }

    # ~~->$ ContinuedBy:FormField~~
    CONTINUED_BY = {
        "name": "continued_by",
        "label": "Continued by a <strong>newer</strong> journal with the ISSN(s)",
        "input": "taglist",
        "validate": [
            {"is_issn_list": {"message": "This is not a valid ISSN"}},  # ~~^-> IsISSN:FormValidator~~
            {"different_to": {"field": "continues",
                              "message": "The ISSN provided in both fields must be different. Please make sure to enter the ISSN of an older journal for the first field and the ISSN of a newer journal for the second field. They cannot be the same."}},
            # ~~^-> DifferetTo:FormValidator~~
            {
                "not_if": {
                    "fields": [{"field": "discontinued_date"}],
                    "message": "You cannot enter both continuation information and a discontinued date"
                }
            }
        ],
        "help": {
            "short_help": "Enter the ISSN(s) of the later title(s) that continue this publication.",
            "render_error_box": False
        },
        "widgets": [
            "click_to_copy",  # ~~^-> ClickToCopy:FormWidget~~
            "full_contents",  # ~~^->FullContents:FormWidget~~
            "tagentry"  # ~~-> TagEntry:FormWidget~~
        ]
    }

    # ~~->$ Subject:FormField~~
    SUBJECT = {
        "name": "subject",
        "label": "Assign one or a maximum of two subject classifications",
        "input": "taglist",
        "help": {
            "short_help": "Selecting a subject will not automatically select its sub-categories",
            "render_error_box": False,
        },
        "validate": [
            {"required_if": {
                "field": "application_status",
                "value": [
                    constants.APPLICATION_STATUS_READY,
                    constants.APPLICATION_STATUS_COMPLETED,
                    constants.APPLICATION_STATUS_ACCEPTED
                ],
                "message": "This field is required when setting the Application Status to {y}, {z} or {a}".format(
                    y=constants.APPLICATION_STATUS_READY,
                    z=constants.APPLICATION_STATUS_COMPLETED,
                    a=constants.APPLICATION_STATUS_ACCEPTED
                )
            }
            }
        ],
        "widgets": [
            "subject_tree"
        ],
        "contexts": {
            "associate_editor": {
                "validate": [
                    "required"
                ]
            }
        }
    }

    # ~~->$ Notes:FormField~~
    NOTES = {
        "name": "notes",
        "input": "group",
        "label": "Notes",
        "repeatable": {
            "initial": 1,
            "add_button_placement": "top"
        },
        "subfields": [
            "note_author",
            "note_date",
            "note",
            "note_id",
            "note_author_id",
        ],
        "template": templates.AF_LIST,
        "entry_template": templates.AF_ENTRY_GOUP,
        "widgets": [
            {"infinite_repeat": {"enable_on_repeat": ["textarea"]}},
            "note_modal",
        ],
        "merge_disabled": "merge_disabled_notes",
    }

    # ~~->$ Note:FormField~~
    NOTE = {
        "subfield": True,
        "name": "note",
        "group": "notes",
        "input": "textarea",
        "disabled": "disable_edit_note_except_editing_user",
    }

    # ~~->$ NoteAuthor:FormField~~
    NOTE_AUTHOR = {
        "subfield": True,
        "name": "note_author",
        "group": "notes",
        "input": "text",
        "disabled": True
    }

    # ~~->$ NoteDate:FormField~~
    NOTE_DATE = {
        "subfield": True,
        "name": "note_date",
        "group": "notes",
        "input": "text",
        "disabled": True
    }

    # ~~->$ NoteID:FormField~~
    NOTE_ID = {
        "subfield": True,
        "name": "note_id",
        "group": "notes",
        "input": "hidden"
    }

    # ~~->$ NoteAuthorID:FormField~~
    NOTE_AUTHOR_ID = {
        "subfield": True,
        "name": "note_author_id",
        "group": "notes",
        "input": "hidden"
    }

    FLAGS = {
        "name": "flags",
        "input": "group",
        "label": "Flags",
        "repeatable": {
            "initial": 2,
            "add_button_placement": "top",
            "add_field_permission": ["admin"]
        },
        "subfields": [
            "flag_setter",
            "flag_created_date",
            "flag_assignee",
            "flag_deadline",
            "flag_note",
            "flag_note_id",
            "flag_resolved"
        ],
        "template": templates.FLAGS_LIST,
        "entry_template": templates.FLAG_ENTRY_GROUP,
        "widgets": [
            "multiple_field",
            "flag_manager"
        ],
        "merge_disabled": "merge_disabled_notes"
    }

    FLAG_RESOLVED = {
        "subfield": True,
        "name": "flag_resolved",
        "group": "flags",
        "input": "hidden",
    }

    # ~~->$ NoteAuthor:FormField~~
    FLAG_SETTER = {
        "subfield": True,
        "name": "flag_setter",
        "group": "flags",
        "input": "hidden",
        "disabled": True
    }

    # ~~->$ NoteDate:FormField~~
    FLAG_CREATED_DATE = {
        "subfield": True,
        "name": "flag_created_date",
        "group": "flags",
        "input": "hidden",
        "disabled": True
    }

    FLAG_DEADLINE = {
        "subfield": True,
        "label": "Deadline",
        "name": "flag_deadline",
        "validate": [
            {"bigenddate": {"message": "This must be a valid date in the BigEnd format (YYYY-MM-DD)", "ignore_empty": True}},
            {"required_if": {
                "field": "flag_note",
                "message": "The flag must have a deadline",
                "skip_disabled": True
            }}
        ],
        "help": {
            "placeholder": "deadline (YYYY-MM-DD)",
            "render_error_box": True,
            "warning_message": Messages.FORMS_APPLICATION_FLAG__PAST_DEADLINE_WARNING
        },
        "group": "flags",
        "input": "text",
    }

    FLAG_NOTE = {
        "subfield": True,
        "name": "flag_note",
        "group": "flags",
        "input": "textarea",
    }

    # ~~->$ NoteID:FormField~~
    FLAG_NOTE_ID = {
        "subfield": True,
        "name": "flag_note_id",
        "group": "flags",
        "input": "hidden"
    }

    FLAG_ASSIGNEE = {
        "subfield": True,
        "name": "flag_assignee",
        "label": "Assign a user",
        "help": {
            "placeholder": "assigned_to"
        },
        "group": "flags",
        "validate": [
            "reserved_usernames",
            "owner_exists",
            {"required_if": {
                "field": "flag_note",
                "message": "The flag must be assigned to someone",
                "skip_disabled": True
            }}
        ],
        "widgets": [
            {"autocomplete": {"type": "admin", "include": False, "allow_clear_input": False}},
            # ~~^-> Autocomplete:FormWidget~~
        ],
        "input": "text",
    }

    # ~~->$ OptionalValidation:FormField~~
    OPTIONAL_VALIDATION = {
        "name": "make_all_fields_optional",
        "label": "Allow save without validation",
        "input": "checkbox",
        "widget": {
            "optional_validation"
        }
    }

    LAST_FULL_REVIEW = {
        "optional": True,
        "label": "Last Full Review Date",
        "name": "last_full_review",
        "validate": [
            {"bigenddate": {"message": "This must be a valid date in the BigEnd format (YYYY-MM-DD)"}},
            {"date_in_the_past": {"message": "The date must be in the past"}}
        ],
        "help": {
            "placeholder": "last full review (YYYY-MM-DD)",
            "render_error_box": True,
            "short_help": "If you have just completed a full review of this Journal, enter the date here."
        },
        "input": "text",    # although this is a date, the text input is the best one to use because the widget will force that type anyway
        "widgets": [
            {"date_picker": {"earlier_than_now": True}}  # ~~^-> DatePicker:FormWidget~~
        ]
    }


##########################################################
# Define our fieldsets
##########################################################

class FieldSetDefinitions:
    # ~~->$ BasicCompliance:FieldSet~~
    BASIC_COMPLIANCE = {
        "name": "basic_compliance",
        "label": "Open access compliance",
        "fields": [
            FieldDefinitions.BOAI["name"],
            FieldDefinitions.OA_STATEMENT_URL["name"],
            FieldDefinitions.OA_START["name"]
        ]
    }

    # ~~->$ AboutJournal:FieldSet~~
    ABOUT_THE_JOURNAL = {
        "name": "about_the_journal",
        "label": "About the journal",
        "fields": [
            FieldDefinitions.TITLE["name"],
            FieldDefinitions.ALTERNATIVE_TITLE["name"],
            FieldDefinitions.JOURNAL_URL["name"],
            FieldDefinitions.PISSN["name"],
            FieldDefinitions.EISSN["name"],
            FieldDefinitions.LANGUAGE["name"]
        ]
    }

    # ~~->$ Publisher:FieldSet~~
    PUBLISHER = {
        "name": "publisher",
        "label": "Publisher",
        "fields": [
            FieldDefinitions.PUBLISHER_NAME["name"],
            FieldDefinitions.PUBLISHER_COUNTRY["name"],
        ]
    }

    # ~~->$ Institution:FieldSet~~
    SOCIETY_OR_INSTITUTION = {
        "name": "society_or_institution",
        "label": "Other organisation, if applicable",
        "fields": [
            FieldDefinitions.INSTITUTION_NAME["name"],
            FieldDefinitions.INSTITUTION_COUNTRY["name"]
        ]
    }

    # ~~->$ Licensing:FieldSet~~
    LICENSING = {
        "name": "licensing",
        "label": "Licensing",
        "fields": [
            FieldDefinitions.LICENSE["name"],
            FieldDefinitions.LICENSE_ATTRIBUTES["name"],
            FieldDefinitions.LICENSE_TERMS_URL["name"]
        ]
    }

    # ~~->$ EmbeddedLicense:FieldSet~~
    EMBEDDED_LICENSING = {
        "name": "embedded_licensing",
        "label": "Embedded licenses",
        "fields": [
            FieldDefinitions.LICENSE_DISPLAY["name"],
            FieldDefinitions.LICENSE_DISPLAY_EXAMPLE_URL["name"]
        ]
    }

    # ~~->$ Copyright:FieldSet~~
    COPYRIGHT = {
        "name": "copyright",
        "label": "Copyright",
        "fields": [
            FieldDefinitions.COPYRIGHT_AUTHOR_RETAINS["name"],
            FieldDefinitions.COPYRIGHT_URL["name"]
        ]
    }

    # ~~->$ PeerReview:FieldSet~~
    PEER_REVIEW = {
        "name": "peer_review",
        "label": "Peer review",
        "fields": [
            FieldDefinitions.REVIEW_PROCESS["name"],
            FieldDefinitions.REVIEW_PROCESS_OTHER["name"],
            FieldDefinitions.REVIEW_URL["name"]
        ]
    }

    # ~~->$ Plagiarism:FieldSet~~
    PLAGIARISM = {
        "name": "plagiarism",
        "label": "Plagiarism",
        "fields": [
            FieldDefinitions.PLAGIARISM_DETECTION["name"],
            FieldDefinitions.PLAGIARISM_URL["name"]
        ]
    }

    # ~~->$ Editorial:FieldSet~~
    EDITORIAL = {
        "name": "editorial",
        "label": "Editorial",
        "fields": [
            FieldDefinitions.AIMS_SCOPE_URL["name"],
            FieldDefinitions.EDITORIAL_BOARD_URL["name"],
            FieldDefinitions.AUTHOR_INSTRUCTIONS_URL["name"],
            FieldDefinitions.PUBLICATION_TIME_WEEKS["name"],
        ]
    }

    # ~~->$ APC:FieldSet~~
    APC = {
        "name": "apc",
        "label": "Publication fees",
        "fields": [
            FieldDefinitions.APC["name"],
            FieldDefinitions.APC_CHARGES["name"],
            FieldDefinitions.APC_CURRENCY["name"],
            FieldDefinitions.APC_MAX["name"],
            FieldDefinitions.APC_URL["name"]
        ]
    }

    # ~~->$ Waivers:FieldSet~~
    APC_WAIVERS = {
        "name": "apc_waivers",
        "label": "Publication fee waivers",
        "fields": [
            FieldDefinitions.HAS_WAIVER["name"],
            FieldDefinitions.WAIVER_URL["name"]
        ]
    }

    # ~~->$ OtherFees:FieldSet~~
    OTHER_FEES = {
        "name": "other_fees",
        "label": "Other fees",
        "fields": [
            FieldDefinitions.HAS_OTHER_CHARGES["name"],
            FieldDefinitions.OTHER_CHARGES_URL["name"]
        ]
    }

    # ~~->$ ArchivingPolicy:FieldSet~~
    ARCHIVING_POLICY = {
        "name": "archiving_policy",
        "label": "Archiving policy",
        "fields": [
            FieldDefinitions.PRESERVATION_SERVICE["name"],
            FieldDefinitions.PRESERVATION_SERVICE_LIBRARY["name"],
            FieldDefinitions.PRESERVATION_SERVICE_OTHER["name"],
            FieldDefinitions.PRESERVATION_SERVICE_URL["name"]
        ]
    }

    # ~~->$ RepositoryPolicy:FieldSet~~
    REPOSITORY_POLICY = {
        "name": "deposit_policy",
        "label": "Repository policy",
        "fields": [
            FieldDefinitions.DEPOSIT_POLICY["name"],
            FieldDefinitions.DEPOSIT_POLICY_OTHER["name"],
            FieldDefinitions.DEPOSIT_POLICY_URL["name"]
        ]
    }

    # ~~->$ UniqueIdentifiers:FieldSet~~
    UNIQUE_IDENTIFIERS = {
        "name": "unique_identifiers",
        "label": "Unique identifiers & structured data",
        "fields": [
            FieldDefinitions.PERSISTENT_IDENTIFIERS["name"],
            FieldDefinitions.PERSISTENT_IDENTIFIERS_OTHER["name"]
        ]
    }


    LABELS = {
        "name": "labels",
        "label": "Specify labels for this journal",
        "fields": [
            FieldDefinitions.S2O["name"],
            FieldDefinitions.MIRROR["name"],
            FieldDefinitions.OJC["name"]
        ]
    }

    # ~~->$ QuickReject:FieldSet~~
    # ~~^-> QuickReject:Feature~~
    QUICK_REJECT = {
        "name": "quick_reject",
        "label": "Quick reject",
        "fields": [
            FieldDefinitions.QUICK_REJECT["name"],
            FieldDefinitions.QUICK_REJECT_DETAILS["name"]
        ]
    }

    # ~~->$ Reassign:FieldSet~~
    REASSIGN = {
        "name": "reassign",
        "label": "Re-assign publisher account",
        "fields": [
            FieldDefinitions.OWNER["name"]
        ]
    }

    LAST_FULL_REVIEW = {
        "name": "last_full_review",
        "label": "Last Full Review",
        "fields": [
            FieldDefinitions.LAST_FULL_REVIEW["name"]
        ]
    }

    # ~~->$ Status:FieldSet~~
    STATUS = {
        "name": "status",
        "label": "Status",
        "fields": [
            FieldDefinitions.APPLICATION_STATUS["name"]
        ]
    }

    # ~~->$ Reviewers:FieldSet~~
    REVIEWERS = {
        "name": "reviewers",
        "label": "Assign for review",
        "fields": [
            FieldDefinitions.EDITOR_GROUP["name"],
            FieldDefinitions.EDITOR["name"]
        ]
    }

    # ~~->$ Continuations:FieldSet~~
    # ~~^-> Continuations:Feature~~
    CONTINUATIONS = {
        "name": "continuations",
        "label": "Continuations",
        "fields": [
            FieldDefinitions.CONTINUES["name"],
            FieldDefinitions.CONTINUED_BY["name"],
            FieldDefinitions.DISCONTINUED_DATE["name"]
        ]
    }

    # ~~->$ Subject:FieldSet~~
    SUBJECT_AND_KEYWORDS = {
        "name": "subject_and_keywords",
        "label": "Subject classification and keywords",
        "fields": [
            FieldDefinitions.SUBJECT["name"],
            FieldDefinitions.KEYWORDS["name"]
        ]
    }

    # ~~->$ Subject:FieldSet~~
    KEYWORDS = {
        "name": "keywords",
        "label": "Keywords",
        "fields": [
            FieldDefinitions.KEYWORDS["name"]
        ]
    }

    # ~~->$ Notes:FieldSet~~
    NOTES = {
        "name": "notes",
        "label": "Notes",
        "fields": [
            FieldDefinitions.NOTES["name"],
            FieldDefinitions.NOTE["name"],
            FieldDefinitions.NOTE_AUTHOR["name"],
            FieldDefinitions.NOTE_DATE["name"],
            FieldDefinitions.NOTE_ID["name"],
            FieldDefinitions.NOTE_AUTHOR_ID["name"]
        ]
    }

    FLAGS = {
        "name": "flags",
        "label": "Flag",
        "fields": [
            FieldDefinitions.FLAGS["name"],
            FieldDefinitions.FLAG_SETTER["name"],
            FieldDefinitions.FLAG_CREATED_DATE["name"],
            FieldDefinitions.FLAG_DEADLINE["name"],
            FieldDefinitions.FLAG_NOTE["name"],
            FieldDefinitions.FLAG_NOTE_ID["name"],
            FieldDefinitions.FLAG_ASSIGNEE["name"],
            FieldDefinitions.FLAG_RESOLVED["name"],
        ]
    }

    # ~~->$ OptionalValidation:FieldSet~~
    OPTIONAL_VALIDATION = {
        "name": "optional_validation",
        "label": "Allow save without validation",
        "fields": [
            FieldDefinitions.OPTIONAL_VALIDATION["name"]
        ]
    }

    # ~~->$ BulkEdit:FieldSet~~
    # ~~^-> BulkEdit:Feature~~
    BULK_EDIT = {
        "name": "bulk_edit",
        "label": "Bulk edit",
        "fields": [
            FieldDefinitions.PUBLISHER_NAME["name"],
            FieldDefinitions.PUBLISHER_COUNTRY["name"],
            FieldDefinitions.OWNER["name"]
        ]
    }


###########################################################
# Define our Contexts
###########################################################

class ApplicationContextDefinitions:
    # ~~->$ NewApplication:FormContext~~
    # ~~^-> ApplicationForm:Crosswalk~~
    # ~~^-> NewApplication:FormProcessor~~

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
        "templates": {
            "form": templates.PUBLIC_APPLICATION_FORM,
            "default_field": templates.AF_FIELD,
            "default_group": templates.AF_GROUP
        },
        "crosswalks": {
            "obj2form": ApplicationFormXWalk.obj2form,
            "form2obj": ApplicationFormXWalk.form2obj
        },
        "processor": application_processors.NewApplication,
    }

    # ~~->$ UpdateRequest:FormContext~~
    # ~~^-> NewApplication:FormContext~~
    # ~~^-> UpdateRequest:FormProcessor~~
    UPDATE = deepcopy(PUBLIC)
    UPDATE["name"] = "update_request"
    UPDATE["processor"] = application_processors.PublisherUpdateRequest
    UPDATE["templates"]["form"] = templates.PUBLISHER_UPDATE_REQUEST_FORM
    UPDATE["fieldsets"] += [
        FieldSetDefinitions.KEYWORDS["name"],
    ]

    # ~~->$ ReadOnlyApplication:FormContext~~
    # ~~^-> NewApplication:FormContext~~
    READ_ONLY = deepcopy(PUBLIC)
    READ_ONLY["name"] = "application_read_only"
    READ_ONLY["processor"] = application_processors.NewApplication  # FIXME: enter the real processor
    READ_ONLY["templates"]["form"] = templates.PUBLISHER_READ_ONLY_APPLICATION
    READ_ONLY["fieldsets"] += [
        FieldSetDefinitions.KEYWORDS["name"],
    ]

    # ~~->$ AssociateEditorApplication:FormContext~~
    # ~~^-> NewApplication:FormContext~~
    # ~~^-> AssociateEditorApplication:FormProcessor~~
    ASSOCIATE = deepcopy(PUBLIC)
    ASSOCIATE["name"] = "associate_editor"
    ASSOCIATE["fieldsets"] += [
        FieldSetDefinitions.STATUS["name"],
        FieldSetDefinitions.SUBJECT_AND_KEYWORDS["name"],
        FieldSetDefinitions.NOTES["name"]
    ]
    ASSOCIATE["processor"] = application_processors.AssociateApplication
    ASSOCIATE["templates"]["form"] = templates.ASSED_APPLICATION_FORM

    # ~~->$ EditorApplication:FormContext~~
    # ~~^-> NewApplication:FormContext~~
    # ~~^-> EditorApplication:FormProcessor~~
    EDITOR = deepcopy(PUBLIC)
    EDITOR["name"] = "editor"
    EDITOR["fieldsets"] += [
        FieldSetDefinitions.STATUS["name"],
        FieldSetDefinitions.REVIEWERS["name"],
        FieldSetDefinitions.SUBJECT_AND_KEYWORDS["name"],
        FieldSetDefinitions.NOTES["name"]
    ]
    EDITOR["processor"] = application_processors.EditorApplication
    EDITOR["templates"]["form"] = templates.EDITOR_APPLICATION_FORM

    # ~~->$ ManEdApplication:FormContext~~
    # ~~^-> NewApplication:FormContext~~
    # ~~^-> ManEdApplication:FormProcessor~~
    MANED = deepcopy(PUBLIC)
    MANED["name"] = "admin"
    MANED["fieldsets"] += [
        FieldSetDefinitions.LABELS["name"],
        FieldSetDefinitions.QUICK_REJECT["name"],
        FieldSetDefinitions.REASSIGN["name"],
        FieldSetDefinitions.STATUS["name"],
        FieldSetDefinitions.REVIEWERS["name"],
        FieldSetDefinitions.CONTINUATIONS["name"],
        FieldSetDefinitions.SUBJECT_AND_KEYWORDS["name"],
        FieldSetDefinitions.NOTES["name"],
    ]
    MANED["processor"] = application_processors.AdminApplication
    MANED["templates"]["form"] = templates.MANED_APPLICATION_FORM

    # now we can update the Public Context with the correct "About" fieldset
    PUBLIC["fieldsets"] += [FieldSetDefinitions.KEYWORDS["name"]]


class JournalContextDefinitions:
    # ~~->$ ReadOnlyJournal:FormContext~~
    # ~~^-> JournalForm:Crosswalk~~
    # ~~^-> ReadOnlyJournal:FormProcessor~~
    ADMIN_READ_ONLY = {
        "name": "admin_readonly",
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
            FieldSetDefinitions.SUBJECT_AND_KEYWORDS["name"],

        ],
        "templates": {
            "form": templates.MANED_READ_ONLY_JOURNAL,
            "default_field": templates.AF_FIELD,
            "default_group": templates.AF_GROUP
        },
        "crosswalks": {
            "obj2form": JournalFormXWalk.obj2form,
            "form2obj": JournalFormXWalk.form2obj
        },
        "processor": application_processors.ReadOnlyJournal
    }

    # identical context for editors, mostly to support the different view contexts
    EDITOR_READ_ONLY = deepcopy(ADMIN_READ_ONLY)
    EDITOR_READ_ONLY["name"] = "editor_readonly"
    EDITOR_READ_ONLY["templates"]["form"] = templates.EDITOR_READ_ONLY_JOURNAL

    # ~~->$ AssEditorJournal:FormContext~~
    # ~~^-> ReadOnlyJournal:FormContext~~
    # ~~^-> AssEdJournal:FormProcessor~~
    ASSOCIATE = deepcopy(ADMIN_READ_ONLY)
    ASSOCIATE["fieldsets"] += [
        FieldSetDefinitions.NOTES["name"]
    ]
    ASSOCIATE["name"] = "associate_editor"
    ASSOCIATE["processor"] = application_processors.AssEdJournalReview
    ASSOCIATE["templates"]["form"] = templates.ASSED_JOURNAL_FORM

    # ~~->$ EditorJournal:FormContext~~
    # ~~^-> AssEdJournal:FormContext~~
    # ~~^-> EditorJournal:FormProcessor~~
    EDITOR = deepcopy(ASSOCIATE)
    EDITOR["name"] = "editor"
    EDITOR["fieldsets"] += [
        FieldSetDefinitions.REVIEWERS["name"]
    ]
    EDITOR["processor"] = application_processors.EditorJournalReview
    EDITOR["templates"]["form"] = templates.EDITOR_JOURNAL_FORM

    # ~~->$ ManEdJournal:FormContext~~
    # ~~^-> EditorJournal:FormContext~~
    # ~~^-> ManEdJournal:FormProcessor~~
    MANED = deepcopy(EDITOR)
    MANED["name"] = "admin"
    MANED["fieldsets"] += [
        FieldSetDefinitions.REASSIGN["name"],
        FieldSetDefinitions.OPTIONAL_VALIDATION["name"],
        FieldSetDefinitions.LABELS["name"],
        FieldSetDefinitions.CONTINUATIONS["name"],
        FieldSetDefinitions.FLAGS["name"],
        FieldSetDefinitions.LAST_FULL_REVIEW["name"]
    ]
    MANED["processor"] = application_processors.ManEdJournalReview
    MANED["templates"]["form"] = templates.MANED_JOURNAL_FORM

    # ~~->$ BulkEditJournal:FormContext~~
    # ~~^-> JournalForm:Crosswalk~~
    # ~~^-> ManEdJournal:FormProcessor~~
    BULK_EDIT = {
        "name": "bulk_edit",
        "fieldsets": [
            FieldSetDefinitions.BULK_EDIT["name"]
        ],
        "templates": {
            "form": templates.MANED_JOURNAL_BULK_EDIT,
            "default_field": templates.AF_FIELD,
            "default_group": templates.AF_GROUP
        },
        "crosswalks": {
            "obj2form": JournalFormXWalk.obj2form,
            "form2obj": JournalFormXWalk.form2obj
        },
        "processor": application_processors.ManEdBulkEdit
    }


#######################################################
# Gather all of our form information in one place
#######################################################

APPLICATION_FORMS = {
    "contexts": {
        ApplicationContextDefinitions.PUBLIC["name"]: ApplicationContextDefinitions.PUBLIC,
        ApplicationContextDefinitions.UPDATE["name"]: ApplicationContextDefinitions.UPDATE,
        ApplicationContextDefinitions.READ_ONLY["name"]: ApplicationContextDefinitions.READ_ONLY,
        ApplicationContextDefinitions.ASSOCIATE["name"]: ApplicationContextDefinitions.ASSOCIATE,
        ApplicationContextDefinitions.EDITOR["name"]: ApplicationContextDefinitions.EDITOR,
        ApplicationContextDefinitions.MANED["name"]: ApplicationContextDefinitions.MANED
    },
    "fieldsets": {v['name']: v for k, v in FieldSetDefinitions.__dict__.items() if not k.startswith('_')},
    "fields": {v['name']: v for k, v in FieldDefinitions.__dict__.items() if not k.startswith('_')}
}

JOURNAL_FORMS = {
    "contexts": {
        JournalContextDefinitions.ADMIN_READ_ONLY["name"]: JournalContextDefinitions.ADMIN_READ_ONLY,
        JournalContextDefinitions.EDITOR_READ_ONLY["name"]: JournalContextDefinitions.EDITOR_READ_ONLY,
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

def iso_country_list(field, formualic_context_name):
    # ~~-> Countries:Data~~
    cl = [{"display": " ", "value": ""}]
    for v, d in country_options:
        cl.append({"display": d, "value": v})
    return cl


def iso_language_list(field, formulaic_context_name):
    # ~~-> Languages:Data~~
    cl = [{"display": " ", "value": ""}]
    for v, d in language_options:
        cl.append({"display": d, "value": v})
    return cl


def iso_currency_list(field, formulaic_context_name):
    # ~~-> Currencies:Data~~
    cl = [{"display": " ", "value": ""}]
    quick_pick = []
    for v, d in currency_options:
        if v in ["GBP", "USD", "EUR"]:
            quick_pick.append({"display": d, "value": v})
        cl.append({"display": d, "value": v})
    if len(quick_pick) > 0:
        cl = quick_pick + cl
    return cl


def quick_reject(field, formulaic_context_name):
    # ~~-> QuickReject:Feature~~
    return [{"display": "Other", "value": ""}] + [{'display': v, 'value': v} for v in
                                                  app.config.get('QUICK_REJECT_REASONS', [])]


def application_statuses(field, formulaic_context):
    # ~~->$ ApplicationStatus:Workflow~~
    # ~~-> ApplicationStatuses:Config~~
    _application_status_base = [  # This is all the Associate Editor sees
        ('', ' '),
        (constants.APPLICATION_STATUS_PENDING, Messages.FORMS__APPLICATION_STATUS__PENDING),
        (constants.APPLICATION_STATUS_IN_PROGRESS, Messages.FORMS__APPLICATION_STATUS__IN_PROGRESS),
        (constants.APPLICATION_STATUS_COMPLETED, Messages.FORMS__APPLICATION_STATUS__COMPLETED)
    ]

    # Note that an admin is given the Post Submission Automation status, as technically they
    # may edit an item that's in this status, but it is functionally useless to them
    # It would be nice to be able to somehow disable it being changed, perhaps we can do that
    # via a widget
    _application_status_admin = _application_status_base + [
        (constants.APPLICATION_STATUS_POST_SUBMISSION_REVIEW,
         Messages.FORMS__APPLICATION_STATUS__POST_SUBMISSION_REVIEW),
        (constants.APPLICATION_STATUS_UPDATE_REQUEST, Messages.FORMS__APPLICATION_STATUS__UPDATE_REQUEST),
        (constants.APPLICATION_STATUS_REVISIONS_REQUIRED, Messages.FORMS__APPLICATION_STATUS__REVISIONS_REQUIRED),
        (constants.APPLICATION_STATUS_ON_HOLD, Messages.FORMS__APPLICATION_STATUS__ON_HOLD),
        (constants.APPLICATION_STATUS_READY, Messages.FORMS__APPLICATION_STATUS__READY),
        (constants.APPLICATION_STATUS_REJECTED, Messages.FORMS__APPLICATION_STATUS__REJECTED),
        (constants.APPLICATION_STATUS_ACCEPTED, Messages.FORMS__APPLICATION_STATUS__ACCEPTED)
    ]

    _application_status_editor = _application_status_base + [
        (constants.APPLICATION_STATUS_READY, Messages.FORMS__APPLICATION_STATUS__READY),
    ]

    formulaic_context_name = None
    if formulaic_context is not None:
        formulaic_context_name = formulaic_context.name

    status_list = []
    if formulaic_context_name is None or formulaic_context_name == "admin":
        status_list = _application_status_admin
    elif formulaic_context_name == "editor":
        status_list = _application_status_editor
    elif formulaic_context_name == "accepted":
        status_list = [(constants.APPLICATION_STATUS_ACCEPTED,
                        Messages.FORMS__APPLICATION_STATUS__ACCEPTED)]  # just the one status - Accepted
    else:
        status_list = _application_status_base

    return [{'display': d, 'value': v} for (v, d) in status_list]


def editor_choices(field, formulaic_context):
    """
    Set the editor field choices from a given editor group name
    ~~->EditorGroup:Model~~
    """
    egf = formulaic_context.get("editor_group")
    wtf = egf.wtfield
    if wtf is None:
        return [{"display": "", "value": ""}]

    editor_group_name = wtf.data
    if editor_group_name is None:
        return [{"display": "", "value": ""}]
    else:
        eg = EditorGroup.pull_by_key("name", editor_group_name)
        if eg is not None:
            editors = [eg.editor]
            editors += eg.associates
            editors = list(set(editors))
            return [{"value": "", "display": "No editor assigned"}] + [{"value": editor, "display": editor} for editor
                                                                       in editors]
        else:
            return [{"display": "", "value": ""}]


#######################################################
## Conditional disableds
#######################################################

def application_status_disabled(field, formulaic_context):
    choices = application_statuses(field, formulaic_context)
    field_value = field.wtfield.data
    return field_value not in [c.get("value") for c in choices]


def disable_edit_note_except_editing_user(field: FormulaicField,
                                          formulaic_context: FormulaicContext):
    """
    Only allow the current user to edit this field if author is current user

    :param field:
    :param formulaic_context:
    :return:
        False is editable, True is disabled
    """

    # ~~->Notes:Feature~~
    editing_user = formulaic_context.extra_param.get('editing_user')
    cur_user_id = editing_user and editing_user.id
    form_field: FormField = field.find_related_form_field('notes', formulaic_context)
    if form_field is None:
        return True
    return cur_user_id != form_field.data.get('note_author_id')


def disable_edit_flag_except_author_admin_assignee(field: FormulaicField,
                                                   formulaic_context: FormulaicContext):
    # This is currently not used but will be needed again when the flags feature will be made available for non-admin users

    """
    Only allow the current user to edit this field if current user is an author, assignee or admin

    :param field:
    :param formulaic_context:
    :return:
        False is editable, True is disabled
    """

    # ~~->Notes:Feature~~
    editing_user = formulaic_context.extra_param.get('editing_user')
    cur_user_id = editing_user and editing_user.id
    cur_user_is_admin = editing_user and editing_user.is_super
    form_field: FormField = field.find_related_form_field('notes', formulaic_context)
    if form_field is None:
        return True

    return (cur_user_id != form_field.data.get('flag_assignee') and
            cur_user_id != form_field.data.get('flag_setter') and
            not cur_user_is_admin)


#######################################################
## Merge disabled
#######################################################

def merge_disabled_notes(notes_group, original_form):
    # ~~->Notes:Feature~~
    merged = []
    wtf = notes_group.wtfield
    for entry in wtf.entries:
        if entry.data.get("note") != "" or entry.data.get("note_id") != "":
            merged.append(entry.data)
    for entry in original_form.notes.entries:
        d = entry.data
        for m in merged:
            if m.get("note_id") != "" and m.get("note_id") == entry.data.get("note_id"):
                # keep = False
                if m.get("note") == "":
                    m["note"] = entry.data.get("note")
                m["note_date"] = entry.data.get("note_date")
                break

    while True:
        try:
            wtf.pop_entry()
        except IndexError:
            break

    for m in merged:
        wtf.append_entry(m)


#######################################################
# Validation features
#######################################################

class ReservedUsernamesBuilder:
    """
    ~~->$ ReservedUsernames:FormValidator~~
    """

    @staticmethod
    def render(settings, html_attrs):
        return

    @staticmethod
    def wtforms(field, settings):
        return ReservedUsernames()


class OwnerExistsBuilder:
    """
    ~~->$ OwnerExists:FormValidator~~
    """

    @staticmethod
    def render(settings, html_attrs):
        return

    @staticmethod
    def wtforms(field, settings):
        return OwnerExists()


class RequiredBuilder:
    """
    ~~->$ Required:FormValidator~~
    """

    @staticmethod
    def render(settings, html_attrs):
        html_attrs["required"] = ""
        if "message" in settings:
            html_attrs["data-parsley-required-message"] = "<p><small>" + settings["message"] + "</small></p>"
        else:
            html_attrs["data-parsley-required-message"] = "<p><small>" + "This answer is required" + "</p></small>"
        html_attrs["data-parsley-validate-if-empty"] = "true"

    @staticmethod
    def wtforms(field, settings):
        return CustomRequired(message=settings.get("message"))


class IsURLBuilder:
    # ~~->$ IsURL:FormValidator~~
    msg = "<p><small>" + "Please enter a valid URL. It should start with http or https" + "</p></small>"

    @staticmethod
    def render(settings, html_attrs):
        html_attrs["type"] = "url"
        html_attrs["pattern"] = regex.HTTP_URL
        html_attrs["data-parsley-pattern"] = regex.HTTP_URL
        html_attrs["data-parsley-pattern-message"] = IsURLBuilder.msg

    @staticmethod
    def wtforms(field, settings):
        return HTTPURL(message=settings.get('message', IsURLBuilder.msg))


class IntRangeBuilder:
    """
    ~~->$ IntRange:FormValidator~~
    ~~^-> NumberRange:FormValidator~~
    """

    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-type"] = "digits"
        default_msg = ""
        if "gte" in settings and "lte" in settings:
            html_attrs["data-parsley-range"] = "[" + str(settings.get("gte")) + ", " + str(settings.get("lte")) + "]"
            default_msg = "This value should be between " + str(settings.get("gte")) + " and " + str(
                settings.get("lte"))
        else:
            if "gte" in settings:
                html_attrs["data-parsley-min"] = settings.get("gte")
                default_msg = "This value should be bigger than " + str(settings.get("gte"))
            if "lte" in settings:
                html_attrs["data-parsley-max"] = settings.get("lte")
                default_msg = "This value should be smaller than " + str(settings.get("gte"))
        html_attrs["data-parsley-range-message"] = "<p><small>" + settings.get("message", default_msg) + "</p></small>"

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
    """
    ~~->$ MaxLen:FormValidator~~
    """

    @staticmethod
    def wtforms(field, settings):
        max = settings.get("max")
        message = settings.get("message") if "message" in settings else 'You can only enter up to {x} keywords.'.format(
            x=max)
        return MaxLen(max, message=message)


class StopWordsBuilder:
    """
    ~~->$ StopWords:FormValidator~~
    """

    @staticmethod
    def wtforms(field, settings):
        stopwords = settings.get("disallowed", [])
        return StopWords(stopwords)


class ISSNInPublicDOAJBuilder:
    """
    ~~->$ ISSNInPublicDOAJ:FormValidator~~
    """

    @staticmethod
    def render(settings, html_attrs):
        # FIXME: not yet implemented in the front end, so setting here is speculative
        html_attrs["data-parsley-issn-in-public-doaj"] = ""

    @staticmethod
    def wtforms(field, settings):
        return ISSNInPublicDOAJ(message=settings.get("message"))


class JournalURLInPublicDOAJBuilder:
    # ~~->$ JournalURLInPublicDOAJ:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        # FIXME: not yet implemented in the front end, so setting here is speculative
        html_attrs["data-parsley-journal-url-in-public-doaj"] = ""

    @staticmethod
    def wtforms(field, settings):
        return JournalURLInPublicDOAJ(message=settings.get("message"))


class NoScriptTagBuilder:
    # ~~->$ NoScriptTag:FormValidator
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-no-script-tag"] = ""
        if "message" in settings:
            html_attrs["data-parsley-noScriptTag-message"] = "<p><small>" + settings["message"] + "</small></p>"
        else:
            html_attrs["data-parsley-no-script-tag-message"] = "<p><small>" + "No script tags allowed" + "</p></small>"

    @staticmethod
    def wtforms(field, settings):
        return NoScriptTag(settings.get("message", "No script tags allowed"))


class OptionalIfBuilder:
    # ~~->$ OptionalIf:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-validate-if-empty"] = "true"
        html_attrs["data-parsley-optional-if"] = settings.get("field")
        html_attrs["data-parsley-optional-if-message"] = "<p><small>" + settings.get("message") + "</p></small>"

    @staticmethod
    def wtforms(field, settings):
        return OptionalIf(settings.get("field") or field, settings.get("message"), settings.get("values", []))


class IsISSNBuilder:
    # ~~->$ IsISSN:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["pattern"] = ISSN
        html_attrs["data-parsley-pattern"] = ISSN
        html_attrs["data-parsley-pattern-message"] = settings.get("message")

    @staticmethod
    def wtforms(field, settings):
        return validators.Regexp(regex=ISSN_COMPILED, message=settings.get("message"))


class IsISSNListBuilder:
    # ~~->$ IsISSNList:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-entry-pattern"] = ISSN

    @staticmethod
    def wtforms(field, settings):
        return RegexpOnTagList(regex=ISSN_COMPILED, message=settings.get("message"))


class DifferentToBuilder:
    # ~~->$ DifferentTo:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-different-to"] = settings.get("field")
        html_attrs["data-parsley-different-to-message"] = "<p><small>" + settings.get("message") + "</small></p>"

    @staticmethod
    def wtforms(field, settings):
        return DifferentTo(settings.get("field") or field, settings.get("ignore_empty", True), settings.get("message"))


class RequiredIfBuilder:
    # ~~->$ RequiredIf:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        val = settings.get("value", constants.DUMMY_STRING)
        if isinstance(val, list):
            val = ",".join(val)

        if settings.get("skip_disabled"):
            html_attrs["data-parsley-validate-if-disabled"] = "false"

        html_attrs["data-parsley-validate-if-empty"] = "true"
        html_attrs["data-parsley-required-if"] = val
        html_attrs["data-parsley-required-if-field"] = settings.get("field")
        if "message" in settings:
            html_attrs["data-parsley-required-if-message"] = "<p><small>" + settings["message"] + "</small></p>"
        else:
            html_attrs["data-parsley-required-if-message"] = "<p><small>" + "This answer is required" + "</small></p>"

    @staticmethod
    def wtforms(field, settings):
        return RequiredIfOtherValue(settings.get("field") or field, settings.get("value"), settings.get("message"))


class OnlyIfBuilder:
    # ~~->$ OnlyIf:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-only-if"] = ",".join([f["field"] for f in settings.get("fields", [])])
        for f in settings.get('fields'):
            if "value" in f:
                html_attrs["data-parsley-only-if-value_" + f["field"]] = f["value"]
            if "not" in f:
                html_attrs["data-parsley-only-if-not_" + f["field"]] = f["not"]
            if "or" in f:
                html_attrs["data-parsley-only-if-or_" + f["field"]] = ",".join(f["or"])
        html_attrs["data-parsley-only-if-message"] = settings.get("message")

    @staticmethod
    def wtforms(fields, settings):
        return OnlyIf(other_fields=settings.get('fields') or fields, ignore_empty=settings.get('ignore_empty', True),
                      message=settings.get('message'))


class OnlyIfExistsBuilder:
    # ~~->$ OnlyIf:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-only-if-exists"] = ",".join([f["field"] for f in settings.get("fields", [])])
        html_attrs["data-parsley-only-if-exists-message"] = "<p><small>" + settings.get("message") + "</small></p>"

    @staticmethod
    def wtforms(fields, settings):
        return OnlyIfExists(other_fields=settings.get('fields') or fields,
                            ignore_empty=settings.get('ignore_empty', True), message=settings.get('message'))


class NotIfBuildier:
    # ~~->$ NotIf:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-not-if"] = ",".join([f.get("field") for f in settings.get("fields", [])])
        if settings.get("message"):
            html_attrs["data-parsley-not-if-message"] = settings.get("message")

    @staticmethod
    def wtforms(fields, settings):
        return NotIf(settings.get('fields') or fields, settings.get('message'))


class GroupMemberBuilder:
    # ~~->$ GroupMember:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        # FIXME: front end validator for this does not yet exist (do we have an existing one from formcontext?)
        html_attrs["data-parsley-group-member-field"] = settings.get("group_field")

    @staticmethod
    def wtforms(field, settings):
        return GroupMember(settings.get('group_field') or field)


class RequiredValueBuilder:
    # ~~->$ RequiredValue:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-requiredvalue"] = settings.get("value")

    @staticmethod
    def wtforms(field, settings):
        return RequiredValue(settings.get("value"), settings.get("message"))


class BigEndDateBuilder:
    # ~~->$ BigEndDate:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-validdate"] = ""
        ignore_empty = settings.get("ignore_empty", False)
        html_attrs["data-parsley-validdate-ignore_empty"] = "true" if ignore_empty else "false"
        html_attrs["data-parsley-pattern-message"] = settings.get("message")

    @staticmethod
    def wtforms(field, settings):
        return BigEndDate(settings.get("message"))

class DateInThePastBuilder:
    # ~~->$ BigEndDate:FormValidator~~
    @staticmethod
    def render(settings, html_attrs):
        # no client side rendering for this, as it interferes with the datepicker
        pass

    @staticmethod
    def wtforms(field, settings):
        return DateInThePast(settings.get("message"))

class YearBuilder:
    @staticmethod
    def render(settings, html_attrs):
        html_attrs["data-parsley-year"] = app.config.get('MINIMAL_OA_START_DATE', 1900)
        html_attrs["data-parsley-year-message"] = "<p><small>" + settings["message"] + "</small></p>"

    @staticmethod
    def wtforms(field, settings):
        return Year(settings.get("message"))


class CurrentISOCurrencyBuilder:
    @staticmethod
    def render(settings, html_attrs):
        pass

    @staticmethod
    def wtforms(field, settings):
        return CurrentISOCurrency(settings.get("message"))


class CurrentISOLanguageBuilder:
    @staticmethod
    def render(settings, html_attrs):
        pass

    @staticmethod
    def wtforms(field, settings):
        return CurrentISOLanguage(settings.get("message"))


#########################################################
# Crosswalks
#########################################################

PYTHON_FUNCTIONS = {
    "options": {
        "iso_country_list": iso_country_list,
        "iso_language_list": iso_language_list,
        "iso_currency_list": iso_currency_list,
        "quick_reject": quick_reject,
        "application_statuses": application_statuses,
        "editor_choices": editor_choices
    },
    "disabled": {
        "application_status_disabled": application_status_disabled,
        "disable_edit_note_except_editing_user": disable_edit_note_except_editing_user,
        "disable_edit_flag_except_author_admin_assignee": disable_edit_flag_except_author_admin_assignee
    },
    "merge_disabled": {
        "merge_disabled_notes": merge_disabled_notes
    },
    "validate": {
        "render": {
            "required": RequiredBuilder.render,
            "is_url": IsURLBuilder.render,
            "int_range": IntRangeBuilder.render,
            "issn_in_public_doaj": ISSNInPublicDOAJBuilder.render,
            "journal_url_in_public_doaj": JournalURLInPublicDOAJBuilder.render,
            "optional_if": OptionalIfBuilder.render,
            "is_issn": IsISSNBuilder.render,
            "is_issn_list": IsISSNListBuilder.render,
            "different_to": DifferentToBuilder.render,
            "required_if": RequiredIfBuilder.render,
            "only_if": OnlyIfBuilder.render,
            "only_if_exists": OnlyIfExistsBuilder.render,
            "group_member": GroupMemberBuilder.render,
            "not_if": NotIfBuildier.render,
            "required_value": RequiredValueBuilder.render,
            "bigenddate": BigEndDateBuilder.render,
            "no_script_tag": NoScriptTagBuilder.render,
            "year": YearBuilder.render,
            "date_in_the_past": DateInThePastBuilder.render
        },
        "wtforms": {
            "required": RequiredBuilder.wtforms,
            "is_url": IsURLBuilder.wtforms,
            "max_tags": MaxTagsBuilder.wtforms,
            "int_range": IntRangeBuilder.wtforms,
            "stop_words": StopWordsBuilder.wtforms,
            "issn_in_public_doaj": ISSNInPublicDOAJBuilder.wtforms,
            "journal_url_in_public_doaj": JournalURLInPublicDOAJBuilder.wtforms,
            "optional_if": OptionalIfBuilder.wtforms,
            "is_issn": IsISSNBuilder.wtforms,
            "is_issn_list": IsISSNListBuilder.wtforms,
            "different_to": DifferentToBuilder.wtforms,
            "required_if": RequiredIfBuilder.wtforms,
            "only_if": OnlyIfBuilder.wtforms,
            "only_if_exists": OnlyIfExistsBuilder.wtforms,
            "group_member": GroupMemberBuilder.wtforms,
            "not_if": NotIfBuildier.wtforms,
            "required_value": RequiredValueBuilder.wtforms,
            "bigenddate": BigEndDateBuilder.wtforms,
            "reserved_usernames": ReservedUsernamesBuilder.wtforms,
            "owner_exists": OwnerExistsBuilder.wtforms,
            "no_script_tag": NoScriptTagBuilder.wtforms,
            "year": YearBuilder.wtforms,
            "current_iso_currency": CurrentISOCurrencyBuilder.wtforms,
            "current_iso_language": CurrentISOLanguageBuilder.wtforms,
            "date_in_the_past": DateInThePastBuilder.wtforms
        }
    }
}

JAVASCRIPT_FUNCTIONS = {
    "clickable_url": "formulaic.widgets.newClickableUrl",  # ~~-> ClickableURL:FormWidget~~
    "click_to_copy": "formulaic.widgets.newClickToCopy",  # ~~-> ClickToCopy:FormWidget~~
    "clickable_owner": "formulaic.widgets.newClickableOwner",  # ~~-> ClickableOwner:FormWidget~~
    "select": "formulaic.widgets.newSelect",  # ~~-> SelectBox:FormWidget~~
    "taglist": "formulaic.widgets.newTagList",  # ~~-> TagList:FormWidget~~
    "tagentry": "formulaic.widgets.newTagEntry",  # ~~-> TagEntry:FormWidget~~
    "multiple_field": "formulaic.widgets.newMultipleField",  # ~~-> MultiField:FormWidget~~
    "infinite_repeat": "formulaic.widgets.newInfiniteRepeat",  # ~~-> InfiniteRepeat:FormWidget~~
    "autocomplete": "formulaic.widgets.newAutocomplete",  # ~~-> Autocomplete:FormWidget~~
    "subject_tree": "formulaic.widgets.newSubjectTree",  # ~~-> SubjectTree:FormWidget~~
    "full_contents": "formulaic.widgets.newFullContents",  # ~~^->FullContents:FormWidget~~
    "load_editors": "formulaic.widgets.newLoadEditors",  # ~~-> LoadEditors:FormWidget~~
    "trim_whitespace": "formulaic.widgets.newTrimWhitespace",  # ~~-> TrimWhitespace:FormWidget~~
    "note_modal": "formulaic.widgets.newNoteModal",  # ~~-> NoteModal:FormWidget~~,
    "autocheck": "formulaic.widgets.newAutocheck",  # ~~-> Autocheck:FormWidget~~
    "issn_link": "formulaic.widgets.newIssnLink",  # ~~-> IssnLink:FormWidget~~,
    "article_info": "formulaic.widgets.newArticleInfo",  # ~~-> ArticleInfo:FormWidget~~
    "flag_manager": "formulaic.widgets.newFlagManager",  # ~~-> FlagManager:FormWidget~~
    "date_picker": "formulaic.widgets.newDatePicker"  # ~~-> DatePicker:FormWidget~~

}


##############################################################
# A couple of convenient widgets for WTForms rendering
##############################################################

class NumberWidget(widgets.Input):
    input_type = 'number'

class FieldsetWidget(object):
    """
       Renders a fieldset with a legend
       if legend_display is true the question is displayed
       if legend_display is false it is for screen readers only
    """
    def __init__(self, legend, sr_only_label = True, prefix_label=False):
        self.sr_only = sr_only_label
        self.prefix_label = prefix_label

        self.legend = f'<legend '
        if self.sr_only:
            self.legend += f'class="sr-only"'
        self.legend += f'>{legend}</legend>'

        self.html_wrapper = f"<fieldset> {self.legend} [BODY]</fieldset>"

    def __call__(self, field, **kwargs):
        fields = ''
        for subfield in field:
            fields += f'{subfield.label}{subfield(**kwargs)}' if self.prefix_label else f'{subfield(**kwargs)}{subfield.label}'

        html = self.html_wrapper.replace("[BODY]", fields)
        return HTMLString(''.join(html))


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
                html.append('<li tabindex=0>%s %s' % (subfield.label, subfield(**kwargs)))
            else:
                label = str(subfield.label)
                html.append('<li tabindex=0>%s %s' % (subfield(**kwargs), label))

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
        # wtfargs["widget"] = ListWidgetWithSubfields()
        wtfargs["widget"] = FieldsetWidget(legend=field.get("label"), sr_only_label=True)
        return UnconstrainedRadioField(**wtfargs)


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
        if "filters" not in wtfargs:
            wtfargs["filters"] = (lambda x: x.strip() if x is not None else x,)
        sf = StringField(**wtfargs)
        if "repeatable" in field:
            sf = FieldList(sf, min_entries=field.get("repeatable", {}).get("initial", 1))
        return sf

class DateBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "date"

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        wtfargs["widget"] = widgets.Input(input_type="date")
        sf = DateField(**wtfargs)
        if "repeatable" in field:
            sf = FieldList(sf, min_entries=field.get("repeatable", {}).get("initial", 1))
        return sf

class TextAreaBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "textarea"

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        sf = TextAreaField(**wtfargs)
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
        return NestedFormField(klazz)


class GroupListBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "group" and field.get("repeatable") is not None

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        ff = GroupBuilder.wtform(formulaic_context, field, wtfargs)
        repeat_cfg = field.get("repeatable", {})
        return FieldList(ff, min_entries=repeat_cfg.get("initial", 1))


class HiddenFieldBuilder(WTFormsBuilder):
    @staticmethod
    def match(field):
        return field.get("input") == "hidden"

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        return HiddenField(**wtfargs)


WTFORMS_BUILDERS = [
    RadioBuilder,
    MultiCheckboxBuilder,
    SingleCheckboxBuilder,
    SelectBuilder,
    MultiSelectBuilder,
    TextBuilder,
    TextAreaBuilder,
    TagListBuilder,
    IntegerBuilder,
    GroupBuilder,
    GroupListBuilder,
    HiddenFieldBuilder,
    DateBuilder
]

ApplicationFormFactory = Formulaic(APPLICATION_FORMS, WTFORMS_BUILDERS, function_map=PYTHON_FUNCTIONS,
                                   javascript_functions=JAVASCRIPT_FUNCTIONS)
JournalFormFactory = Formulaic(JOURNAL_FORMS, WTFORMS_BUILDERS, function_map=PYTHON_FUNCTIONS,
                               javascript_functions=JAVASCRIPT_FUNCTIONS)

if __name__ == "__main__":
    """
    Running this file from the command line enables you to output documentation for a given form context.

    See `docs/forms.sh` for where this is used

    To create the documentation you can call this file with 3 arguments:

    -t - the object type to output.  Either 'journal' or 'application'
    -c - the form context.  Will be one of the contexts defined elsewhere in this file, which may be specific to the
            object type.  For example, 'admin' or 'editor'
    -o - the path to the file where to output the result

    The output is a CSV which lists the following information:

    * Form Position - the position in the form.  Felds are listed in order
    * Field Name - the form field name
    * Label - the form field label
    * Input Type - what kind of input (e.g. radio, text)
    * Options - the express options allowed, or the name of the function which generates the options
    * Disabled? - is the field disabled in this context
    * Fieldset ID - the ID (from this file) of the fieldset that this field is part of
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--type", help="object type to output")
    parser.add_argument("-c", "--context", help="context to output")
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    if not args.context:
        print("Please specify a context to output")
        parser.print_help()
        exit()

    if not args.type:
        print("Please specify a type to output")
        parser.print_help()
        exit()

    fc = None
    if args.type == "journal":
        fc = JournalFormFactory.context(args.context)
    elif args.type == "application":
        fc = ApplicationFormFactory.context(args.context)

    if fc is not None:
        fc.to_summary_csv(args.out)
    else:
        print("You did not enter a valid type.  Use one of 'journal' or 'application'")
