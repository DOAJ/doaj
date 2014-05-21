import json
from copy import deepcopy
from datetime import datetime

from flask import flash
from flask import render_template, redirect, url_for

from portality import lcc
from portality.util import listpop
from portality.datasets import licenses
from portality.models import Journal, EditorGroup, Account
from portality.view import forms
from portality.core import app
import portality.models as models
import portality.util as util
from portality import xwalk
from portality.view.forms import JournalForm, subjects2str, other_val, digital_archiving_policy_specific_library_value

from portality.datasets import country_options_two_char_code_index
from portality.lcc import lcc_jstree

def get_journal(journal_id):
    j = models.Journal.pull(journal_id)
    return j

def request_handler(request, journal_id, redirect_route="admin.journal_page", template="admin/journal.html",
                    activate_deactivate=False, group_editable=False, editors=None, editorial_available=False):
    j = get_journal(journal_id)

    current_info = models.ObjectDict(JournalFormXWalk.obj2form(j))
    form = JournalForm(request.form, current_info)

    current_country = xwalk.get_country_code(j.bibjson().country)

    if current_country not in country_options_two_char_code_index:
        # couldn't find it, better warn the user to look for it
        # themselves
        country_help_text = "This journal's country has been recorded as \"{country}\". Please select it in the Country menu.".format(country=current_country)
    else:
        country_help_text = ''

    form.country.description = '<span class="red">' + country_help_text + '</span>'

    # add the contents of a few fields to their descriptions since select2 autocomplete
    # would otherwise obscure the full values
    if form.publisher.data:
        if not form.publisher.description:
            form.publisher.description = 'Full contents: ' + form.publisher.data
        else:
            form.publisher.description += '<br><br>Full contents: ' + form.publisher.data

    if form.society_institution.data:
        if not form.society_institution.description:
            form.society_institution.description = 'Full contents: ' + form.society_institution.data
        else:
            form.society_institution.description += '<br><br>Full contents: ' + form.society_institution.data

    if form.platform.data:
        if not form.platform.description:
            form.platform.description = 'Full contents: ' + form.platform.data
        else:
            form.platform.description += '<br><br>Full contents: ' + form.platform.data

    first_field_with_error = ''

    if editors is not None:
        form.editor.choices = [("", "Choose an editor")] + [(editor, editor) for editor in editors]
    else:
        if j.editor is not None:
            form.editor.choices = [(j.editor, j.editor)]
        else:
            form.editor.choices = [("", "")]

    if request.method == 'POST':
        if form.make_all_fields_optional.data:
            valid = True
        else:
            valid = form.validate()
        if valid:
            # even though you can only edit journals right now, keeping the same
            # method as editing suggestions (i.e. creating a new object
            # and editing its properties)

            email_editor = False
            if group_editable:
                email_editor = JournalFormXWalk.is_new_editor_group(form, j)

            email_associate = False
            if editorial_available:
                email_associate = JournalFormXWalk.is_new_editor(form, j)

            # do the core crosswalk
            journal = JournalFormXWalk.form2obj(form, existing_journal=j)

            # some of the properties (id, in_doaj, etc.) have to be carried over
            # otherwise they implicitly end up getting changed to their defaults
            # when a journal gets edited (e.g. it always gets taken out of DOAJ)
            # if we don't copy over the in_doaj attribute to the new journal object
            journal['id'] = j['id']
            created_date = j.created_date if j.created_date else datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            journal.set_created(created_date)
            journal.bibjson().active = j.is_in_doaj()
            journal.set_in_doaj(j.is_in_doaj())

            if not group_editable or not editorial_available:
                journal.set_editor_group(j.editor_group)

            if not editorial_available:
                journal.set_editor(j.editor)

            # FIXME: probably should check that the editor is in the editor_group and remove if not

            journal.save()
            flash('Journal updated.', 'success')

            # only actually send the email when we've successfully processed the form
            if email_editor:
                send_editor_group_email(journal)

            if email_associate:
                send_editor_email(journal)

            return redirect(url_for(redirect_route, journal_id=journal_id, _anchor='done'))
                # meaningless anchor to replace #first_problem used on the form
                # anchors persist between 3xx redirects to the same resource
        else:
            for field in form:  # in order of definition of fields, so the order of rendering should be (manually) kept the same as the order of definition for this to work
                if field.errors:
                    first_field_with_error = field.short_name
                    break

    return render_template(
            template,
            form=form,
            first_field_with_error=first_field_with_error,
            q_numbers=xrange(1, 10000).__iter__(),  # a generator for the purpose of displaying numbered questions
            other_val=other_val,
            digital_archiving_policy_specific_library_value=digital_archiving_policy_specific_library_value,
            edit_journal_page=True,
            admin_page=True,
            journal=j,
            subjectstr=subjects2str(j.bibjson().subjects()),
            lcc_jstree=json.dumps(lcc_jstree),
            activate_deactivate=activate_deactivate,
            group_editable=group_editable,
            editorial_available=editorial_available
    )

