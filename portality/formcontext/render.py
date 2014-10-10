from portality.formcontext.formhelper import FormHelper
from portality.formcontext.choices import Choices
from copy import deepcopy

class Renderer(object):
    def __init__(self):
        self.FIELD_GROUPS = {}
        self.fh = FormHelper()
        self._error_fields = []
        self._disabled_fields = []

    def render_field_group(self, form_context, field_group_name=None):
        if field_group_name is None:
            return self._render_all(form_context)

        # get the group definition
        group_def = self.FIELD_GROUPS.get(field_group_name)
        if group_def is None:
            return ""

        # build the frag
        frag = ""
        for entry in group_def:
            field_name = entry.keys()[0]
            config = entry.get(field_name)

            config = self._rewrite_extra_fields(form_context, config)
            field = form_context.form[field_name]

            if field_name in self.disabled_fields:
                config = deepcopy(config)
                config["disabled"] = "disabled"

            frag += self.fh.render_field(field, **config)

        return frag

    @property
    def error_fields(self):
        return self._error_fields

    def set_error_fields(self, fields):
        self._error_fields = fields

    @property
    def disabled_fields(self):
        return self._disabled_fields

    def set_disabled_fields(self, fields):
        self._disabled_fields = fields

    def _rewrite_extra_fields(self, form_context, config):
        if "extra_input_fields" in config:
            config = deepcopy(config)
            for opt, field_ref in config.get("extra_input_fields").iteritems():
                extra_field = form_context.form[field_ref]
                config["extra_input_fields"][opt] = extra_field
        return config

    def _render_all(self, form_context):
        frag = ""
        for field in form_context.form:
            frag += self.fh.render_field(form_context, field.short_name)
        return frag


class ApplicationRenderer(Renderer):
    def __init__(self):
        super(ApplicationRenderer, self).__init__()

        # allow the subclass to define the order the groups should be considered in.  This is useful for
        # numbering questions and determining first errors
        self.GROUP_ORDER = ["basic_info", "editorial_process", "openness", "content_licensing", "copyright", "submitter_info"]

        # define the basic field groups
        self.FIELD_GROUPS = {
            "basic_info" : [
                {"title" : {"class": "input-xlarge"}},
                {"url" : {"class": "input-xlarge"}},
                {"alternative_title" : {"class": "input-xlarge"}},
                {"pissn" : {"class": "input-small", "size": "9", "maxlength": "9"}},
                {"eissn" : {"class": "input-small", "size": "9", "maxlength": "9"}},
                {"publisher" : {"class": "input-xlarge"}},
                {"society_institution" : {"class": "input-xlarge"}},
                {"platform" : {"class": "input-xlarge"}},
                {"contact_name" : {}},
                {"contact_email" : {}},
                {"confirm_contact_email" : {}},
                {"country" : {"class": "input-large"}},
                {"processing_charges" : {}},
                {"processing_charges_amount" : {"class": "input-mini"}},
                {"processing_charges_currency" : {"class": "input-large"}},
                {"submission_charges" : {}},
                {"submission_charges_amount" : {"class": "input-mini"}},
                {"submission_charges_currency" : {"class": "input-large"}},
                {"articles_last_year" : {"class": "input-mini"}},
                {"articles_last_year_url" : {"class": "input-xlarge"}},
                {"waiver_policy" : {}},
                {"waiver_policy_url" : {"class": "input-xlarge"}},
                {
                    "digital_archiving_policy" : {
                        "extra_input_fields" : {
                            Choices.digital_archiving_policy_val("other") : "digital_archiving_policy_other",
                            Choices.digital_archiving_policy_val("library") : "digital_archiving_policy_library"
                        }
                    }
                },
                {"digital_archiving_policy_url" : {"class": "input-xlarge"}},
                {"crawl_permission" : {}},
                {
                    "article_identifiers" : {
                        "extra_input_fields": {
                            Choices.article_identifiers_val("other") : "article_identifiers_other"
                        }
                    }
                },
                {"metadata_provision" : {}},
                {"download_statistics" : {}},
                {"download_statistics_url" : {"class": "input-xlarge"}},
                {"first_fulltext_oa_year" : {"class": "input-mini"}},
                {
                    "fulltext_format" : {
                        "extra_input_fields": {
                            Choices.fulltext_format_val("other") : "fulltext_format_other"
                        }
                    }
                },
                {"keywords" : {"class": "input-xlarge"}},
                {"languages" : {"class": "input-xlarge"}}
            ],

            "editorial_process" : [
                {"editorial_board_url" : {"class": "input-xlarge"}},
                {"review_process" : {}},
                {"review_process_url" : {"class": "input-xlarge"}},
                {"aims_scope_url" : {"class": "input-xlarge"}},
                {"instructions_authors_url" : {"class": "input-xlarge"}},
                {"plagiarism_screening" : {}},
                {"plagiarism_screening_url" : {"class": "input-xlarge"}},
                {"publication_time" : {"class": "input-tiny"}}
            ],

            "openness" : [
                {"oa_statement_url" : {"class": "input-xlarge"}}
            ],

            "content_licensing" : [
                {"license_embedded" : {}},
                {"license_embedded_url" : {"class": "input-xlarge"}},
                {
                    "license" : {
                        "extra_input_fields": {
                            Choices.licence_val("other") : "license_other"
                        }
                    }
                },
                {"license_checkbox" : {}},
                {"license_url" : {"class": "input-xlarge"}},
                {"open_access" : {}},
                {
                    "deposit_policy" : {
                        "extra_input_fields": {
                            Choices.open_access_val("other") : "deposit_policy_other"
                        }
                    }
                }
            ],

            "copyright" : [
                {
                    "copyright" : {
                        "extra_input_fields": {
                            Choices.copyright_val("other") :  "copyright_other"
                        }
                    }
                },
                {"copyright_url" : {"class": "input-xlarge"}},
                {
                    "publishing_rights" : {
                        "extra_input_fields": {
                            Choices.publishing_rights_val("other") : "publishing_rights_other"
                        }
                    }
                },
                {"publishing_rights_url" : {"class": "input-xlarge"}}
            ],

            "submitter_info" : [
                {"suggester_name" : {}},
                {"suggester_email" : {"class": "input-xlarge"}},
                {"suggester_email_confirm" : {"class": "input-xlarge"}},
            ]
        }

    def number_questions(self):
        q = 1
        for g in self.GROUP_ORDER:
            cfg = self.FIELD_GROUPS.get(g)
            for obj in cfg:
                field = obj.keys()[0]
                obj[field]["q_num"] = str(q)
                q += 1

    def set_error_fields(self, fields):
        super(ApplicationRenderer, self).set_error_fields(fields)

        # find the first error in the form and tag it
        found = False
        for g in self.GROUP_ORDER:
            cfg = self.FIELD_GROUPS.get(g)
            for obj in cfg:
                field = obj.keys()[0]
                if field in self.error_fields:
                    obj[field]["first_error"] = True
                    found = True
                    break
            if found:
                break



