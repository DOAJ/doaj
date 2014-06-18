from datetime import datetime
from flask import render_template, flash, url_for, json, abort

from flask.ext.login import current_user

from portality.core import app
from portality import lcc
from portality import journal
from portality.account import create_account_on_suggestion_approval, \
    send_suggestion_approved_email
from portality import models
from portality.util import flash_with_url, listpop
from portality.view import forms
from portality.datasets import licenses
from portality.view.forms import other_val, digital_archiving_policy_specific_library_value
from werkzeug.utils import redirect

from portality.view.forms import EditSuggestionForm, subjects2str
from portality.lcc import lcc_jstree
from portality import util
from portality import lock

def request_handler(request, suggestion_id, redirect_route="admin.suggestion_page", template="admin/suggestion.html", locked_template="admin/suggestion_locked.html",
                    editors=None, group_editable=False, editorial_available=False, status_options="admin"):
    if not current_user.has_role("edit_suggestion"):
        abort(401)
    s = models.Suggestion.pull(suggestion_id)
    if s is None:
        abort(404)

    # attempt to get a lock on the object
    try:
        lockinfo = lock.lock("suggestion", suggestion_id, current_user.id)
    except lock.Locked as l:
        return render_template(locked_template, suggestion=s, lock=l.lock)

    current_info = models.ObjectDict(SuggestionFormXWalk.obj2form(s))
    form = EditSuggestionForm(request.form, current_info)

    if status_options == "admin":
        form.application_status.choices = forms.application_status_choices_admin
    else:
        form.application_status.choices = forms.application_status_choices_editor

    process_the_form = True
    if request.method == 'POST' and s.application_status == 'accepted':
        flash('You cannot edit suggestions which have been accepted into DOAJ.', 'error')
        process_the_form = False

    if form.application_status.data == "accepted" and form.make_all_fields_optional.data:
        flash("You cannot accept a suggestion into the DOAJ without fully validating it", "error")
        process_the_form = False

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

    if editors is not None:
        form.editor.choices = [("", "Choose an editor")] + [(editor, editor) for editor in editors]
    else:
        if s.editor is not None:
            form.editor.choices = [(s.editor, s.editor)]
        else:
            form.editor.choices = [("", "")]


    return suggestion_form(form, request, template,
                           existing_suggestion=s,
                           suggestion=s,
                           process_the_form=process_the_form,
                           admin_page=True,
                           subjectstr=subjects2str(s.bibjson().subjects()),
                           lcc_jstree=json.dumps(lcc_jstree),
                           group_editable=group_editable,
                           editorial_available=editorial_available,
                           redirect_route=redirect_route,
                           lock=lockinfo
    )