def suggestion2journal(suggestion):
    journal_data = deepcopy(suggestion.data)
    del journal_data['suggestion']
    del journal_data['index']
    del journal_data['admin']['application_status']
    del journal_data['id']
    del journal_data['created_date']
    del journal_data['last_updated']
    journal_data['bibjson']['active'] = True
    new_j = Journal(**journal_data)
    return new_j

JOURNAL_ASSIGNED_GROUP_TEMPLATE = \
"""
Dear {editor},

The journal "{journal_name}" has been assigned to your Editor Group by a Managing Editor.
You may access the journal in your Editor Area: {url_root}/editor/ .

The DOAJ Team
Twitter: https://twitter.com/DOAJplus
Facebook: http://www.facebook.com/DirectoryofOpenAccessJournals
LinkedIn: http://www.linkedin.com/company/directory-of-open-access-journals-doaj-
"""


def send_editor_group_email(journal):
    eg = EditorGroup.pull_by_key("name", journal.editor_group)
    if eg is None:
        return
    editor = Account.pull(eg.editor)

    url_root = app.config.get("BASE_URL")
    to = [editor.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - new journal assigned to your group"
    text = JOURNAL_ASSIGNED_GROUP_TEMPLATE.format(editor=editor.id.encode('utf-8', 'replace'), journal_name=journal.bibjson().title.encode('utf-8', 'replace'), url_root=url_root)

    util.send_mail(to=to, fro=fro, subject=subject, text=text)

JOURNAL_ASSIGNED_EDITOR_TEMPLATE = \
"""
Dear {editor},

The journal "{journal_name}" has been assigned to you by the Editor in your Editor Group "{group_name}".
You may access the journal in your Editor Area: {url_root}/editor/ .

The DOAJ Team
Twitter: https://twitter.com/DOAJplus
Facebook: http://www.facebook.com/DirectoryofOpenAccessJournals
LinkedIn: http://www.linkedin.com/company/directory-of-open-access-journals-doaj-
"""

def send_editor_email(journal):
    editor = Account.pull(journal.editor)
    eg = EditorGroup.pull_by_key("name", journal.editor_group)

    url_root = app.config.get("BASE_URL")
    to = [editor.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - new journal assigned to you"
    text = JOURNAL_ASSIGNED_EDITOR_TEMPLATE.format(editor=editor.id.encode('utf-8', 'replace'),
                                                   journal_name=journal.bibjson().title.encode('utf-8', 'replace'),
                                                   group_name=eg.name.encode("utf-8", "replace"), url_root=url_root)

    util.send_mail(to=to, fro=fro, subject=subject, text=text)

class JournalFormXWalk(object):
    # NOTE: if you change something here, you will probably
    # need to change the same thing in SuggestionFormXWalk in portality.suggestion .
    # TODO: refactor suggestion and journal xwalks to put the common code in one place

    @classmethod
    def is_new_editor_group(cls, form, old_journal):
        old_eg = old_journal.editor_group
        new_eg = form.editor_group.data
        return old_eg != new_eg and new_eg is not None and new_eg != ""

    @classmethod
    def is_new_editor(cls, form, old_journal):
        old_ed = old_journal.editor
        new_ed = form.editor.data
        return old_ed != new_ed and new_ed is not None and new_ed != ""

    @staticmethod
    def form2obj(form, existing_journal):
        journal = Journal()
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

        if forms.interpret_special(form.processing_charges.data):
            bibjson.set_apc(form.processing_charges_currency.data, form.processing_charges_amount.data)

        if forms.interpret_special(form.submission_charges.data):
            bibjson.set_submission_charges(form.submission_charges_currency.data, form.submission_charges_amount.data)

        if forms.interpret_special(form.waiver_policy.data):
            bibjson.add_url(form.waiver_policy_url.data, 'waiver_policy')

        # checkboxes
        if forms.interpret_special(form.digital_archiving_policy.data) or form.digital_archiving_policy_url.data:
            archiving_policies = forms.interpret_special(form.digital_archiving_policy.data)
            archiving_policies = forms.interpret_other(archiving_policies, form.digital_archiving_policy_other.data, store_other_label=True)
            archiving_policies = forms.interpret_other(archiving_policies, form.digital_archiving_policy_library.data, forms.digital_archiving_policy_specific_library_value, store_other_label=True)
            bibjson.set_archiving_policy(archiving_policies, form.digital_archiving_policy_url.data)

        if form.crawl_permission.data and form.crawl_permission.data != 'None':
            bibjson.allows_fulltext_indexing = forms.interpret_special(form.crawl_permission.data)  # just binary

        # checkboxes
        article_ids = forms.interpret_special(form.article_identifiers.data)
        article_ids = forms.interpret_other(article_ids, form.article_identifiers_other.data)
        if article_ids:
            bibjson.persistent_identifier_scheme = article_ids

        if (form.download_statistics.data and form.download_statistics.data != 'None') or form.download_statistics_url.data:
            bibjson.set_article_statistics(form.download_statistics_url.data, forms.interpret_special(form.download_statistics.data))

        if form.first_fulltext_oa_year.data:
            bibjson.set_oa_start(year=form.first_fulltext_oa_year.data)

        # checkboxes
        fulltext_format = forms.interpret_other(form.fulltext_format.data, form.fulltext_format_other.data)
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
                has_detection=forms.interpret_special(form.plagiarism_screening.data)
            )

        if form.publication_time.data:
            bibjson.publication_time = form.publication_time.data

        bibjson.add_url(form.oa_statement_url.data, urltype='oa_statement')

        license_type = forms.interpret_other(form.license.data, form.license_other.data)
        if forms.interpret_special(license_type):
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
                open_access=forms.interpret_special(form.open_access.data),
                by=by, nc=nc, nd=nd, sa=sa,
                embedded=forms.interpret_special(form.license_embedded.data),
                embedded_example_url=form.license_embedded_url.data
            )

        # checkboxes
        deposit_policies = forms.interpret_special(form.deposit_policy.data)  # need empty list if it's just "None"
        deposit_policies = forms.interpret_other(deposit_policies, form.deposit_policy_other.data)
        if deposit_policies:
            bibjson.deposit_policy = deposit_policies

        if form.copyright.data and form.copyright.data != 'None':
            holds_copyright = forms.interpret_other(
                forms.interpret_special(form.copyright.data),
                form.copyright_other.data
            )
            bibjson.set_author_copyright(form.copyright_url.data, holds_copyright=holds_copyright)

        if form.publishing_rights.data and form.publishing_rights.data != 'None':
            publishing_rights = forms.interpret_other(
                forms.interpret_special(form.publishing_rights.data),
                form.publishing_rights_other.data
            )
            bibjson.set_author_publishing_rights(form.publishing_rights_url.data, holds_rights=publishing_rights)

        # need to copy over the notes from the existing journal object, if any, otherwise
        # the dates on all the notes will get reset to right now (i.e. last_updated)
        # since the journal object we're creating in this xwalk is a new, empty one
        journal.set_notes(existing_journal.notes())

        # generate index of notes, just the text
        curnotes = []
        for curnote in journal.notes():
            curnotes.append(curnote['note'])

        # add any new notes
        formnotes = []
        for formnote in form.notes.data:
            if formnote['note']:
                if formnote['note'] not in curnotes:
                    journal.add_note(formnote['note'])
                # also generate another text index of notes, this time an index of the form notes
                formnotes.append(formnote['note'])

        # delete all notes not coming back from the form, means they've been deleted
        # also if one of the saved notes is completely blank, delete it
        for curnote in journal.notes()[:]:
            if not curnote['note'] or curnote['note'] not in formnotes:
                journal.remove_note(curnote)

        new_subjects = []
        for code in form.subject.data:
            sobj = {"scheme": 'LCC', "term": lcc.lookup_code(code), "code": code}
            new_subjects.append(sobj)
        bibjson.set_subjects(new_subjects)

        owner = form.owner.data.strip()
        if owner:
            journal.set_owner(owner)

        editor_group = form.editor_group.data.strip()
        print "editor_group", editor_group
        if editor_group:
            journal.set_editor_group(editor_group)

        editor = form.editor.data.strip()
        print "editor", editor
        if editor:
            journal.set_editor(editor)

        # old fields - only create them in the journal record if the values actually exist
        # need to use interpret_special in the test condition in case 'None' comes back from the form
        if getattr(form, 'author_pays', None):
            if forms.interpret_special(form.author_pays.data):
                bibjson.author_pays = form.author_pays.data
        if getattr(form, 'author_pays_url', None):
            if forms.interpret_special(form.author_pays_url.data):
                bibjson.author_pays_url = form.author_pays_url.data
        if getattr(form, 'oa_end_year', None):
            if forms.interpret_special(form.oa_end_year.data):
                bibjson.set_oa_end(form.oa_end_year.data)

        return journal


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
            forminfo['processing_charges'] = forms.reverse_interpret_special(True)
            forminfo['processing_charges_currency'] = apc.get('currency')
            forminfo['processing_charges_amount'] = apc.get('average_price')
        else:
            forminfo['processing_charges'] = forms.reverse_interpret_special(False)

        submission_charges = bibjson.submission_charges
        if submission_charges:
            forminfo['submission_charges'] = forms.reverse_interpret_special(True)
            forminfo['submission_charges_currency'] = submission_charges.get('currency')
            forminfo['submission_charges_amount'] = submission_charges.get('average_price')
        else:
            forminfo['submission_charges'] = forms.reverse_interpret_special(False)

        forminfo['waiver_policy_url'] = bibjson.get_single_url(urltype='waiver_policy')
        forminfo['waiver_policy'] = forminfo['waiver_policy_url'] == ''

        # checkboxes
        archiving_policies = forms.reverse_interpret_special(bibjson.archiving_policy.get('policy', []), field='digital_archiving_policy')

        # for backwards compatibility we keep the "Other" field first in the reverse xwalk
        # previously we didn't store which free text value was which (Other, or specific national library)
        # so in those cases, just put it in "Other", it'll be correct most of the time
        archiving_policies, forminfo['digital_archiving_policy_other'] = \
            forms.reverse_interpret_other(archiving_policies, forms.digital_archiving_policy_choices_list)

        archiving_policies, forminfo['digital_archiving_policy_library'] = \
            forms.reverse_interpret_other(
                archiving_policies,
                forms.digital_archiving_policy_choices_list,
                other_value=forms.digital_archiving_policy_specific_library_value,
                replace_label=forms.digital_archiving_policy_specific_library_label
            )

        forminfo['digital_archiving_policy'] = archiving_policies
        forminfo['digital_archiving_policy_url'] = bibjson.archiving_policy.get('url')

        forminfo['crawl_permission'] = forms.reverse_interpret_special(bibjson.allows_fulltext_indexing)

        # checkboxes
        article_ids = forms.reverse_interpret_special(bibjson.persistent_identifier_scheme)
        article_ids, forminfo['article_identifiers_other'] = \
            forms.reverse_interpret_other(article_ids, forms.article_identifiers_choices_list)

        forminfo['article_identifiers'] = article_ids

        forminfo['download_statistics'] = forms.reverse_interpret_special(bibjson.article_statistics.get('statistics'))
        forminfo['download_statistics_url'] = bibjson.article_statistics.get('url')

        forminfo['first_fulltext_oa_year'] = bibjson.oa_start.get('year')

        # checkboxes
        forminfo['fulltext_format'], forminfo['fulltext_format_other'] = \
            forms.reverse_interpret_other(bibjson.format, forms.fulltext_format_choices_list)

        forminfo['keywords'] = bibjson.keywords

        forminfo['languages'] = bibjson.language

        forminfo['editorial_board_url'] = bibjson.get_single_url('editorial_board')

        forminfo['review_process'] = bibjson.editorial_review.get('process', '')
        forminfo['review_process_url'] = bibjson.editorial_review.get('url')

        forminfo['aims_scope_url'] = bibjson.get_single_url('aims_scope')
        forminfo['instructions_authors_url'] = bibjson.get_single_url('author_instructions')

        forminfo['plagiarism_screening'] = forms.reverse_interpret_special(bibjson.plagiarism_detection.get('detection'))
        forminfo['plagiarism_screening_url'] = bibjson.plagiarism_detection.get('url')

        forminfo['publication_time'] = bibjson.publication_time

        forminfo['oa_statement_url'] = bibjson.get_single_url('oa_statement')

        license = bibjson.get_license()
        license = license if license else {}  # reinterpret the None val
        forminfo['license'], forminfo['license_other'] = forms.reverse_interpret_other(license.get('type'), forms.license_choices_list)

        if forminfo['license_other']:
            forminfo['license_checkbox'] = []
            if license.get('BY'): forminfo['license_checkbox'].append('by')
            if license.get('SA'): forminfo['license_checkbox'].append('sa')
            if license.get('NC'): forminfo['license_checkbox'].append('nc')
            if license.get('ND'): forminfo['license_checkbox'].append('nd')

        forminfo['license_url'] = license.get('url')
        forminfo['open_access'] = forms.reverse_interpret_special(license.get('open_access'))
        forminfo['license_embedded'] = forms.reverse_interpret_special(license.get('embedded'))
        forminfo['license_embedded_url'] = license.get('embedded_example_url')

        # checkboxes
        forminfo['deposit_policy'], forminfo['deposit_policy_other'] = \
            forms.reverse_interpret_other(forms.reverse_interpret_special(bibjson.deposit_policy), forms.deposit_policy_choices_list)

        forminfo['copyright'], forminfo['copyright_other'] = \
            forms.reverse_interpret_other(
                forms.reverse_interpret_special(bibjson.author_copyright.get('copyright', '')),
                forms.ternary_choices_list
            )
        forminfo['copyright_url'] = bibjson.author_copyright.get('url')

        forminfo['publishing_rights'], forminfo['publishing_rights_other'] = \
            forms.reverse_interpret_other(
                forms.reverse_interpret_special(bibjson.author_publishing_rights.get('publishing_rights', '')),
                forms.ternary_choices_list
            )
        forminfo['publishing_rights_url'] = bibjson.author_publishing_rights.get('url')

        forminfo['notes'] = obj.notes()

        forminfo['subject'] = []
        for s in bibjson.subjects():
            forminfo['subject'].append(s['code'])

        forminfo['owner'] = obj.owner
        if obj.editor_group is not None:
            forminfo['editor_group'] = obj.editor_group
        if obj.editor is not None:
            forminfo['editor'] = obj.editor
        
        # old fields - only show them if the values actually exist in the journal record
        if bibjson.author_pays:
            forminfo['author_pays'] = bibjson.author_pays
        if bibjson.author_pays_url:
            forminfo['author_pays_url'] = bibjson.author_pays_url
        if bibjson.oa_end:
            forminfo['oa_end_year'] = bibjson.oa_end.get('year')

        return forminfo