class PublicApplicationRenderer(ApplicationRenderer):
    def __init__(self):
        super(PublicApplicationRenderer, self).__init__()

        # explicitly call number questions, as it is not called by default (because other implementations may want
        # to mess with the group order and field groups first
        self.number_questions()

class ManEdApplicationReviewRenderer(ApplicationRenderer):
    def __init__(self):
        super(ManEdApplicationReviewRenderer, self).__init__()

        # extend the list of field groups
        self.FIELD_GROUPS["status"] = [
            {"application_status" : {"class" : "input-large"}}
        ]
        self.FIELD_GROUPS["account"] = [
            {"owner" : {"class" : "input-large"}}
        ]
        self.FIELD_GROUPS["subject"] = [
            {"subject" : {}}
        ]
        self.FIELD_GROUPS["editorial"] = [
            {"editor_group" : {"class" : "input-large"}},
            {"editor" : {"class" : "input-large"}}
        ]
        self.FIELD_GROUPS["notes"] = [
            {
                "notes" : {
                    "render_subfields_horizontal" : True,
                    "container_class" : "deletable",
                    "subfield_display-note" : "8",
                    "subfield_display-date" : "3"
                }
            }
        ]

        self.number_questions()

class EditorApplicationReviewRenderer(ApplicationRenderer):
    def __init__(self):
        super(EditorApplicationReviewRenderer, self).__init__()

        # extend the list of field groups
        self.FIELD_GROUPS["status"] = [
            {"application_status" : {"class" : "input-large"}}
        ]
        self.FIELD_GROUPS["subject"] = [
            {"subject" : {}}
        ]
        self.FIELD_GROUPS["editorial"] = [
            {"editor_group" : {"class" : "input-large"}},
            {"editor" : {"class" : "input-large"}}
        ]
        self.FIELD_GROUPS["notes"] = [
            {
                "notes" : {
                    "render_subfields_horizontal" : True,
                    "subfield_display-note" : "8",
                    "subfield_display-date" : "3"
                }
            }
        ]

        self.number_questions()

class AssEdApplicationReviewRenderer(ApplicationRenderer):
    def __init__(self):
        super(AssEdApplicationReviewRenderer, self).__init__()

        # extend the list of field groups
        self.FIELD_GROUPS["status"] = [
            {"application_status" : {"class" : "input-large"}}
        ]
        self.FIELD_GROUPS["subject"] = [
            {"subject" : {}}
        ]
        self.FIELD_GROUPS["notes"] = [
            {
                "notes" : {
                    "render_subfields_horizontal" : True,
                    "subfield_display-note" : "8",
                    "subfield_display-date" : "3"
                }
            }
        ]

        self.number_questions()
