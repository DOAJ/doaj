import json
from datetime import datetime

from flask import Blueprint, request, flash, abort, make_response
from flask import render_template, redirect, url_for
from flask.ext.login import current_user, login_required

from portality.core import app, ssl_required, restrict_to_role
import portality.models as models
from portality.suggestion import suggestion_form, SuggestionFormXWalk
from portality.journal import JournalFormXWalk
import portality.util as util
from portality import xwalk
from portality.view.forms import JournalForm, SuggestionForm, \
    EditSuggestionForm, subjects2str, other_val, \
    digital_archiving_policy_specific_library_value
from portality.datasets import country_options_two_char_code_index
from portality.lcc import lcc_jstree


blueprint = Blueprint('admin', __name__)

# restrict everything in admin to logged in users with the "admin" role
@blueprint.before_request
def restrict():
    return restrict_to_role('admin')

# build an admin page where things can be done
@blueprint.route('/')
@login_required
@ssl_required
def index():
    return render_template('admin/index.html', admin_page=True)

@blueprint.route("/journals")
@login_required
@ssl_required
def journals():
    if not current_user.has_role("admin_journals"):
        abort(401)
    return render_template('admin/journals.html',
               search_page=True,
               facetviews=['journals'],
               admin_page=True
           )


def get_journal(journal_id):
    if not current_user.has_role("edit_journal"):
        abort(401)
    j = models.Journal.pull(journal_id)
    if j is None:
        abort(404)
    return j

@blueprint.route("/article/<article_id>", methods=["POST"])
@login_required
@ssl_required
def article_endpoint(article_id):
    if not current_user.has_role("delete_article"):
        abort(401)
    a = models.Article.pull(article_id)
    if a is None:
        abort(404)
    delete = request.values.get("delete", "false")
    if delete != "true":
        abort(400)
    a.snapshot()
    a.delete()
    # return a json response
    resp = make_response(json.dumps({"success" : True}))
    resp.mimetype = "application/json"
    return resp

@blueprint.route("/journal/<journal_id>", methods=["GET", "POST"])
@login_required
@ssl_required
def journal_page(journal_id):
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
        form.publisher.description = 'Full contents: ' + form.publisher.data

    if form.society_institution.data:
        form.society_institution.description = 'Full contents: ' + form.society_institution.data

    if form.platform.data:
        form.platform.description = 'Full contents: ' + form.platform.data

    first_field_with_error = ''

    if request.method == 'POST':
        if form.make_all_fields_optional.data:
            valid = True
        else:
            valid = form.validate()
        if valid:
            # even though you can only edit journals right now, keeping the same
            # method as editing suggestions (i.e. creating a new object
            # and editing its properties)

            # some of the properties (id, in_doaj, etc.) have to be carried over
            # otherwise they implicitly end up getting changed to their defaults
            # when a journal gets edited (e.g. it always gets taken out of DOAJ)
            # if we don't copy over the in_doaj attribute to the new journal object
            journal = JournalFormXWalk.form2obj(form, existing_journal=j)
            journal['id'] = j['id']
            created_date = j.created_date if j.created_date else datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            journal.set_created(created_date)
            journal.bibjson().active = j.is_in_doaj()
            journal.set_in_doaj(j.is_in_doaj())
            journal.save()
            flash('Journal updated.', 'success')
            return redirect(url_for('.journal_page', journal_id=journal_id, _anchor='done'))
                # meaningless anchor to replace #first_problem used on the form
                # anchors persist between 3xx redirects to the same resource
        else:
            for field in form:  # in order of definition of fields, so the order of rendering should be (manually) kept the same as the order of definition for this to work
                if field.errors:
                    first_field_with_error = field.short_name
                    break

    return render_template(
            "admin/journal.html",
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
    )

@blueprint.route("/journal/<journal_id>/activate", methods=["GET", "POST"])
@login_required
@ssl_required
def journal_activate(journal_id):
    j = get_journal(journal_id)
    j.bibjson().active = True
    j.set_in_doaj(True)
    j.save()
    j.propagate_in_doaj_status_to_articles()  # will save each article, could take a while
    return redirect(url_for('.journal_page', journal_id=journal_id))

@blueprint.route("/journal/<journal_id>/deactivate", methods=["GET", "POST"])
@login_required
@ssl_required
def journal_deactivate(journal_id):
    j = get_journal(journal_id)
    j.bibjson().active = False
    j.set_in_doaj(False)
    j.save()
    j.propagate_in_doaj_status_to_articles()  # will save each article, could take a while
    return redirect(url_for('.journal_page', journal_id=journal_id))

@blueprint.route("/applications")
@login_required
@ssl_required
def suggestions():
    return render_template('admin/suggestions.html',
               search_page=True,
               facetviews=['suggestions'],
               admin_page=True
           )

@blueprint.route("/suggestion/<suggestion_id>", methods=["GET", "POST"])
@login_required
@ssl_required
def suggestion_page(suggestion_id):
    if not current_user.has_role("edit_suggestion"):
        abort(401)
    s = models.Suggestion.pull(suggestion_id)
    if s is None:
        abort(404)

    current_info = models.ObjectDict(SuggestionFormXWalk.obj2form(s))
    form = EditSuggestionForm(request.form, current_info)

    process_the_form = True
    if request.method == 'POST' and s.application_status == 'accepted':
        flash('You cannot edit suggestions which have been accepted into DOAJ.', 'error')
        process_the_form = False

    # add the contents of a few fields to their descriptions since select2 autocomplete
    # would otherwise obscure the full values
    if form.publisher.data:
        if not form.publisher.description:
            form.publisher.description = 'Full contents: ' + form.publisher.data
        else:
            form.publisher.description = '<br><br>Full contents: ' + form.publisher.data

    if form.society_institution.data:
        if not form.society_institution.description:
            form.society_institution.description = 'Full contents: ' + form.society_institution.data
        else:
            form.society_institution.description = '<br><br>Full contents: ' + form.society_institution.data

    if form.platform.data:
        if not form.platform.description:
            form.platform.description = 'Full contents: ' + form.platform.data
        else:
            form.platform.description = '<br><br>Full contents: ' + form.platform.data

    redirect_url_on_success = url_for('.suggestion_page', suggestion_id=suggestion_id, _anchor='done')
    # meaningless anchor to replace #first_problem used on the form
    # anchors persist between 3xx redirects to the same resource
    # (/application)

    return suggestion_form(form, request, redirect_url_on_success, "admin/suggestion.html",
                           existing_suggestion=s,
                           suggestion=s,
                           process_the_form=process_the_form,
                           admin_page=True,
                           subjectstr=subjects2str(s.bibjson().subjects()),
                           lcc_jstree=json.dumps(lcc_jstree),
    )

@blueprint.route("/admin_site_search")
@login_required
@ssl_required
def admin_site_search():
    return render_template("admin/admin_site_search.html", admin_page=True, search_page=True, facetviews=['admin_journals_and_articles'])
