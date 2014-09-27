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
from portality import app_email
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
        return render_template(locked_template, suggestion=s, lock=l.lock, edit_suggestion_page=True)

    current_info = models.ObjectDict(SuggestionFormXWalk.obj2form(s))
    form = EditSuggestionForm(request.form, current_info)

    if status_options == "admin":
        form.application_status.choices = forms.application_status_choices_admin
    else:
        form.application_status.choices = forms.application_status_choices_editor

    process_the_form = True
    if request.method == 'POST' and s.application_status == 'accepted':
        flash('You cannot edit applications which have been accepted into DOAJ.', 'error')
        process_the_form = False

    if form.application_status.data == "accepted" and form.make_all_fields_optional.data:
        flash("You cannot accept an application into the DOAJ without fully validating it", "error")
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
            #if form.make_all_fields_optional.data:
            #    valid = True
            #else:
            #    valid = form.validate()
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
                        print "field with error", first_field_with_error
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

def send_editor_group_email(suggestion):
    eg = models.EditorGroup.pull_by_key("name", suggestion.editor_group)
    if eg is None:
        return
    editor = models.Account.pull(eg.editor)

    url_root = app.config.get("BASE_URL")
    to = [editor.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - new journal assigned to your group"

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/suggestion_assigned_group.txt",
                        editor=editor.id.encode('utf-8', 'replace'),
                        journal_name=suggestion.bibjson().title.encode('utf-8', 'replace'),
                        url_root=url_root
                        )


def send_editor_email(suggestion):
    editor = models.Account.pull(suggestion.editor)
    eg = models.EditorGroup.pull_by_key("name", suggestion.editor_group)

    url_root = app.config.get("BASE_URL")
    to = [editor.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - new journal assigned to you"

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/suggestion_assigned_editor.txt",
                        editor=editor.id.encode('utf-8', 'replace'),
                        journal_name=suggestion.bibjson().title.encode('utf-8', 'replace'),
                        group_name=eg.name.encode("utf-8", "replace"),
                        url_root=url_root
                        )


