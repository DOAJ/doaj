import json

from flask import Blueprint, request, flash, abort, make_response
from flask import render_template, redirect, url_for
from flask.ext.login import current_user, login_required

from portality.core import app, ssl_required, restrict_to_role
import portality.models as models
import portality.util as util
from portality import xwalk
from portality.view.forms import JournalForm
from portality.view.account import get_redirect_target
from portality.datasets import country_options_two_char_code_index


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
    return render_template('admin/journals.html',
               search_page=True,
               facetviews=['journals'],
               admin_page=True
           )

@blueprint.route("/journal/<journal_id>", methods=["GET", "POST"])
@login_required
@ssl_required
def journal_page(journal_id):
    if not current_user.has_role("edit_journal"):
        abort(401)
    j = models.Journal.pull(journal_id)
    if j is None:
        abort(404)

    current_country = xwalk.get_country_code(j.bibjson().country)

    if current_country not in country_options_two_char_code_index:
        # couldn't find it, better warn the user to look for it
        # themselves
        country_help_text = "This journal's country has been recorded as \"{country}\". Please select it in the Country menu.".format(country=current_country)
    else:
        country_help_text = ''

    current_info = {
        'in_doaj': j.is_in_doaj(),
        'url': j.bibjson().get_single_url(urltype='homepage'),
        'title': j.bibjson().title,
        'alternative_title': j.bibjson().alternative_title,
        'pissn': j.bibjson().get_one_identifier(j.bibjson().P_ISSN),
        'eissn': j.bibjson().get_one_identifier(j.bibjson().E_ISSN),
        'publisher': j.bibjson().publisher,
        'provider': j.bibjson().provider,
        'oa_start_year': j.bibjson().oa_start.get('year', ''),
        'oa_end_year': j.bibjson().oa_end.get('year', ''),
        'country': current_country,
        'license': j.bibjson().get_license_type(),
        'author_pays': j.bibjson().author_pays,
        'author_pays_url': j.bibjson().author_pays_url,
        'keywords': j.bibjson().keywords,
        'languages': j.bibjson().language,
    }

    form = JournalForm(request.form, **current_info)
    form.country.description = '<span class="red">' + country_help_text + '</span>'

    there_were_errors = False
    if request.method == 'POST':
        if form.validate():
            nj = j
            nj.bibjson().active = form.in_doaj.data
            nj.set_in_doaj(form.in_doaj.data)
            nj.bibjson().update_url(form.url.data, 'homepage')
            nj.bibjson().title = form.title.data
            nj.bibjson().alternative_title = form.alternative_title.data
            nj.bibjson().update_identifier(nj.bibjson().P_ISSN, form.pissn.data)
            nj.bibjson().update_identifier(nj.bibjson().E_ISSN, form.eissn.data)
            nj.bibjson().publisher = form.publisher.data
            nj.bibjson().provider = form.provider.data
            nj.bibjson().set_oa_start(year=form.oa_start_year.data)
            nj.bibjson().set_oa_end(year=form.oa_end_year.data)
            nj.bibjson().country = form.country.data
            nj.bibjson().set_license(license_title=form.license.data, license_type=form.license.data)
            nj.bibjson().author_pays = form.author_pays.data
            nj.bibjson().author_pays_url = form.author_pays_url.data
            nj.bibjson().set_keywords(form.keywords.data)
            nj.bibjson().set_language(form.languages.data)
            nj.save()
            return redirect(url_for('admin.journal_page', journal_id=journal_id))  # observe the POST->redirect pattern
        else:
            there_were_errors = True

    subject_strings = []
    for sub in j.bibjson().subjects():
        subject_strings.append('[{scheme}] {term}'.format(scheme=sub.get('scheme'), term=sub.get('term')))
    subject_final_str = ', '.join(subject_strings)

    return render_template("admin/journal.html", form=form, journal=j, admin_page=True, subject=subject_final_str, there_were_errors=there_were_errors)

@blueprint.route("/suggestions")
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
        
    if request.method == "GET":
        return render_template("admin/suggestion.html", suggestion=s, admin_page=True, edit_suggestion_page=True)

    elif request.method == "POST":
        req = json.loads(request.data)
        new_status = req.get("status")
        s.set_application_status(new_status)
        s.save()
        return "", 204


