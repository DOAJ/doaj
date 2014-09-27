from portality import models, lcc
from portality.datasets import licenses, main_license_options
from flask.ext.login import current_user
from portality.util import flash_with_url, listpop

none_val = "None"
true_val = 'True'
false_val = 'False'

other_val = 'Other'
other_label = other_val
other_choice = (other_val, other_val)

digital_archiving_policy_no_policy_value = "No policy in place"
digital_archiving_policy_specific_library_value = 'A national library'
digital_archiving_policy_specific_library_label = digital_archiving_policy_specific_library_value
digital_archiving_policy_optional_url_choices = [
    (digital_archiving_policy_no_policy_value, digital_archiving_policy_no_policy_value),
]
digital_archiving_policy_optional_url_choices_optvals = [v[0] for v in digital_archiving_policy_optional_url_choices]
__digital_archiving_policy_choices = [
    ('LOCKSS', 'LOCKSS'),
    ('CLOCKSS', 'CLOCKSS'),
    ('Portico', 'Portico'),
    ('PMC/Europe PMC/PMC Canada', 'PMC/Europe PMC/PMC Canada'),
    (digital_archiving_policy_specific_library_value, digital_archiving_policy_specific_library_value),
] + [other_choice]
digital_archiving_policy_choices = digital_archiving_policy_optional_url_choices  + __digital_archiving_policy_choices
digital_archiving_policy_choices_list = [v[0] for v in digital_archiving_policy_choices]

article_identifiers_choices = [
    (none_val, none_val),
    ('DOI', 'DOI'),
    ('Handles', 'Handles'),
    ('ARK', 'ARK'),
] + [other_choice]
article_identifiers_choices_list = [v[0] for v in article_identifiers_choices]

fulltext_format_choices = [
    ('PDF', 'PDF'),
    ('HTML', 'HTML'),
    ('ePUB', 'ePUB'),
    ('XML', 'XML'),
] + [other_choice]
fulltext_format_choices_list = [v[0] for v in fulltext_format_choices]

license_optional_url_choices = [ ('Not CC-like', 'No') ]
license_optional_url_choices_optvals = [v[0] for v in license_optional_url_choices]
license_choices = main_license_options + license_optional_url_choices + [other_choice]
license_choices_list = [v[0] for v in license_choices]


deposit_policy_choices = [
    (none_val, none_val),
    ('Sherpa/Romeo', 'Sherpa/Romeo'),
    ('Dulcinea', 'Dulcinea'),
    ('OAKlist', 'OAKlist'),
    ('H\xc3\xa9lo\xc3\xafse'.decode('utf-8'), 'H\xc3\xa9lo\xc3\xafse'.decode('utf-8')),
    ('Diadorim', 'Diadorim'),
] + [other_choice]
deposit_policy_choices_list = [v[0] for v in deposit_policy_choices]

optional_url_binary_choices = [(false_val, 'No')]
optional_url_binary_choices_optvals = [v[0] for v in optional_url_binary_choices]
binary_choices = [(true_val, 'Yes')] + optional_url_binary_choices
ternary_choices = binary_choices + [other_choice]
optional_url_ternary_choices_optvals = optional_url_binary_choices_optvals  # "No" still makes the URL optional, from ["Yes", "No", "Other"]
ternary_choices_list = [v[0] for v in ternary_choices]

def interpret_special(val):
    # if you modify this, make sure to modify reverse_interpret_special as well
    if isinstance(val, basestring):
        if val.lower() == true_val.lower():
            return True
        elif val.lower() == false_val.lower():
            return False
        elif val.lower() == none_val.lower():
            return None
        elif val == digital_archiving_policy_no_policy_value:
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
        return none_val
    elif val is True:
        return true_val
    elif val is False:
        return false_val
    # no need to handle digital archiving policy or other list
    # fields here - empty lists handled below

    if isinstance(val, list):
        if len(val) == 1:
            reverse_actual_val = reverse_interpret_special(val[0], field=field)
            return [reverse_actual_val]
        elif len(val) == 0:
            # mostly it'll just be a None val
            if field == 'digital_archiving_policy':
                return [digital_archiving_policy_no_policy_value]

            return [none_val]

        return val

    return val



def interpret_other(value, other_field_data, other_value=other_val, store_other_label=False):
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
    if isinstance(value, basestring):
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


def reverse_interpret_other(interpreted_value, possible_original_values, other_value=other_val, replace_label=other_label):
    '''
    Returns tuple: (main field value or list of values, other field value)
    '''
    # if you modify this, make sure to modify interpret_other too
    other_field_val = ''

    if isinstance(interpreted_value, basestring):
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

