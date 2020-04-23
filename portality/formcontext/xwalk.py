from portality import models, lcc
from portality.datasets import licenses
from portality.util import listpop
from copy import deepcopy
from portality.formcontext.choices import Choices

def interpret_list(current_values, allowed_values, substitutions):
    current_values = deepcopy(current_values)
    interpreted_fields = {}

    foreign_values = {}
    for cv in current_values:
        if cv not in allowed_values:
            foreign_values[current_values.index(cv)] = cv
    ps = list(foreign_values.keys())
    ps.sort()

    # FIXME: if the data is broken, just return it as is
    if len(ps) > len(substitutions):
        return current_values

    i = 0
    for k in ps:
        interpreted_fields[substitutions[i].get("field")] = current_values[k]
        current_values[k] = substitutions[i].get("default")
        i += 1

    return current_values, interpreted_fields


def interpret_special(val):
    # if you modify this, make sure to modify reverse_interpret_special as well
    if isinstance(val, str):
        if val.lower() == Choices.TRUE.lower():
            return True
        elif val.lower() == Choices.FALSE.lower():
            return False
        elif val.lower() == Choices.NONE.lower():
            return None
        elif val == Choices.digital_archiving_policy_val("none"):
            return None

    if isinstance(val, list):
        if len(val) == 1:
            actual_val = interpret_special(val[0])
            if not actual_val:
                return []
            return val

        return val

    return val

def reverse_interpret_special(val, field=''):
    # if you modify this, make sure to modify interpret_special as well

    if val is None:
        return Choices.NONE
    elif val is True:
        return Choices.TRUE
    elif val is False:
        return Choices.FALSE
    # no need to handle digital archiving policy or other list
    # fields here - empty lists handled below

    if isinstance(val, list):
        if len(val) == 1:
            reverse_actual_val = reverse_interpret_special(val[0], field=field)
            return [reverse_actual_val]
        elif len(val) == 0:
            # mostly it'll just be a None val
            if field == 'digital_archiving_policy':
                return [Choices.digital_archiving_policy_val("none")]

            return [Choices.NONE]

        return val

    return val


def interpret_other(value, other_field_data, other_value=Choices.OTHER, store_other_label=False):
    '''
    Interpret a value list coming from (e.g.) checkboxes when one of
    them says "Other" and allows free-text input.

    The value can also be a string. In that case, if it matched other_value, other_field_data is returned
    instead of the original value. This is for radio buttons with an "Other" option - you only get 1 value
    from the form, but if it's "Other", you still need to replace it with the relevant free text field data.

    :param value: String or list of values from the form.
        checkboxes_field.data basically.
    :param other_field_data: data from the Other inline extra text input field.
        Usually checkboxes_field_other.data or similar.
    :param other_value: Which checkbox has an extra field? Put its value in here. It's "Other" by default.
        More technically: the value which triggers considering and adding the data in other_field to value.
    '''
    # if you modify this, make sure to modify reverse_interpret_other too
    if isinstance(value, str):
        if value == other_value:
            return other_field_data
    elif isinstance(value, list):
        value = value[:]
        # if "Other" (or some custom value) is in the there, remove it and take the data from the extra text field
        if other_value in value and other_field_data:
            # preserve the order, important for reversing this process when displaying the edit form
            where = value.index(other_value)
            if store_other_label:
                # Needed when multiple items in the list could be freely specified,
                # i.e. unrestricted by the choices for that field.
                # Digital archiving policies is such a field, with both an
                # "Other" choice requiring free text input and a "A national library"
                # choice requiring free text input, presumably with the name
                # of the library.
                value[where] = [other_value, other_field_data]
            else:
                value[where] = other_field_data
    # don't know what else to do, just return it as-is
    return value