# provide reusability to the view functions
def suggestion_form(form, request, template_name, existing_suggestion=None, success_url=None,
                    process_the_form=True, group_editable=False, editorial_available=False, redirect_route=None, lock=None, **kwargs):

    first_field_with_error = ''

    #import json
    #print json.dumps(request.form, indent=3)

    #import json
    #print json.dumps(form.data, indent=3)

    # the code below will output only submitted values which were truthy
    # useful for debugging the form itself without getting lost in the
    # 57-field object that gets created
    #print
    #print
    #for field in form:
    #    #if field.data and field.data != 'None':
    #    if field.short_name == 'subject':
    #        print field.short_name, '::', field.data, ',', type(field.data)
    #print

    if request.method == 'POST':
        if not process_the_form:
            if existing_suggestion:
                # this is not a success, so we do not consider the success_url
                return redirect(url_for(redirect_route, suggestion_id=existing_suggestion.id, _anchor='cannot_edit'))
        else:
            if form.make_all_fields_optional.data:
                valid = True
            else:
                valid = form.validate()

            if valid:
                email_editor = False
                if group_editable:
                    email_editor = SuggestionFormXWalk.is_new_editor_group(form, existing_suggestion)

                email_associate = False
                if editorial_available:
                    email_associate = SuggestionFormXWalk.is_new_editor(form, existing_suggestion)

                # do the core crosswalk
                suggestion = SuggestionFormXWalk.form2obj(form, existing_suggestion)

                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                if not existing_suggestion:
                    suggestion.suggested_on = now
                    suggestion.set_application_status('pending')
                else:
                    # copy over any important fields from the previous version of the object
                    created_date = existing_suggestion.created_date if existing_suggestion.created_date else now
                    suggestion.set_created(created_date)
                    suggestion.suggested_on = existing_suggestion.suggested_on
                    suggestion.data['id'] = existing_suggestion.data['id']
                    if ((suggestion.owner is None or suggestion.owner == "") and (existing_suggestion.owner is not None)) or not current_user.has_role("admin"):
                        suggestion.set_owner(existing_suggestion.owner)

                    if not group_editable or not editorial_available:
                        suggestion.set_editor_group(existing_suggestion.editor_group)

                    if not editorial_available:
                        suggestion.set_editor(existing_suggestion.editor)

                    # FIXME: probably should check that the editor is in the editor_group and remove if not

                # the code below can be used to quickly debug objects which
                # fail to serialise as JSON - there should be none of those
                # in the suggestion!
                '''
                import json
                for thing in suggestion.data:
                    try:
                        if thing == 'bibjson':
                            bibjson = suggestion.bibjson().bibjson
                            for thing2 in bibjson:
                                try:
                                    print json.dumps(bibjson[thing2])
                                except TypeError as e:
                                    print 'This is it:',thing2
                                    print e
                                    print
                                    print json.dumps(bibjson[thing2])
                    except TypeError as e:
                        print 'This is it:',thing
                        print e
                        print
                '''

                # the code below produces a dump of the object returned by
                # the crosswalk
                '''
                import json
                print
                print
                print 'Now all the data!'

                print json.dumps(suggestion.data, indent=3)
                '''

                suggestion.save()
                if existing_suggestion:
                    flash('Application updated.', 'success')
                    if suggestion.application_status == 'accepted':
                        # this suggestion is just getting accepted
                        j = journal.suggestion2journal(suggestion)
                        j.set_in_doaj(True)
                        j.save()
                        qobj = j.make_query(q=j.id)
                        jurl = url_for('admin.admin_site_search') + '?source=' + json.dumps(qobj).replace('"', '&quot;')
                        flash_with_url('<a href="{url}" target="_blank">New journal created</a>.'.format(url=jurl), 'success')
                        owner = create_account_on_suggestion_approval(suggestion, j)
                        send_suggestion_approved_email(j.bibjson().title, owner.email)

                # only actually send the email when we've successfully processed the form
                if email_editor:
                    send_editor_group_email(suggestion)

                if email_associate:
                    send_editor_email(suggestion)

                if success_url:
                    return redirect(success_url)
                else:
                    return redirect(url_for(redirect_route, suggestion_id=suggestion.id, _anchor='done'))
            else:
                for field in form:  # in order of definition of fields, so the order of rendering should be (manually) kept the same as the order of definition for this to work
                    if field.errors:
                        first_field_with_error = field.short_name
                        break
    return render_template(
            template_name,
            form=form,
            first_field_with_error=first_field_with_error,
            q_numbers=xrange(1, 10000).__iter__(),  # a generator for the purpose of displaying numbered questions
            other_val=other_val,
            digital_archiving_policy_specific_library_value=digital_archiving_policy_specific_library_value,
            edit_suggestion_page=True,
            group_editable=group_editable,
            editorial_available=editorial_available,
            lock=lock,
            **kwargs
    )

SUGGESTION_ASSIGNED_GROUP_TEMPLATE = \
"""
Dear {editor},

A new application for the journal "{journal_name}" has been assigned to your Editor Group by a Managing Editor.
You may access the application in your Editor Area: {url_root}/editor/ .

The DOAJ Team
Twitter: https://twitter.com/DOAJplus
Facebook: http://www.facebook.com/DirectoryofOpenAccessJournals
LinkedIn: http://www.linkedin.com/company/directory-of-open-access-journals-doaj-
"""


