from portality.formcontext.formhelper import FormHelperBS3
from portality.formcontext.choices import Choices
from copy import deepcopy

class Renderer(object):
    def __init__(self):
        self.FIELD_GROUPS = {}
        self.fh = FormHelperBS3()
        self._error_fields = []
        self._disabled_fields = []
        self._disable_all_fields = False
        self._highlight_completable_fields = False

    def check_field_group_exists(self, field_group_name):
        """ Return true if the field group exists in this form """
        group_def = self.FIELD_GROUPS.get(field_group_name)
        if group_def is None:
            return False
        else:
            return True

    def render_field_group(self, form_context, field_group_name=None, group_cfg=None):
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
            config = deepcopy(config)

            config = self._rewrite_extra_fields(form_context, config)
            field = form_context.form[field_name]

            if field_name in self.disabled_fields or self._disable_all_fields is True:
                config["disabled"] = "disabled"

            if self._highlight_completable_fields is True:
                valid = field.validate(form_context.form)
                config["complete_me"] = not valid

            if group_cfg is not None:
                config.update(group_cfg)

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

    def disable_all_fields(self, disable):
        self._disable_all_fields = disable

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

    def find_field(self, field, field_group):
        for index, item in enumerate(self.FIELD_GROUPS[field_group]):
            if field in item:
                return index

    def insert_field_after(self, field_to_insert, after_this_field, field_group):
        self.FIELD_GROUPS[field_group].insert(
            self.find_field(after_this_field, field_group) + 1,
            field_to_insert
        )


class BasicJournalInformationRenderer(Renderer):
    def __init__(self):
        super(BasicJournalInformationRenderer, self).__init__()

        # allow the subclass to define the order the groups should be considered in.  This is useful for
        # numbering questions and determining first errors
        self.NUMBERING_ORDER = ["basic_info", "editorial_process", "openness", "content_licensing", "copyright"]
        self.ERROR_CHECK_ORDER = deepcopy(self.NUMBERING_ORDER)

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
                {"processing_charges_url" : {"class": "input-xlarge"}},
                {"processing_charges_amount" : {"class": "input-mini"}},
                {"processing_charges_currency" : {"class": "input-large"}},
                {"submission_charges" : {}},
                {"submission_charges_url" : {"class": "input-xlarge"}},
                {"submission_charges_amount" : {"class": "input-mini"}},
                {"submission_charges_currency" : {"class": "input-large"}},
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
                {"review_process" : {"class" : "form-control input-xlarge"}},
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
                    "copyright" : {}
                },
                {"copyright_url" : {"class": "input-xlarge"}},
                {
                    "publishing_rights" : {}
                },
                {"publishing_rights_url" : {"class": "input-xlarge"}}
            ]
        }

    def check_field_groups(self):
        '''
        Check whether field groups which are being referenced in various renderer lists actually exist.

        Should only be called in self.__init__ by non-abstract classes,
        i.e. the bottom of the inheritance tree, the ones that would
        actually get used to render forms.

        Otherwise the check becomes meaningless (and always fails) as it will check whether
        all groups are defined in a class that isn't supposed to have all
        the definitions - being abstract, it may only have a few common ones.
        '''
        for group in self.NUMBERING_ORDER:
            try:
                self.FIELD_GROUPS[group]
            except KeyError as e:
                raise KeyError(
                    'Can\'t number a group which does not exist. '
                    'Field group "{0}" is not defined in self.FIELD_GROUPS '
                    'but is present in self.NUMBERING_ORDER. '
                    'This is in renderer {1}.'.format(e.message, self.__class__.__name__)
                )

        for group in self.ERROR_CHECK_ORDER:
            try:
                self.FIELD_GROUPS[group]
            except KeyError as e:
                raise KeyError(
                    'Can\'t check a group which does not exist for errors. '
                    'Field group "{0}" is not defined in self.FIELD_GROUPS '
                    'but is present in self.ERROR_CHECK_ORDER. '
                    'This is in renderer {1}.'.format(e.message, self.__class__.__name__)
                )

    def number_questions(self):
        q = 1
        for g in self.NUMBERING_ORDER:
            cfg = self.FIELD_GROUPS.get(g)
            for obj in cfg:
                field = obj.keys()[0]
                obj[field]["q_num"] = str(q)
                q += 1

    def question_number(self, field):
        for g in self.FIELD_GROUPS:
            cfg = self.FIELD_GROUPS.get(g)
            for obj in cfg:
                f = obj.keys()[0]
                if f == field and "q_num" in obj[f]:
                    return obj[f]["q_num"]
        return ""

    def set_error_fields(self, fields):
        super(BasicJournalInformationRenderer, self).set_error_fields(fields)

        # find the first error in the form and tag it
        found = False
        for g in self.ERROR_CHECK_ORDER:
            cfg = self.FIELD_GROUPS.get(g)
            # If a group is specified as part of the error checks but is
            # not defined in self.FIELD_GROUPS then do not try to check
            # it for errors - there are no fields to check.
            if cfg:
                for obj in cfg:
                    field = obj.keys()[0]
                    if field in self.error_fields:
                        obj[field]["first_error"] = True
                        found = True
                        break
            if found:
                break


