from portality.formcontext.formhelper import FormHelper

class Renderer(object):
    FIELD_GROUPS = {}

    # FIXME: a bit implementation specific - could make static, or part of the init method
    fh = FormHelper()

    def render_field_group(self, form_context, field_group_name=None):
        if field_group_name is None:
            return self._render_all(form_context)

        # get the group definition
        group_def = self.FIELD_GROUPS.get(field_group_name)
        if group_def is None:
            return ""

        # build the frag
        frag = ""
        for field_name, config in group_def.iteritems():
            frag += self.fh.render_field(form_context, field_name, **config)

        return frag

    def _render_all(self, form_context):
        frag = ""
        for field in form_context.form:
            frag += self.fh.render_field(form_context, field.short_name)
        return frag

# FIXME: factor this out to choices.py
other_val = 'Other'
digital_archiving_policy_specific_library_value = 'A national library'

class SuggestionFormRenderer(Renderer):

    FIELD_GROUPS = {
        "basic_info" : {
            "title" : {"class" : "input-xlarge"},
            "url" : {"class" : "input-xlarge"},
            "digital_archiving_policy" : {
                "extra_input_fields" : [
                    {"field" : "digital_archiving_policy_other", "when_label_is" : other_val},
                    {"field" : "digital_archiving_policy_library", "when_label_is" : digital_archiving_policy_specific_library_value}
                ]
            }
        }
    }
    """
    basic_info_fields = [
        {"field": "title", "class": "input-xlarge"},
        {"field": "url", "class": "input-xlarge"},
        {"field": "alternative_title", "class": "input-xlarge"},
        {"field": "pissn", "class": "input-small", "size": "9", "maxlength": "9"},
        {"field": "eissn", "class": "input-small", "size": "9", "maxlength": "9"},
        {"field": "publisher", "class": "input-xlarge"},
        {"field": "society_institution", "class": "input-xlarge"},
        {"field": "platform", "class": "input-xlarge"},
        {"field": "contact_name", },
        {"field": "contact_email", },
        {"field": "confirm_contact_email", },
        {"field": "country", "class": "input-large"},
        {"field": "processing_charges", },
        {"field": "processing_charges_amount", "class": "input-mini"},
        {"field": "processing_charges_currency", "class": "input-large"},
        {"field": "submission_charges", },
        {"field": "submission_charges_amount", "class": "input-mini"},
        {"field": "submission_charges_currency", "class": "input-large"},
        {"field": "articles_last_year", "class": "input-mini"},
        {"field": "articles_last_year_url", "class": "input-xlarge"},
        {"field": "waiver_policy", },
        {"field": "waiver_policy_url", "class": "input-xlarge"},
        {
            "field": "digital_archiving_policy",
            "extra_input_field": form.digital_archiving_policy_other,
            "display_extra_when_label_is": other_val,
            "extra_input_field2": form.digital_archiving_policy_library,
            "display_extra2_when_label_is": digital_archiving_policy_specific_library_value,
        },
        {"field": "digital_archiving_policy_url", "class": "input-xlarge"},
        {"field": "crawl_permission", },
        {"field": "article_identifiers", "extra_input_field": form.article_identifiers_other, "display_extra_when_label_is": other_val},
        {"field": "metadata_provision", },
        {"field": "download_statistics", },
        {"field": "download_statistics_url", "class": "input-xlarge"},
        {"field": "first_fulltext_oa_year", "class": "input-mini"},
        {"field": "fulltext_format", "extra_input_field": form.fulltext_format_other, "display_extra_when_label_is": other_val},
        {"field": "keywords", "class": "input-xlarge"},
        {"field": "languages", "class": "input-xlarge"}
    ]

    editorial_process_fields = [
        {"field": "editorial_board_url", "class": "input-xlarge"},
        {"field": "review_process", },
        {"field": "review_process_url", "class": "input-xlarge"},
        {"field": "aims_scope_url", "class": "input-xlarge"},
        {"field": "instructions_authors_url", "class": "input-xlarge"},
        {"field": "plagiarism_screening", },
        {"field": "plagiarism_screening_url", "class": "input-xlarge"},
        {"field": "publication_time", "class": "input-tiny"},
    ]

    openness_fields = [
        {"field": "oa_statement_url", "class": "input-xlarge"},
    ]

    content_licensing_fields = [
      {"field": "license_embedded", },
      {"field": "license_embedded_url", "class": "input-xlarge"},
      {"field": "license", "extra_input_field": form.license_other, "display_extra_when_label_is": other_val},
      {"field": "license_checkbox", },
      {"field": "license_url", "class": "input-xlarge"},
      {"field": "open_access", },
      {"field": "deposit_policy", "extra_input_field": form.deposit_policy_other, "display_extra_when_label_is": other_val},
    ]

    copyright_fields = [
        {"field": "copyright", "extra_input_field": form.copyright_other, "display_extra_when_label_is": other_val},
        {"field": "copyright_url", "class": "input-xlarge"},
        {"field": "publishing_rights", "extra_input_field": form.publishing_rights_other, "display_extra_when_label_is": other_val},
        {"field": "publishing_rights_url", "class": "input-xlarge"},
    ]

    submitter_info_fields = [
        {"field": "suggester_name", },
        {"field": "suggester_email", "class": "input-xlarge"},
        {"field": "suggester_email_confirm", "class": "input-xlarge"},
    ]
    """
