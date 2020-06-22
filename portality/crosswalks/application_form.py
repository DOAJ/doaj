from portality import models, lcc
from portality.datasets import licenses
from portality.util import listpop
from portality.formcontext.choices import Choices
from portality.crosswalks.journal_form import JournalGenericXWalk

class ApplicationFormXWalk(JournalGenericXWalk):

    _formFields2objectFields = {
        "instructions_authors_url" : "bibjson.link.url where bibjson.link.type=author_instructions",
        "oa_statement_url" : "bibjson.link.url where bibjson.link.type=oa_statement",
        "aims_scope_url" : "bibjson.link.url where bibjson.link.type=aims_scope",
        "submission_charges_url" : "bibjson.submission_charges_url",
        "editorial_board_url" : "bibjson.link.url where bibjson.link.type=editorial_board",
    }

    @classmethod
    def formField2objectField(cls, field):
        return cls._formFields2objectFields.get(field, field)

    @classmethod
    def form2obj(cls, form):
        application = models.Application()
        bibjson = application.bibjson()

        cls.form2bibjson(form, bibjson)

        # admin stuff
        if getattr(form, 'application_status', None):
            application.set_application_status(form.application_status.data)

        # FIXME: in the new version of the form, notes will have IDs, so we need to pick them up too
        if getattr(form, 'notes', None):
            for formnote in form.notes.data:
                if formnote["note"]:
                    application.add_note(formnote["note"])

        if getattr(form, 'subject', None):
            new_subjects = []
            for code in form.subject.data:
                sobj = {"scheme": 'LCC', "term": lcc.lookup_code(code), "code": code}
                new_subjects.append(sobj)
            bibjson.set_subjects(new_subjects)

        if getattr(form, 'owner', None):
            owns = form.owner.data
            if owns:
                owns = owns.strip()
                application.set_owner(owns)

        if getattr(form, 'editor_group', None):
            editor_group = form.editor_group.data
            if editor_group:
                editor_group = editor_group.strip()
                application.set_editor_group(editor_group)

        if getattr(form, "editor", None):
            editor = form.editor.data
            if editor:
                editor = editor.strip()
                application.set_editor(editor)

        if getattr(form, "doaj_seal", None):
            application.set_seal(form.doaj_seal.data)

        # continuations information
        if getattr(form, "replaces", None):
            bibjson.replaces = form.replaces.data
        if getattr(form, "is_replaced_by", None):
            bibjson.is_replaced_by = form.is_replaced_by.data
        if getattr(form, "discontinued_date", None):
            bibjson.discontinued_date = form.discontinued_date.data

        return application

    @classmethod
    def obj2form(cls, obj):
        forminfo = {}
        bibjson = obj.bibjson()

        cls.bibjson2form(bibjson, forminfo)

        return forminfo