class SuggestionFormXWalk(object):
    # NOTE: if you change something here, unless it only relates to suggestions, you will probably
    # need to change the same thing in JournalFormXWalk in portality.journal .
    # TODO: refactor suggestion and journal xwalks to put the common code in one place

    @classmethod
    def is_new_editor_group(cls, form, old_suggestion):
        old_eg = old_suggestion.editor_group
        new_eg = form.editor_group.data
        return old_eg != new_eg and new_eg is not None and new_eg != ""

    @classmethod
    def is_new_editor(cls, form, old_suggestion):
        old_ed = old_suggestion.editor
        new_ed = form.editor.data
        return old_ed != new_ed and new_ed is not None and new_ed != ""

    @staticmethod
    def form2obj(form, existing_suggestion=None):
        suggestion = models.Suggestion()
        bibjson = suggestion.bibjson()

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
            suggestion.add_contact(form.contact_name.data, form.contact_email.data)
        if form.country.data:
            bibjson.country = form.country.data

        if interpret_special(form.processing_charges.data):
            bibjson.set_apc(form.processing_charges_currency.data, form.processing_charges_amount.data)

        if interpret_special(form.submission_charges.data):
            bibjson.set_submission_charges(form.submission_charges_currency.data, form.submission_charges_amount.data)

        suggestion.set_articles_last_year(form.articles_last_year.data, form.articles_last_year_url.data)

        if interpret_special(form.waiver_policy.data):
            bibjson.add_url(form.waiver_policy_url.data, 'waiver_policy')

        # checkboxes
        if interpret_special(form.digital_archiving_policy.data) or form.digital_archiving_policy_url.data:
            archiving_policies = interpret_special(form.digital_archiving_policy.data)
            archiving_policies = interpret_other(archiving_policies, form.digital_archiving_policy_other.data, store_other_label=True)
            archiving_policies = interpret_other(archiving_policies, form.digital_archiving_policy_library.data, digital_archiving_policy_specific_library_value, store_other_label=True)
            bibjson.set_archiving_policy(archiving_policies, form.digital_archiving_policy_url.data)

        if form.crawl_permission.data and form.crawl_permission.data != 'None':
            bibjson.allows_fulltext_indexing = interpret_special(form.crawl_permission.data)  # just binary

        # checkboxes
        article_ids = interpret_special(form.article_identifiers.data)
        article_ids = interpret_other(article_ids, form.article_identifiers_other.data)
        if article_ids:
            bibjson.persistent_identifier_scheme = article_ids

        if form.metadata_provision.data and form.metadata_provision.data != 'None':
            suggestion.article_metadata = interpret_special(form.metadata_provision.data)  # just binary

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
                by = True if 'by' in form.license_checkbox.data else False
                nc = True if 'nc' in form.license_checkbox.data else False
                nd = True if 'nd' in form.license_checkbox.data else False
                sa = True if 'sa' in form.license_checkbox.data else False
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
            holds_copyright = interpret_other(
                interpret_special(form.copyright.data),
                form.copyright_other.data
            )
            bibjson.set_author_copyright(form.copyright_url.data, holds_copyright=holds_copyright)

        if form.publishing_rights.data and form.publishing_rights.data != 'None':
            publishing_rights = interpret_other(
                interpret_special(form.publishing_rights.data),
                form.publishing_rights_other.data
            )
            bibjson.set_author_publishing_rights(form.publishing_rights_url.data, holds_rights=publishing_rights)

        if form.suggester_name.data or form.suggester_email.data:
            suggestion.set_suggester(form.suggester_name.data, form.suggester_email.data)

        # admin stuff
        if getattr(form, 'application_status', None):
            suggestion.set_application_status(form.application_status.data)

        if getattr(form, 'notes', None):
            # need to copy over the notes from the existing suggestion object, if any, otherwise
            # the dates on all the notes will get reset to right now (i.e. last_updated)
            # since the suggestion object we're creating in this xwalk is a new, empty one
            if existing_suggestion:
                suggestion.set_notes(existing_suggestion.notes())

            # generate index of notes, just the text
            curnotes = []
            for curnote in suggestion.notes():
                curnotes.append(curnote['note'])

            # add any new notes
            formnotes = []
            for formnote in form.notes.data:
                if formnote['note']:
                    if formnote['note'] not in curnotes and formnote["note"] != "":
                        suggestion.add_note(formnote['note'])
                    # also generate another text index of notes, this time an index of the form notes
                    formnotes.append(formnote['note'])

            if current_user.has_role("delete_note"):
                # delete all notes not coming back from the form, means they've been deleted
                # also if one of the saved notes is completely blank, delete it
                for curnote in suggestion.notes()[:]:
                    if not curnote['note'] or curnote['note'] not in formnotes:
                        suggestion.remove_note(curnote)

        if getattr(form, 'subject', None):
            new_subjects = []
            for code in form.subject.data:
                sobj = {"scheme": 'LCC', "term": lcc.lookup_code(code), "code": code}
                new_subjects.append(sobj)
            bibjson.set_subjects(new_subjects)

        if getattr(form, 'owner', None):
            owns = form.owner.data.strip()
            if owns:
                suggestion.set_owner(form.owner.data.strip())

        if getattr(form, 'editor_group', None):
            editor_group = form.editor_group.data.strip()
            if editor_group:
                suggestion.set_editor_group(editor_group)

        if getattr(form, "editor", None):
            editor = form.editor.data.strip()
            if editor:
                suggestion.set_editor(editor)

        return suggestion


    @staticmethod
    def obj2form(obj):
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

        apc = bibjson.apc
        if apc:
            forminfo['processing_charges'] = reverse_interpret_special(True)
            forminfo['processing_charges_currency'] = apc.get('currency')
            forminfo['processing_charges_amount'] = apc.get('average_price')
        else:
            forminfo['processing_charges'] = reverse_interpret_special(False)

        submission_charges = bibjson.submission_charges
        if submission_charges:
            forminfo['submission_charges'] = reverse_interpret_special(True)
            forminfo['submission_charges_currency'] = submission_charges.get('currency')
            forminfo['submission_charges_amount'] = submission_charges.get('average_price')
        else:
            forminfo['submission_charges'] = reverse_interpret_special(False)

        articles_last_year = obj.articles_last_year
        if articles_last_year:
            forminfo['articles_last_year'] = articles_last_year.get('count')
            forminfo['articles_last_year_url'] = articles_last_year.get('url')

        forminfo['waiver_policy_url'] = bibjson.get_single_url(urltype='waiver_policy')
        forminfo['waiver_policy'] = forminfo['waiver_policy_url'] == ''

        # checkboxes
        archiving_policies = reverse_interpret_special(bibjson.archiving_policy.get('policy', []), field='digital_archiving_policy')

        # for backwards compatibility we keep the "Other" field first in the reverse xwalk
        # previously we didn't store which free text value was which (Other, or specific national library)
        # so in those cases, just put it in "Other", it'll be correct most of the time
        archiving_policies, forminfo['digital_archiving_policy_other'] = \
            reverse_interpret_other(archiving_policies, digital_archiving_policy_choices_list)

        archiving_policies, forminfo['digital_archiving_policy_library'] = \
            reverse_interpret_other(
                archiving_policies,
                digital_archiving_policy_choices_list,
                other_value=digital_archiving_policy_specific_library_value,
                replace_label=digital_archiving_policy_specific_library_label
            )

        forminfo['digital_archiving_policy'] = archiving_policies
        forminfo['digital_archiving_policy_url'] = bibjson.archiving_policy.get('url')

        forminfo['crawl_permission'] = reverse_interpret_special(bibjson.allows_fulltext_indexing)

        # checkboxes
        article_ids = reverse_interpret_special(bibjson.persistent_identifier_scheme)
        article_ids, forminfo['article_identifiers_other'] = \
            reverse_interpret_other(article_ids, article_identifiers_choices_list)

        forminfo['article_identifiers'] = article_ids

        forminfo['metadata_provision'] = reverse_interpret_special(obj.article_metadata)


        forminfo['download_statistics'] = reverse_interpret_special(bibjson.article_statistics.get('statistics'))
        forminfo['download_statistics_url'] = bibjson.article_statistics.get('url')

        forminfo['first_fulltext_oa_year'] = bibjson.oa_start.get('year')

        # checkboxes
        forminfo['fulltext_format'], forminfo['fulltext_format_other'] = \
            reverse_interpret_other(bibjson.format, fulltext_format_choices_list)

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
        forminfo['license'], forminfo['license_other'] = reverse_interpret_other(license.get('type'), license_choices_list)

        if forminfo['license_other']:
            forminfo['license_checkbox'] = []
            if license.get('BY'): forminfo['license_checkbox'].append('by')
            if license.get('SA'): forminfo['license_checkbox'].append('sa')
            if license.get('NC'): forminfo['license_checkbox'].append('nc')
            if license.get('ND'): forminfo['license_checkbox'].append('nd')

        forminfo['license_url'] = license.get('url')
        forminfo['open_access'] = reverse_interpret_special(license.get('open_access'))
        forminfo['license_embedded'] = reverse_interpret_special(license.get('embedded'))
        forminfo['license_embedded_url'] = license.get('embedded_example_url')

        # checkboxes
        forminfo['deposit_policy'], forminfo['deposit_policy_other'] = \
            reverse_interpret_other(reverse_interpret_special(bibjson.deposit_policy), deposit_policy_choices_list)

        forminfo['copyright'], forminfo['copyright_other'] = \
            reverse_interpret_other(
                reverse_interpret_special(bibjson.author_copyright.get('copyright')),
                ternary_choices_list
            )
        forminfo['copyright_url'] = bibjson.author_copyright.get('url')

        forminfo['publishing_rights'], forminfo['publishing_rights_other'] = \
            reverse_interpret_other(
                reverse_interpret_special(bibjson.author_publishing_rights.get('publishing_rights')),
                ternary_choices_list
            )
        forminfo['publishing_rights_url'] = bibjson.author_publishing_rights.get('url')

        forminfo['suggester_name'] = obj.suggester.get('name')
        forminfo['suggester_email'] = obj.suggester.get('email')
        forminfo['suggester_email_confirm'] = forminfo['suggester_email']

        forminfo['application_status'] = obj.application_status

        forminfo['notes'] = obj.notes()

        forminfo['subject'] = []
        for s in bibjson.subjects():
            forminfo['subject'].append(s['code'])

        forminfo['owner'] = obj.owner
        if obj.editor_group is not None:
            forminfo['editor_group'] = obj.editor_group
        if obj.editor is not None:
            forminfo['editor'] = obj.editor

        return forminfo