FORMS = {
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
            ]
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
                "peer_review"
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
            "conditional" : [{"field" : "boai", "value" : True}],
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
            "options" : "iso_country_list",     # means to get the list from a function
            "multiple" : False,
            "help": {
                "description": "",
                "tooltip": """The country where the publisher carries out its business operations and is registered.""",
            },
            "validate" : [
                "required"
            ],
            "widgets" : [
                {"autocomplete" : {"field" : "country"}}
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
                {"max_tags" : {"max" : 6}},
                "stop_words"
            ],
            "postprocessing" : [
                "to_lower"
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
            "input" : "text",
            "help" : {
                "placeholder" : "Other peer review"
            },
            "asynchronous_warning" : [
                {"warn_on_value" : {"value" : "None"}}
            ]
        }
    }

}

def iso_country_list():
    from portality.formcontext.choices import Choices
    cl = []
    for v, d in Choices.country():
        cl.append({"display" : d, "value" : v})
    return cl


PYTHON_FUNCTIONS = {
    "iso_country_list" : "portality.formcontext.form_definitions.iso_country_list",
    "required" : "portality.formcontext.validators.required",
    "is_url" : "portality.formcontext.validators.is_url",
    "all_urls_the_same" : "portality.formcontext.validators.all_urls_the_same",
    "required_value" : "portality.formcontext.validators.required_value",
    "max_tags" : "portality.formcontext.validators.max_tags",
    "stop_words" : "portality.formcontext.validators.stop_words",
    "to_lower" : "portality.formcontext.postprocessing.to_lower",
    "int_range" : "portality.formcontext.validators.int_range",
    "warn_on_value" : "portality.formcontext.validators.warn_on_value",
    "clickable_url" : "portality.formcontext.widgets.clickable_url"
}


JAVASCRIPT_FUNCTIONS = {
    "required_value" : "doaj.forms.validators.requiredValue",
    "required" : "doaj.forms..validators.required",
    "is_url" : "doaj.forms.validators.isUrl",
    "max_tags" : "doaj.forms.validators.maxTags",
    "stop_words" : "doaj.forms.validators.stopWords",
    "int_range" : "doaj.forms.validators.intRange",
    "autocomplete" : "doaj.forms.widgets.autocomplete",
    "clickable_url" : "formulaic.widgets.newClickableUrl"
}

if __name__ == "__main__":
    from portality.lib.formulaic import Formulaic, FormulaicException
    import json

    try:
        f = Formulaic(FORMS, function_map=PYTHON_FUNCTIONS)
        c = f.context("public")
        print(json.dumps(c._definition, indent=2))
        w = c.wtform()
        for field in w:
            print(field())
    except FormulaicException as e:
        print(e.message)
        raise e