"""
        from portality.formcontext.form_definitions import application_form as ApplicationFormFactory

        forminfo = {}
        bibjson = obj.bibjson()

        forminfo["boai"] = bibjson.boai
        forminfo["oa_statement_url"] = bibjson.oa_statement_url
        forminfo["country"] = bibjson.publisher_country
        forminfo["keywords"] = bibjson.keywords
        forminfo["licensing"] = [l.get("type") for l in bibjson.licenses]
        forminfo["submission_time"] = bibjson.publication_time_weeks
        forminfo["peer_review"] = [p for p in bibjson.editorial_review_process if p in [c[0] for c in ApplicationFormFactory.choices_for("peer_review")]]

        others = [p for p in bibjson.editorial_review_process if
                    p not in [c[0] for c in ApplicationFormFactory.choices_for("peer_review")]]
        if len(others) > 0:
            forminfo["peer_review_other"] = others[0]

        return forminfo

        forminfo['title'] = bibjson.title
        forminfo['url'] = bibjson.get_single_url(urltype='homepage')
        forminfo['alternative_title'] = bibjson.alternative_title
        forminfo['pissn'] = listpop(bibjson.get_identifiers(idtype=bibjson.P_ISSN))
        forminfo['eissn'] = listpop(bibjson.get_identifiers(idtype=bibjson.E_ISSN))
        forminfo['publisher'] = bibjson.publisher
        forminfo['society_institution'] = bibjson.institution
        forminfo['platform'] = bibjson.provider
        forminfo['contact_name'] = listpop(obj.contacts(), {}).get('name')
        forminfo['contact_email'] = listpop(obj.contacts(), {}).get('email')
        forminfo['confirm_contact_email'] = forminfo['contact_email']
        forminfo['country'] = bibjson.country
        forminfo["replaces"] = bibjson.replaces
        forminfo["is_replaced_by"] = bibjson.is_replaced_by
        forminfo["discontinued_date"] = bibjson.discontinued_date

        apc = bibjson.apc
        if apc:
            forminfo['processing_charges'] = reverse_interpret_special(True)
            forminfo['processing_charges_currency'] = apc.get('currency')
            forminfo['processing_charges_amount'] = apc.get('average_price')
        else:
            forminfo['processing_charges'] = reverse_interpret_special(False)

        forminfo['processing_charges_url'] = bibjson.apc_url

        submission_charges = bibjson.submission_charges
        if submission_charges:
            forminfo['submission_charges'] = reverse_interpret_special(True)
            forminfo['submission_charges_currency'] = submission_charges.get('currency')
            forminfo['submission_charges_amount'] = submission_charges.get('average_price')
        else:
            forminfo['submission_charges'] = reverse_interpret_special(False)

        forminfo['submission_charges_url'] = bibjson.submission_charges_url

        articles_last_year = obj.articles_last_year
        if articles_last_year:
            forminfo['articles_last_year'] = articles_last_year.get('count')
            forminfo['articles_last_year_url'] = articles_last_year.get('url')

        forminfo['waiver_policy_url'] = bibjson.get_single_url(urltype='waiver_policy')
        forminfo['waiver_policy'] = reverse_interpret_special(forminfo['waiver_policy_url'] is not None and forminfo['waiver_policy_url'] != '')


        #archiving_policies = reverse_interpret_special(bibjson.archiving_policy.get('policy', []), field='digital_archiving_policy')
        #substitutions = [
        #    {"default": Choices.digital_archiving_policy_val("library"), "field" : "digital_archiving_policy_library" },
        #    {"default": Choices.digital_archiving_policy_val("other"), "field" : "digital_archiving_policy_other"}
        #]
        #archiving_policies, special_fields = interpret_list(
        #    archiving_policies, # current values
        #    Choices.digital_archiving_policy_list(), # allowed values
        #    substitutions # substitution instructions
        #)
        #forminfo.update(special_fields)

        # checkboxes
        archiving_policies = reverse_interpret_special(bibjson.archiving_policy.get('policy', []), field='digital_archiving_policy')

        # for backwards compatibility we keep the "Other" field first in the reverse xwalk
        # previously we didn't store which free text value was which (Other, or specific national library)
        # so in those cases, just put it in "Other", it'll be correct most of the time
        archiving_policies, forminfo['digital_archiving_policy_other'] = \
            reverse_interpret_other(archiving_policies, Choices.digital_archiving_policy_list())

        archiving_policies, forminfo['digital_archiving_policy_library'] = \
            reverse_interpret_other(
                archiving_policies,
                Choices.digital_archiving_policy_list(),
                other_value=Choices.digital_archiving_policy_val("library"),
                replace_label=Choices.digital_archiving_policy_label("library")
            )

        forminfo['digital_archiving_policy'] = archiving_policies
        forminfo['digital_archiving_policy_url'] = bibjson.archiving_policy.get('url')

        forminfo['crawl_permission'] = reverse_interpret_special(bibjson.allows_fulltext_indexing)

        # checkboxes
        article_ids = reverse_interpret_special(bibjson.persistent_identifier_scheme)
        article_ids, forminfo['article_identifiers_other'] = \
            reverse_interpret_other(article_ids, Choices.article_identifiers_list())

        forminfo['article_identifiers'] = article_ids

        forminfo['metadata_provision'] = reverse_interpret_special(obj.article_metadata)

        forminfo['download_statistics'] = reverse_interpret_special(bibjson.article_statistics.get('statistics'))
        forminfo['download_statistics_url'] = bibjson.article_statistics.get('url')

        forminfo['first_fulltext_oa_year'] = bibjson.oa_start.get('year')

        # checkboxes
        forminfo['fulltext_format'], forminfo['fulltext_format_other'] = \
            reverse_interpret_other(bibjson.format, Choices.fulltext_format_list())

        forminfo['keywords'] = bibjson.keywords

        forminfo['languages'] = bibjson.language

        forminfo['editorial_board_url'] = bibjson.get_single_url('editorial_board')

        forminfo['review_process'] = bibjson.editorial_review.get('process')
        forminfo['review_process_url'] = bibjson.editorial_review.get('url')

        forminfo['aims_scope_url'] = bibjson.get_single_url('aims_scope')
        forminfo['instructions_authors_url'] = bibjson.get_single_url('author_instructions')

        forminfo['plagiarism_screening'] = reverse_interpret_special(bibjson.plagiarism_detection.get('detection'))
        forminfo['plagiarism_screening_url'] = bibjson.plagiarism_detection.get('url')

        forminfo['publication_time'] = bibjson.publication_time

        forminfo['oa_statement_url'] = bibjson.get_single_url('oa_statement')

        license = bibjson.get_license()
        license = license if license else {}  # reinterpret the None val
        forminfo['license'], forminfo['license_other'] = reverse_interpret_other(license.get('type'), Choices.licence_list())

        if forminfo['license_other']:
            forminfo['license_checkbox'] = []
            if license.get('BY'): forminfo['license_checkbox'].append('BY')
            if license.get('SA'): forminfo['license_checkbox'].append('SA')
            if license.get('NC'): forminfo['license_checkbox'].append('NC')
            if license.get('ND'): forminfo['license_checkbox'].append('ND')

        forminfo['license_url'] = license.get('url')
        forminfo['open_access'] = reverse_interpret_special(license.get('open_access'))
        forminfo['license_embedded'] = reverse_interpret_special(license.get('embedded'))
        forminfo['license_embedded_url'] = license.get('embedded_example_url')

        # checkboxes
        forminfo['deposit_policy'], forminfo['deposit_policy_other'] = \
            reverse_interpret_other(reverse_interpret_special(bibjson.deposit_policy), Choices.deposit_policy_list())

        forminfo['copyright'] = reverse_interpret_special(bibjson.author_copyright.get('copyright', ''))
        forminfo['copyright_url'] = bibjson.author_copyright.get('url')

        forminfo['publishing_rights'] = reverse_interpret_special(bibjson.author_publishing_rights.get('publishing_rights', ''))
        forminfo['publishing_rights_url'] = bibjson.author_publishing_rights.get('url')

        forminfo['suggester_name'] = obj.suggester.get('name')
        forminfo['suggester_email'] = obj.suggester.get('email')
        forminfo['suggester_email_confirm'] = forminfo['suggester_email']

        forminfo['application_status'] = obj.application_status

        forminfo['notes'] = obj.ordered_notes

        forminfo['subject'] = []
        for s in bibjson.subjects():
            if "code" in s:
                forminfo['subject'].append(s['code'])

        forminfo['owner'] = obj.owner
        if obj.editor_group is not None:
            forminfo['editor_group'] = obj.editor_group
        if obj.editor is not None:
            forminfo['editor'] = obj.editor

        forminfo['doaj_seal'] = obj.has_seal()

        return forminfo
        """