def reverse_interpret_other(interpreted_value, possible_original_values, other_value=Choices.OTHER, replace_label=Choices.OTHER):
    '''
    Returns tuple: (main field value or list of values, other field value)
    '''
    # if you modify this, make sure to modify interpret_other too
    other_field_val = ''

    if isinstance(interpreted_value, str):
        # A special case first: where the value is the empty string.
        # In that case, the main field was never submitted (e.g. if it was
        # a choice of "Yes", "No" and "Other", none of those were submitted
        # as an answer - maybe it was an optional field).
        if not interpreted_value:
            return None, None

        # if the stored (a.k.a. interpreted) value is not one of the
        # possible values, then the "Other" option must have been
        # selected during initial submission
        # if so, all we've got to do is swap them
        # so the main field gets a value of "Other" or similar
        # and the secondary (a.k.a. other) field gets the currently
        # stored value - resulting in a form that looks exactly like the
        # one initially submitted
        if interpreted_value not in possible_original_values:
            return other_value, interpreted_value

    elif isinstance(interpreted_value, list):
        # 2 copies of the list needed
        interpreted_value = interpreted_value[:]  # don't modify the original list passed in
        for iv in interpreted_value[:]:  # don't modify the list while iterating over it

            # same deal here, if the original list was ['LOCKSS', 'Other']
            # and the secondary field was 'some other policy'
            # then it would have been interpreted by interpret_other
            # into ['LOCKSS', 'some other policy']
            # so now we need to turn that back into
            # (['LOCKSS', 'Other'], 'some other policy')
            if iv not in possible_original_values:
                where = interpreted_value.index(iv)

                if isinstance(iv, list):
                    # This is a field with two or more choices which require
                    # further specification via free text entry.
                    # If we only recorded the free text values, we wouldn't
                    # be able to tell which one relates to which choice.
                    # E.g. ["some other archiving policy", "Library of Chile"]
                    # does not tell us that "some other archiving policy"
                    # is related to the "Other" field, and "Library of Chile"
                    # is related to the "A national library field.
                    #
                    # [["Other", "some other archiving policy"], ["A national library", "Library of Chile"]]
                    # does tell us that, on the other hand.
                    # It is this case that we are dealing with here.
                    label = iv[0]
                    val = iv[1]
                    if label == replace_label:
                        other_field_val = val
                        interpreted_value[where] = label
                    else:
                        continue
                else:
                    other_field_val = iv
                    interpreted_value[where] = other_value
                    break

    return interpreted_value, other_field_val


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