def send_editor_group_email(suggestion):
    eg = models.EditorGroup.pull_by_key("name", suggestion.editor_group)
    if eg is None:
        return
    editor = models.Account.pull(eg.editor)

    url_root = app.config.get("BASE_URL")
    to = [editor.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - new journal assigned to your group"
    text = SUGGESTION_ASSIGNED_GROUP_TEMPLATE.format(editor=editor.id.encode('utf-8', 'replace'), journal_name=suggestion.bibjson().title.encode('utf-8', 'replace'), url_root=url_root)

    util.send_mail(to=to, fro=fro, subject=subject, text=text)

SUGGESTION_ASSIGNED_EDITOR_TEMPLATE = \
"""
Dear {editor},

A new application for the journal "{journal_name}" has been assigned to you by the Editor in your Editor Group "{group_name}".
You may access the application in your Editor Area: {url_root}/editor/ .

The DOAJ Team
Twitter: https://twitter.com/DOAJplus
Facebook: http://www.facebook.com/DirectoryofOpenAccessJournals
LinkedIn: http://www.linkedin.com/company/directory-of-open-access-journals-doaj-
"""

def send_editor_email(suggestion):
    editor = models.Account.pull(suggestion.editor)
    eg = models.EditorGroup.pull_by_key("name", suggestion.editor_group)

    url_root = app.config.get("BASE_URL")
    to = [editor.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - new journal assigned to you"
    text = SUGGESTION_ASSIGNED_EDITOR_TEMPLATE.format(editor=editor.id.encode('utf-8', 'replace'),
                                                   journal_name=suggestion.bibjson().title.encode('utf-8', 'replace'),
                                                   group_name=eg.name.encode("utf-8", "replace"), url_root=url_root)

    util.send_mail(to=to, fro=fro, subject=subject, text=text)

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

        if forms.interpret_special(form.processing_charges.data):
            bibjson.set_apc(form.processing_charges_currency.data, form.processing_charges_amount.data)

        if forms.interpret_special(form.submission_charges.data):
            bibjson.set_submission_charges(form.submission_charges_currency.data, form.submission_charges_amount.data)

        suggestion.set_articles_last_year(form.articles_last_year.data, form.articles_last_year_url.data)

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

        if form.metadata_provision.data and form.metadata_provision.data != 'None':
            suggestion.article_metadata = forms.interpret_special(form.metadata_provision.data)  # just binary

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
                    if formnote['note'] not in curnotes:
                        suggestion.add_note(formnote['note'])
                    # also generate another text index of notes, this time an index of the form notes
                    formnotes.append(formnote['note'])

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

        articles_last_year = obj.articles_last_year
        if articles_last_year:
            forminfo['articles_last_year'] = articles_last_year.get('count')
            forminfo['articles_last_year_url'] = articles_last_year.get('url')

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

        forminfo['metadata_provision'] = forms.reverse_interpret_special(obj.article_metadata)


        forminfo['download_statistics'] = forms.reverse_interpret_special(bibjson.article_statistics.get('statistics'))
        forminfo['download_statistics_url'] = bibjson.article_statistics.get('url')

        forminfo['first_fulltext_oa_year'] = bibjson.oa_start.get('year')

        # checkboxes
        forminfo['fulltext_format'], forminfo['fulltext_format_other'] = \
            forms.reverse_interpret_other(bibjson.format, forms.fulltext_format_choices_list)

        forminfo['keywords'] = bibjson.keywords

        forminfo['languages'] = bibjson.language

        forminfo['editorial_board_url'] = bibjson.get_single_url('editorial_board')

        forminfo['review_process'] = bibjson.editorial_review.get('process')
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
                forms.reverse_interpret_special(bibjson.author_copyright.get('copyright')),
                forms.ternary_choices_list
            )
        forminfo['copyright_url'] = bibjson.author_copyright.get('url')

        forminfo['publishing_rights'], forminfo['publishing_rights_other'] = \
            forms.reverse_interpret_other(
                forms.reverse_interpret_special(bibjson.author_publishing_rights.get('publishing_rights')),
                forms.ternary_choices_list
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