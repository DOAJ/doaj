from portality import models, lcc
from portality.datasets import licenses
from portality.formcontext.choices import Choices
from portality.formcontext.xwalks.interpreting_methods import interpret_special, interpret_other, reverse_interpret_special, \
    reverse_interpret_other
from portality.formcontext.xwalks.journal_generic import JournalGenericXWalk
from portality.util import listpop


class JournalFormXWalk(JournalGenericXWalk):

    @classmethod
    def form2obj(cls, form):
        journal = models.Journal()
        bibjson = journal.bibjson()

        # The if statements that wrap practically every field are there due to this
        # form being used to edit old journals which don't necessarily have most of
        # this info.
        # It also allows admins to delete the contents of any field if they wish,
        # by ticking the "Allow incomplete form" checkbox and deleting the contents
        # of that field. The if condition(s) will then *not* add the relevant field to the
        # new journal object being constructed.
        # add_url in the journal model has a safeguard against empty URL-s.

        if form.title.data:
            bibjson.title = form.title.data
        bibjson.add_url(form.url.data, urltype='homepage')
        if form.alternative_title.data:
            bibjson.alternative_title = form.alternative_title.data
        if form.pissn.data:
            bibjson.add_identifier(bibjson.P_ISSN, form.pissn.data)
        if form.eissn.data:
            bibjson.add_identifier(bibjson.E_ISSN, form.eissn.data)
        if form.publisher.data:
            bibjson.publisher = form.publisher.data
        if form.society_institution.data:
            bibjson.institution = form.society_institution.data
        if form.platform.data:
            bibjson.provider = form.platform.data
        if form.contact_name.data or form.contact_email.data:
            journal.add_contact(form.contact_name.data, form.contact_email.data)
        if form.country.data:
            bibjson.country = form.country.data

        if interpret_special(form.processing_charges.data):
            bibjson.set_apc(form.processing_charges_currency.data, form.processing_charges_amount.data)

        if form.processing_charges_url.data:
            bibjson.apc_url = form.processing_charges_url.data

        if interpret_special(form.submission_charges.data):
            bibjson.set_submission_charges(form.submission_charges_currency.data, form.submission_charges_amount.data)

        if form.submission_charges_url.data:
            bibjson.submission_charges_url = form.submission_charges_url.data

        if interpret_special(form.waiver_policy.data):
            bibjson.add_url(form.waiver_policy_url.data, 'waiver_policy')

        # checkboxes
        if interpret_special(form.digital_archiving_policy.data) or form.digital_archiving_policy_url.data:
            archiving_policies = interpret_special(form.digital_archiving_policy.data)
            archiving_policies = interpret_other(archiving_policies, form.digital_archiving_policy_other.data, store_other_label=True)
            archiving_policies = interpret_other(archiving_policies, form.digital_archiving_policy_library.data, Choices.digital_archiving_policy_val("library"), store_other_label=True)
            bibjson.set_archiving_policy(archiving_policies, form.digital_archiving_policy_url.data)

        if form.crawl_permission.data and form.crawl_permission.data != 'None':
            bibjson.allows_fulltext_indexing = interpret_special(form.crawl_permission.data)  # just binary

        # checkboxes
        article_ids = interpret_special(form.article_identifiers.data)
        article_ids = interpret_other(article_ids, form.article_identifiers_other.data)
        if article_ids:
            bibjson.persistent_identifier_scheme = article_ids

        if (form.download_statistics.data and form.download_statistics.data != 'None') or form.download_statistics_url.data:
            bibjson.set_article_statistics(form.download_statistics_url.data, interpret_special(form.download_statistics.data))

        if form.first_fulltext_oa_year.data:
            bibjson.set_oa_start(year=form.first_fulltext_oa_year.data)

        # checkboxes
        fulltext_format = interpret_other(form.fulltext_format.data, form.fulltext_format_other.data)
        if fulltext_format:
            bibjson.format = fulltext_format

        if form.keywords.data:
            bibjson.set_keywords(form.keywords.data)  # tag list field

        if form.languages.data:
            bibjson.set_language(form.languages.data)  # select multiple field - gives a list back

        bibjson.add_url(form.editorial_board_url.data, urltype='editorial_board')

        if form.review_process.data or form.review_process_url.data:
            bibjson.set_editorial_review(form.review_process.data, form.review_process_url.data)

        bibjson.add_url(form.aims_scope_url.data, urltype='aims_scope')
        bibjson.add_url(form.instructions_authors_url.data, urltype='author_instructions')

        if (form.plagiarism_screening.data and form.plagiarism_screening.data != 'None') or form.plagiarism_screening_url.data:
            bibjson.set_plagiarism_detection(
                form.plagiarism_screening_url.data,
                has_detection=interpret_special(form.plagiarism_screening.data)
            )

        if form.publication_time.data:
            bibjson.publication_time = form.publication_time.data

        bibjson.add_url(form.oa_statement_url.data, urltype='oa_statement')

        license_type = interpret_other(form.license.data, form.license_other.data)
        if interpret_special(license_type):
        # "None" and "False" as strings like they come out of the WTForms processing)
        # would get interpreted correctly by this check, so "None" licenses should not appear
            if license_type in licenses:
                by = licenses[license_type]['BY']
                nc = licenses[license_type]['NC']
                nd = licenses[license_type]['ND']
                sa = licenses[license_type]['SA']
                license_title = licenses[license_type]['title']
            elif form.license_checkbox.data:
                by = True if 'BY' in form.license_checkbox.data else False
                nc = True if 'NC' in form.license_checkbox.data else False
                nd = True if 'ND' in form.license_checkbox.data else False
                sa = True if 'SA' in form.license_checkbox.data else False
                license_title = license_type
            else:
                by = None; nc = None; nd = None; sa = None;
                license_title = license_type

            bibjson.set_license(
                license_title,
                license_type,
                url=form.license_url.data,
                open_access=interpret_special(form.open_access.data),
                by=by, nc=nc, nd=nd, sa=sa,
                embedded=interpret_special(form.license_embedded.data),
                embedded_example_url=form.license_embedded_url.data
            )

        # checkboxes
        deposit_policies = interpret_special(form.deposit_policy.data)  # need empty list if it's just "None"
        deposit_policies = interpret_other(deposit_policies, form.deposit_policy_other.data)
        if deposit_policies:
            bibjson.deposit_policy = deposit_policies

        if form.copyright.data and form.copyright.data != 'None':
            holds_copyright = interpret_special(form.copyright.data)
            bibjson.set_author_copyright(form.copyright_url.data, holds_copyright=holds_copyright)

        if form.publishing_rights.data and form.publishing_rights.data != 'None':
            publishing_rights = interpret_special(form.publishing_rights.data)
            bibjson.set_author_publishing_rights(form.publishing_rights_url.data, holds_rights=publishing_rights)

        for formnote in form.notes.data:
            if formnote["note"]:
                journal.add_note(formnote["note"])

        new_subjects = []
        for code in form.subject.data:
            sobj = {"scheme": 'LCC', "term": lcc.lookup_code(code), "code": code}
            new_subjects.append(sobj)
        bibjson.set_subjects(new_subjects)

        if getattr(form, 'owner', None):
            owner = form.owner.data
            if owner:
                owner = owner.strip()
                journal.set_owner(owner)

        if getattr(form, 'editor_group', None):
            editor_group = form.editor_group.data
            if editor_group:
                editor_group = editor_group.strip()
                journal.set_editor_group(editor_group)

        if getattr(form, "editor", None):
            editor = form.editor.data
            if editor:
                editor = editor.strip()
                journal.set_editor(editor)

        if getattr(form, "doaj_seal", None):
            journal.set_seal(form.doaj_seal.data)

        # continuations information
        if getattr(form, "replaces", None):
            bibjson.replaces = form.replaces.data
        if getattr(form, "is_replaced_by", None):
            bibjson.is_replaced_by = form.is_replaced_by.data
        if getattr(form, "discontinued_date", None):
            bibjson.discontinued_date = form.discontinued_date.data

        # old fields - only create them in the journal record if the values actually exist
        # need to use interpret_special in the test condition in case 'None' comes back from the form
        if getattr(form, 'author_pays', None):
            if interpret_special(form.author_pays.data):
                bibjson.author_pays = form.author_pays.data
        if getattr(form, 'author_pays_url', None):
            if interpret_special(form.author_pays_url.data):
                bibjson.author_pays_url = form.author_pays_url.data
        if getattr(form, 'oa_end_year', None):
            if interpret_special(form.oa_end_year.data):
                bibjson.set_oa_end(form.oa_end_year.data)

        return journal


    @classmethod
    def obj2form(cls, obj):
        forminfo = {}
        bibjson = obj.bibjson()

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

        forminfo['download_statistics'] = reverse_interpret_special(bibjson.article_statistics.get('statistics'))
        forminfo['download_statistics_url'] = bibjson.article_statistics.get('url')

        forminfo['first_fulltext_oa_year'] = bibjson.oa_start.get('year')

        # checkboxes
        forminfo['fulltext_format'], forminfo['fulltext_format_other'] = \
            reverse_interpret_other(bibjson.format, Choices.fulltext_format_list())

        forminfo['keywords'] = bibjson.keywords

        forminfo['languages'] = bibjson.language

        forminfo['editorial_board_url'] = bibjson.get_single_url('editorial_board')

        forminfo['review_process'] = bibjson.editorial_review.get('process', '')
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

        # old fields - only show them if the values actually exist in the journal record
        if bibjson.author_pays:
            forminfo['author_pays'] = bibjson.author_pays
        if bibjson.author_pays_url:
            forminfo['author_pays_url'] = bibjson.author_pays_url
        if bibjson.oa_end:
            forminfo['oa_end_year'] = bibjson.oa_end.get('year')

        return forminfo