class ApplicationRenderer(BasicJournalInformationRenderer):
    def __init__(self):
        super(ApplicationRenderer, self).__init__()

        # allow the subclass to define the order the groups should be considered in.  This is useful for
        # numbering questions and determining first errors
        self.NUMBERING_ORDER.append("submitter_info")
        self.ERROR_CHECK_ORDER = deepcopy(self.NUMBERING_ORDER)  # in this case these can be the same

        self.FIELD_GROUPS["submitter_info"] = [
            {"suggester_name" : {}},
            {"suggester_email" : {"class": "input-xlarge"}},
            {"suggester_email_confirm" : {"class": "input-xlarge"}},
        ]

        self.insert_field_after(
            field_to_insert={"articles_last_year" : {"class": "input-mini"}},
            after_this_field="submission_charges_currency",
            field_group="basic_info"
        )
        self.insert_field_after(
            field_to_insert={"articles_last_year_url" : {"class": "input-xlarge"}},
            after_this_field="articles_last_year",
            field_group="basic_info"
        )
        self.insert_field_after(
            field_to_insert={"metadata_provision" : {}},
            after_this_field="article_identifiers",
            field_group="basic_info"
        )


class PublicApplicationRenderer(ApplicationRenderer):
    def __init__(self):
        super(PublicApplicationRenderer, self).__init__()

        # explicitly call number questions, as it is not called by default (because other implementations may want
        # to mess with the group order and field groups first)
        self.number_questions()

        self.check_field_groups()


class PublisherUpdateRequestRenderer(ApplicationRenderer):
    def __init__(self):
        super(PublisherUpdateRequestRenderer, self).__init__()

        self.NUMBERING_ORDER.remove("submitter_info")
        self.ERROR_CHECK_ORDER = deepcopy(self.NUMBERING_ORDER)
        del self.FIELD_GROUPS["submitter_info"]

        # explicitly call number questions, as it is not called by default (because other implementations may want
        # to mess with the group order and field groups first
        self.number_questions()

        self.check_field_groups()

        self._highlight_completable_fields = True


class PublisherUpdateRequestReadOnlyRenderer(ApplicationRenderer):
    def __init__(self):
        super(PublisherUpdateRequestReadOnlyRenderer, self).__init__()

        self.ERROR_CHECK_ORDER = []

        self.number_questions()

        self.check_field_groups()


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
        self.FIELD_GROUPS["seal"] = [
            {"doaj_seal" : {}}
        ]
        self.FIELD_GROUPS["continuations"] = [
            {"replaces" : {"class": "input-xlarge"}},
            {"is_replaced_by" : {"class": "input-xlarge"}},
            {"discontinued_date" : {}}
        ]

        self.ERROR_CHECK_ORDER = ["status", "account", "editorial", "continuations", "subject"] + self.ERROR_CHECK_ORDER + ["notes"]  # but do NOT include the new groups in self.NUMBERING_ORDER, don"t want them numbered

        self.number_questions()

        self.check_field_groups()

        self._highlight_completable_fields = True


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

        self.ERROR_CHECK_ORDER = ["status", "editorial", "subject"] + self.ERROR_CHECK_ORDER + ["notes"]
        # don"t want the extra groups numbered so not added to self.NUMBERING_ORDER

        self.number_questions()

        self.check_field_groups()

        self._highlight_completable_fields = True


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

        self.ERROR_CHECK_ORDER = ["status", "subject"] + self.ERROR_CHECK_ORDER + ["notes"]

        self.number_questions()

        self.check_field_groups()

        self._highlight_completable_fields = True


