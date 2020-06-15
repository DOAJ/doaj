from portality import models, lcc
from portality.datasets import licenses
from portality.formcontext.choices import Choices
from crosswalks.interpreting_methods import interpret_special, interpret_other, reverse_interpret_special, \
    reverse_interpret_other
from portality.util import listpop


class JournalGenericXWalk(object):
    @classmethod
    def is_new_editor_group(cls, form, old):
        old_eg = old.editor_group
        new_eg = form.editor_group.data
        return old_eg != new_eg and new_eg is not None and new_eg != ""

    @classmethod
    def is_new_editor(cls, form, old):
        old_ed = old.editor
        new_ed = form.editor.data
        return old_ed != new_ed and new_ed is not None and new_ed != ""

    @classmethod
    def form2bibjson(cls, form, bibjson):
        if form.alternative_title.data:
            bibjson.alternative_title = form.alternative_title.data

        for apc_record in form.apc_charges.data:
            if not apc_record["apc_currency"] and not apc_record["apc_max"]:
                continue
            bibjson.add_apc(apc_record["apc_currency"], apc_record["apc_max"])

        if form.apc_url.data:
            bibjson.apc_url = form.apc_url.data

        pres_services = []
        if len(form.preservation_service.data) > 0:
            pres_services = [e for e in form.preservation_service.data if
                             e not in ["national_library", "none", "other"]]
        if "other" in form.preservation_service.data and form.preservation_service_other.data:
            pres_services.append(form.preservation_service_other.data)
        bibjson.set_preservation(pres_services, form.preservation_service_url.data)
        if "national_library" in form.preservation_service.data and form.preservation_service_library.data:
            bibjson.add_preservation(libraries=form.preservation_service_library.data)

        if form.copyright_author_retains.data:
            bibjson.author_retains_copyright = form.copyright_author_retains.data

        if form.copyright_url.data:
            bibjson.copyright_url = form.copyright_url.data

        dep_services = []
        if len(form.deposit_policy.data) > 0:
            dep_services = [e for e in form.deposit_policy.data if e not in ["Unregistered", "none", "other"]]
        if "other" in form.deposit_policy.data and form.deposit_policy_other.data:
            dep_services.append(form.deposit_policy_other.data)
        if dep_services:
            bibjson.deposit_policy = dep_services
        if "Unregistered" in form.deposit_policy.data:
            bibjson.deposit_policy_registered = False
        elif len(dep_services) > 0:
            bibjson.deposit_policy_registered = True

        if form.review_process.data or form.review_process_url.data:
            processes = [e for e in form.review_process.data if e not in ["other"]]
            if "other" in form.review_process.data and form.review_process_other.data:
                processes.append(form.review_process_other.data)
            bibjson.set_editorial_review(processes, form.review_url.data, form.editorial_board_url.data)

        if form.pissn.data:
            bibjson.pissn = form.pissn.data

        if form.eissn.data:
            bibjson.eissn = form.eissn.data

        if "institution_name" in form.institution.data:
            bibjson.institution_name = form.institution.data["institution_name"]
        if "institution_country" in form.institution.data:
            bibjson.institution_country = form.institution.data["institution_country"]

        if form.keywords.data:
            bibjson.keywords = form.keywords.data

        if form.language.data:
            bibjson.language = form.language.data  # select multiple field - gives a list back

        lurl = form.license_terms_url.data
        if lurl:
            bibjson.license_terms_url = lurl
        for ltype in form.license.data:
            by, nc, nd, sa = None, None, None, None
            if ltype in licenses:
                by = licenses[ltype]['BY']
                nc = licenses[ltype]['NC']
                nd = licenses[ltype]['ND']
                sa = licenses[ltype]['SA']
                lurl = licenses[type]["url"]
            elif form.license_attributes.data:
                by = True if 'BY' in form.license_attributes.data else False
                nc = True if 'NC' in form.license_attributes.data else False
                nd = True if 'ND' in form.license_attributes.data else False
                sa = True if 'SA' in form.license_attributes.data else False
            bibjson.add_license(ltype, url=lurl, by=by, nc=nc, nd=nd, sa=sa)

        if form.license_display.data:
            bibjson.article_license_display = form.license_display.data

        if form.license_display_example_url.data:
            bibjson.article_license_display_example_url = form.license_display_example_url.data

        if form.boai.data:
            bibjson.boai = form.boai.data

        if form.oa_statement_url.data:
            bibjson.oa_statement_url = form.oa_statement_url.data

        if form.journal_url.data:
            bibjson.journal_url = form.journal_url.data

        if form.aims_scope_url.data:
            bibjson.aims_scope_url = form.aims_scope_url.data

        if form.author_instructions_url.data:
            bibjson.author_instructions_url = form.author_instructions_url.data

        if form.waiver_url.data:
            bibjson.waiver_url = form.waiver_url.data

        schemes = [e for e in form.persistent_identifiers.data if e not in ["none", "other"]]
        if "other" in form.persistent_identifiers.data and form.persistent_identifiers_other.data:
            schemes.append(form.persistent_identifiers_other.data)
        if len(schemes) > 0:
            bibjson.pid_scheme = schemes

        if form.plagiarism_detection.data:
            has_detection = form.plagiarism_detection.data == "y"
            bibjson.set_plagiarism_detection(form.plagiarism_url.data, has_detection)

        if form.publication_time_weeks.data:
            bibjson.publication_time_weeks = form.publication_time_weeks.data

        if "publisher_name" in form.publisher.data:
            bibjson.publisher_name = form.publisher.data["publisher_name"]
        if "publisher_country" in form.publisher.data:
            bibjson.publisher_country = form.publisher.data["publisher_country"]

        if form.other_charges_url.data:
            bibjson.other_charges_url = form.other_charges_url.data

        if form.title.data:
            bibjson.title = form.title.data

        if form.apc.data:
            has_apc = form.apc.data == "y"
            bibjson.has_apc = has_apc

        if form.has_other_charges.data:
            has_other = form.has_other_charges.data == "y"
            bibjson.has_other_charges = has_other

        if form.has_waiver.data:
            has_waiver = form.has_waiver.data == "y"
            bibjson.has_waiver = has_waiver

        if form.orcid_ids.data:
            orcids = form.orcid_ids.data == "y"
            bibjson.article_orcid = orcids

        if form.open_citations.data:
            oc = form.open_citations.data == "y"
            bibjson.article_i4oc_open_citations = oc

        if form.deposit_policy_url.data:
            bibjson.deposit_policy_url = form.deposit_policy_url.data


class JournalFormXWalk(JournalGenericXWalk):

    @classmethod
    def form2obj(cls, form):
        journal = models.Journal()
        bibjson = journal.bibjson()

        # first do the generic crosswalk to bibjson
        cls.form2bibjson(form, bibjson)

        ################################################

        # admin fields we haven't thought about yet

        """
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
        """

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