class SuggestionFormXWalk(JournalGenericXWalk):

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

        #this is done for new version of public application form

        suggestion = models.Suggestion()
        bibjson = suggestion.bibjson()

        # The if statements that wrap practically every field are there due to this
        # form being used to edit old journals which don't necessarily have most of
        # this info.
        # It also allows admins to delete the contents of any field if they wish,
        # by ticking the "Allow incomplete form" checkbox and deleting the contents
        # of that field. The if condition(s) will then *not* add the relevant field to the
        # new journal object being constructed.
        # add_url in the journal model has a safeguard against empty URL-s.

        if form.alternative_title.data and form.alternative_title.data != '':
            bibjson.alternative_title = form.alternative_title.data

        if form.processing_charges_amount.data and form.processing_charges_amount.data != '':
            bibjson.add_apc(form.processing_charges_currency.data, form.processing_charges_amount.data)

        if form.processing_charges_url.data and form.processing_charges_url.data != '':
            bibjson.apc_url = form.processing_charges_url.data

        if form.other_charges_url.data and form.other_charges_url.data != '':
            bibjson.other_charges_url = form.other_charges_url.data


        services = form.preservation_services.data if form.preservation_services.data else None
        library = form.preservation_library.data if form.preservation_library.data else None
        bibjson.add_preservation(services, library)

        if form.preservation_url.data and form.preservation_url.data != '':
            bibjson.preservation_url = form.preservation_url.data

        if form.copyright_url.data and form.copyright_url.data != '':
            bibjson.copyright_url = form.copyright_url.data

        if form.country.data and form.country.data != '':
            bibjson.country = form.country.data

        if form.deposit_policy_service.data and form.deposit_policy_service.data != '':
            services = form.deposit_policy_service.split(',')
            for s in services:
                bibjson.add_deposit_policy(s)

        if form.deposit_policy_is_registered.data and form.deposit_policy_is_registered.data != '':
            bibjson.deposit_policy_registered = form.deposit_policy_is_registered.data

        if form.deposit_policy_url.data and form.deposit_policy_url.data != '':
            bibjson.deposit_policy_url = form.deposit_policy_url.data

        if form.review_process.data and form.review_process.data != '':
            bibjson.review_process = form.review_process.data

        if form.review_process_url.data and form.review_process_url.data != '':
            bibjson.review_process_url = form.review_process_url.data

        if form.pissn.data and form.pissn.data != '':
            bibjson.add_identifier(bibjson.P_ISSN, form.pissn.data)

        if form.eissn.data and form.eissn.data != '':
            bibjson.add_identifier(bibjson.E_ISSN, form.eissn.data)

        if form.society_institution.data and form.society_institution.data != '':
            bibjson.institution = form.society_institution.data

        if form.keywords.data and form.keywords.data != '':
            bibjson.set_keywords(form.keywords.data)  # tag list field

        if form.languages.data and form.languages.data != '':
            bibjson.set_language(form.languages.data)  # select multiple field - gives a list back

        if form.license_checkbox.data and form.license_checkbox.data != '':
            by = True if 'BY' in form.license_checkbox.data else False
            nc = True if 'NC' in form.license_checkbox.data else False
            nd = True if 'ND' in form.license_checkbox.data else False
            sa = True if 'SA' in form.license_checkbox.data else False
        else:
            by = None
            nc = None
            nd = None
            sa = None

        license_type = form.license_type.data if form.license_type.data else None
        license_url = form.license_url.data if form.license_url.data else None

        bibjson.add_licence(
            license_type,
            url=license_url,
            by=by, nc=nc, nd=nd, sa=sa,
        )

        if form.license_display.data and form.license_display.data != '':
            bibjson.add_article_license_display(form.license_display.data)
        if form.license_display_example_url.data and form.license_display_example_url.data != '':
            bibjson.article_license_display_example_url = form.license_display_example_url.data

        if form.boai.data and form.boai.data != '':
            bibjson.boai = form.boai.data

        if form.oa_statement_url.data and form.oa_statement_url.data != '':
            bibjson.add_url(form.url.data, urltype='oa_statement')

        if form.url.data and form.url.data != '':
            bibjson.add_url(form.url.data, urltype='homepage')

        if form.aims_scope_url and form.aims_scope_url != '':
            bibjson.add_url(form.url.data, urltype='aims_scope')

        if form.editorial_board_url.data and form.editorial_board_url.data != '':
            bibjson.add_url(form.url.data, urltype='editorial_board')

        if form.author_instructions_url.data and form.author_instructions_url.data != '':
            bibjson.add_url(form.url.data, urltype='author_instructions')

        if form.waiver_policy_url.data and form.waiver_policy_url.data != '':
            bibjson.add_url(form.url.data, urltype='waiver_policy')

        if form.pid_scheme.data and form.pid_scheme.data != '':
            bibjson.add_pid_scheme(form.pid_scheme.data)

        if form.plagiarism_screening_url.data and form.plagiarism_screening_url.data != '':
            bibjson.set_plagiarism_detection(form.plagiarism_screening_url.data)

        if form.publication_time.data and form.publication_time.data != '':
            bibjson.publication_time_weeks = form.publication_time.data

        if form.publisher.data and form.publisher.data != '':
            bibjson.publisher = form.publisher.data

        if form.title.data and form.title.data != '':
            bibjson.title = form.title.data

        if form.processing_charges_url.data and form.processing_charges_url.data != '':
            bibjson.apc_url = form.processing_charges_url.data

        if form.article_orcid.data and form.article_orcid.data != '':
            bibjson.article_orcid = form.article_orcid.data

        if form.article_i4oc_open_citations.data and form.article_i4oc_open_citations.data != '':
            bibjson.article_i4oc_open_citations = form.article_i4oc_open_citations.data

        if form.contact_name.data and form.contact_email.data != '':
            suggestion.add_contact(form.contact_name.data, form.contact_email.data)

        return suggestion


    @classmethod
    def obj2form(cls, obj):
        forminfo = {}
        bibjson = obj.bibjson()

        forminfo['alternative_title'] = bibjson.alternative_title
        apc = bibjson.apc
        if apc:
            forminfo['processing_charges_currency'] = apc[0].get('currency')
            forminfo['processing_charges_amount'] = apc[0].get('price')

        forminfo['processing_charges_url'] = bibjson.apc_url

        forminfo['preservation_services'] = bibjson.preservation_services
        forminfo['preservation_url'] = bibjson.preservation_url
        forminfo['preservation_library'] = bibjson.preservation_library

        forminfo['copyright_url'] = bibjson.copyright_url

        forminfo['country'] = bibjson.country

        forminfo['deposit_policy'] = bibjson.deposit_policy
        forminfo['deposit_policy_is_registered'] = bibjson.deposit_policy_registered
        forminfo['deposit_policy_url'] = bibjson.deposit_policy_url

        forminfo['review_process'] = bibjson.editorial_review_process
        forminfo['review_process_url'] = bibjson.editorial_review_url

        forminfo['pissn'] = listpop(bibjson.get_identifiers(idtype=bibjson.P_ISSN))
        forminfo['eissn'] = listpop(bibjson.get_identifiers(idtype=bibjson.E_ISSN))

        forminfo['society_institution'] = bibjson.institution

        forminfo['keywords'] = bibjson.keywords

        forminfo['languages'] = bibjson.language

        license = bibjson.licenses[0]

        if license.get('BY'): reverse_interpret_special("by", True)
        if license.get('SA'): reverse_interpret_special("sa", True)
        if license.get('NC'): reverse_interpret_special("nc", True)
        if license.get('ND'): reverse_interpret_special("nd", True)

        forminfo["license_type"] = license.get('type')
        forminfo['license_url'] = license.get('url')

        forminfo["license_display"] =  bibjson.article_license_display
        forminfo["license_display_example_url"] = bibjson.article_license_display_example_url

        forminfo["boai"] = bibjson.boai

        forminfo["oa_statement_url"] = bibjson.get_single_url(urltype="oa_statement")
        forminfo['url'] = bibjson.get_single_url(urltype="homepage")
        forminfo['aims_scope_url'] = bibjson.get_single_url(urltype="aims_scope")
        forminfo['editorial_board_url'] = bibjson.get_single_url(urltype="editorial_board")
        forminfo['author_instructions_url'] = bibjson.get_single_url(urltype="author_instructions")
        forminfo['waiver_policy_url'] = bibjson.get_single_url(urltype="waiver_policy")

        forminfo['pid_scheme'] = bibjson.pid_scheme

        forminfo['plagiarism_screening_url'] = bibjson.plagiarism_url

        forminfo['publication_time'] = bibjson.publication_time_weeks

        forminfo['publisher'] = bibjson.publisher_name

        forminfo['title'] = bibjson.title

        forminfo["article_orcid"] = bibjson.article_orcid

        forminfo["article_i4oc_open_citations"] = bibjson.article_i4oc_open_citations

        forminfo['contact_name'] = obj.data["admin"]["contact"]["name"]
        forminfo['contact_email'] = obj.data["admin"]["contact"]["email"]
        forminfo['confirm_contact_email'] = forminfo['contact_email']

        forminfo['applicant_name'] = obj.data["admin"]["applicant"]["name"]
        forminfo['applicant_email'] = obj.data["admin"]["applicant"]["email"]
        forminfo['applicant_email_confirm'] = forminfo['applicant_email']


        #non-public form

        #
        # forminfo["replaces"] = bibjson.replaces
        # forminfo["is_replaced_by"] = bibjson.is_replaced_by
        # forminfo['application_status'] = obj.data["admin"]["application_status"]
        #
        # forminfo['notes'] = obj.ordered_notes
        #
        # forminfo['subject'] = bibjson.subjects
        #
        # forminfo['owner'] = obj.owner
        # if obj.editor_group is not None:
        #     forminfo['editor_group'] = obj.editor_group
        # if obj.editor is not None:
        #     forminfo['editor'] = obj.editor
        #
        # forminfo['doaj_seal'] = obj.has_seal()

        return forminfo