class JournalRenderer(BasicJournalInformationRenderer):
    def __init__(self):
        super(JournalRenderer, self).__init__()

        self.FIELD_GROUPS["subject"] = [
            {"subject" : {}}
        ]

        self.FIELD_GROUPS["old_journal_fields"] = [
            {"author_pays": {}},
            {"author_pays_url": {"class": "input-xlarge"}},
            {"oa_end_year": {"class": "input-mini"}},
        ]

    def render_field_group(self, form_context, field_group_name=None, **kwargs):
        if field_group_name == "old_journal_fields":
            display_old_journal_fields = False
            for old_field_def in self.FIELD_GROUPS["old_journal_fields"]:
                old_field_name = old_field_def.keys()[0]
                old_field = getattr(form_context.form, old_field_name)
                if old_field:
                    if old_field.data and old_field.data != 'None':
                        display_old_journal_fields = True

            if not display_old_journal_fields:
                return ""
            # otherwise let it fall through and render the old journal fields

        return super(JournalRenderer, self).render_field_group(form_context, field_group_name, **kwargs)


class ManEdJournalReviewRenderer(JournalRenderer):
    def __init__(self):
        super(ManEdJournalReviewRenderer, self).__init__()

        # extend the list of field groups
        self.FIELD_GROUPS["account"] = [
            {"owner" : {"class" : "input-large"}}
        ]

        self.FIELD_GROUPS["editorial"] = [
            {"editor_group" : {"class" : "input-large"}},
            {"editor" : {"class" : "input-large"}},
        ]
        self.FIELD_GROUPS["notes"] = [
            {
                "notes" : {
                    "render_subfields_horizontal" : True,
                    "container_class" : "deletable",
                    "subfield_display-note" : "8",
                    "subfield_display-date" : "3",
                    "label_width" : 1
                }
            }
        ]
        self.FIELD_GROUPS["make_all_fields_optional"] = [
            {"make_all_fields_optional": {}}
        ]
        self.FIELD_GROUPS["seal"] = [
            {"doaj_seal" : {}}
        ]
        self.FIELD_GROUPS["continuations"] = [
            {"replaces" : {"class": "input-xlarge"}},
            {"is_replaced_by" : {"class": "input-xlarge"}},
            {"discontinued_date" : {}}
        ]

        self.ERROR_CHECK_ORDER = ["make_all_fields_optional", "account", "editorial", "continuations", "subject"] + self.ERROR_CHECK_ORDER + ["notes"]

        self.number_questions()

        self.check_field_groups()

        self._highlight_completable_fields = True


class ManEdJournalBulkEditRenderer(Renderer):
    def __init__(self):
        super(ManEdJournalBulkEditRenderer, self).__init__()

        self.FIELD_GROUPS = {
            "main" : [
                {"publisher" : {"class": "input-xlarge"}},
                {"platform" : {"class": "input-xlarge"}},
                {"country" : {"class": "input-large"}},

                {"owner" : {"class" : "input-large"}},
                {"contact_name" : {"class" : "input-large"}},
                {"contact_email" : {"class" : "input-large"}},

                {"doaj_seal" : {"class" : "form-control input-large"}}
            ]
        }


class EditorJournalReviewRenderer(JournalRenderer):
    def __init__(self):
        self.display_old_journal_fields = False  # an instance var flag for the template

        super(EditorJournalReviewRenderer, self).__init__()

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

        self.ERROR_CHECK_ORDER = ["editorial", "subject"] + self.ERROR_CHECK_ORDER + ["notes"]

        # don't want the extra groups numbered so not added to self.NUMBERING_ORDER

        self.number_questions()

        self.check_field_groups()

        self._highlight_completable_fields = True


class AssEdJournalReviewRenderer(JournalRenderer):
    def __init__(self):
        super(AssEdJournalReviewRenderer, self).__init__()

        # extend the list of field groups
        self.FIELD_GROUPS["notes"] = [
            {
                "notes" : {
                    "render_subfields_horizontal" : True,
                    "subfield_display-note" : "8",
                    "subfield_display-date" : "3"
                }
            }
        ]

        self.ERROR_CHECK_ORDER = ["subject"] + self.ERROR_CHECK_ORDER + ["notes"]

        self.number_questions()

        self.check_field_groups()

        self._highlight_completable_fields = True


class ReadOnlyJournalRenderer(JournalRenderer):
    def __init__(self):
        super(ReadOnlyJournalRenderer, self).__init__()

        # extend the list of field groups
        self.FIELD_GROUPS["notes"] = [
            {
                "notes" : {
                    "render_subfields_horizontal" : True,
                    "subfield_display-note" : "8",
                    "subfield_display-date" : "3"
                }
            }
        ]

        self.ERROR_CHECK_ORDER = []

        self.number_questions()

        self.check_field_groups()