class JournalFormXWalk(JournalGenericXWalk):

    @classmethod
    def form2obj(cls, form):

        #this is new version for public application form


        #todo new public application form is ready above


        #  # FIXME: in the new version of the form, notes will have IDs, so we need to pick them up too
        # for formnote in form.notes.data:
        #     if formnote["note"]:
        #         journal.add_note(formnote["note"])
        #
        # new_subjects = []
        # for code in form.subject.data:
        #     sobj = {"scheme": 'LCC', "term": lcc.lookup_code(code), "code": code}
        #     new_subjects.append(sobj)
        # bibjson.set_subjects(new_subjects)
        #
        # if getattr(form, 'owner', None):
        #     owner = form.owner.data
        #     if owner:
        #         owner = owner.strip()
        #         journal.set_owner(owner)
        #
        # if getattr(form, 'editor_group', None):
        #     editor_group = form.editor_group.data
        #     if editor_group:
        #         editor_group = editor_group.strip()
        #         journal.set_editor_group(editor_group)
        #
        # if getattr(form, "editor", None):
        #     editor = form.editor.data
        #     if editor:
        #         editor = editor.strip()
        #         journal.set_editor(editor)
        #
        # if getattr(form, "doaj_seal", None):
        #     journal.set_seal(form.doaj_seal.data)
        #
        # # continuations information
        # if getattr(form, "replaces", None):
        #     bibjson.replaces = form.replaces.data
        # if getattr(form, "is_replaced_by", None):
        #     bibjson.is_replaced_by = form.is_replaced_by.data
        # if getattr(form, "discontinued_date", None):
        #     bibjson.discontinued_date = form.discontinued_date.data

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
            forminfo['processing_charges_amount'] = apc.get('max_price')[0]
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
        #forminfo['waiver_policy'] = reverse_interpret_special(forminfo['waiver_policy_url'] is not None and forminfo['waiver_policy_url'] != '')

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
        forminfo['license_display'] = reverse_interpret_special(license.get('embedded'))
        forminfo['license_display_url'] = license.get('embedded_example_url')

        forminfo['article_orcid'] = bibjson.article_orcid
        forminfo['boai'] = bibjson.boai
        forminfo['article_i4oc_open_citations'] = bibjson.article_i4oc_open_citations

        # # checkboxes
        # forminfo['deposit_policy'], forminfo['deposit_policy_other'] = \
        #     reverse_interpret_other(reverse_interpret_special(bibjson.deposit_policy), Choices.deposit_policy_list())

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
