'''
This is the default app controller for portality.
For inclusion in your own project you should make your own version of this controller
and include the views you require, as well as writing new ones. Of course, views must 
also be backed up by models, so have a look at the example models and use them / write 
new ones as required too.
'''
import os

from flask import request, abort, render_template, redirect, send_file, url_for, flash
from flask.ext.login import login_user, current_user

import portality.models as models
from portality.core import app, login_manager
from portality import settings
from portality.util import flash_with_url

from portality.view.account import blueprint as account
from portality.view.admin import blueprint as admin
from portality.view.publisher import blueprint as publisher
from portality.view.query import blueprint as query
from portality.view.stream import blueprint as stream
from portality.view.forms import blueprint as forms
from portality.view.doaj import blueprint as doaj
from portality.view.oaipmh import blueprint as oaipmh
from portality.view.atom import blueprint as atom
from portality.view.editor import blueprint as editor
from portality.view.doajservices import blueprint as services

app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(publisher, url_prefix='/publisher')
app.register_blueprint(query, url_prefix='/query')
app.register_blueprint(query, url_prefix="/admin_query")
app.register_blueprint(query, url_prefix="/publisher_query")
app.register_blueprint(query, url_prefix="/editor_query")
app.register_blueprint(query, url_prefix="/associate_query")
app.register_blueprint(stream, url_prefix='/stream')
app.register_blueprint(forms, url_prefix='/forms')
app.register_blueprint(editor, url_prefix='/editor')
app.register_blueprint(services, url_prefix='/service')

app.register_blueprint(oaipmh)
app.register_blueprint(atom)
app.register_blueprint(doaj)

"""
FIXME: this needs to be sorted out - they shouldn't be in here and in doaj.py, but there is an issue
with the 404 pages which requires them
"""
import sys
try:
    if sys.version_info.major == 2 and sys.version_info.minor < 7:
        from portality.ordereddict import OrderedDict
except AttributeError:
    if sys.version_info[0] == 2 and sys.version_info[1] < 7:
        from portality.ordereddict import OrderedDict
    else:
        from collections import OrderedDict
else:
    from collections import OrderedDict
SPONSORS = {
        # the key should correspond to the sponsor logo name in
        # /static/doaj/images/sponsors without the extension for
        # consistency - no code should rely on this though
        'biomed-central': {'name':'BioMed Central', 'logo': 'biomed-central.gif', 'url': 'http://www.biomedcentral.com/'},
        'coaction': {'name': 'Co-Action Publishing', 'logo': 'coaction.gif', 'url': 'http://www.co-action.net/'},
        'cogent-oa': {'name': 'Cogent OA', 'logo': 'cogent-oa.gif', 'url': 'http://cogentoa.com/'},
        'copernicus': {'name': 'Copernicus Publications', 'logo': 'copernicus.gif', 'url': 'http://publications.copernicus.org/'},
        'frontiers': {'name': 'Frontiers', 'logo': 'frontiers.gif', 'url': 'http://www.frontiersin.org/'},
        'hindawi': {'name': 'Hindawi Publishing Corporation', 'logo': 'hindawi.jpg', 'url': 'http://www.hindawi.com/'},
        'inasp': {'name': 'International Network for the Availability of Scientific Publications (INASP)', 'logo': 'inasp.png', 'url': 'http://www.inasp.info/'},
        'lund-university': {'name': 'Lund University', 'logo': 'lund-university.jpg', 'url': 'http://www.lunduniversity.lu.se/'},
        'mdpi': {'name': 'Multidisciplinary Digital Publishing Institute (MDPI)', 'logo': 'mdpi.png', 'url': 'http://www.mdpi.com/'},
        'springer': {'name': 'Springer Science+Business Media', 'logo': 'springer.gif', 'url': 'http://www.springer.com/'},
        'taylor-and-francis': {'name': 'Taylor and Francis Group', 'logo': 'taylor-and-francis.gif', 'url': 'http://www.taylorandfrancisgroup.com/'},
        'karger-oa': {'name': 'Karger Open Access', 'logo': 'karger-oa.jpg', 'url': 'http://www.karger.com/OpenAccess'},
        'cottage-labs': {'name': 'Cottage Labs LLP', 'logo': 'cottagelabs.gif', 'url': 'http://cottagelabs.com'},
        'wiley': {'name': 'Wiley', 'logo': 'wiley.gif', 'url': 'http://wiley.com'},
}
SPONSORS = OrderedDict(sorted(SPONSORS.items(), key=lambda t: t[0])) # create an ordered dictionary, sort by the key of the unordered one


@app.route("/formcontext/<context_type>/<example>", methods=["GET", "POST"])
@app.route("/formcontext/<context_type>/<example>/<id>", methods=["GET", "POST"])
def formcontext(context_type, example, id=None):
    print context_type, example
    from portality.formcontext import formcontext
    fc = None

    if context_type == 'application':

        # public application form (DONE)
        if example == "public":
            if request.method == "GET":
                fc = formcontext.ApplicationFormFactory.get_form_context()
                return fc.render_template(edit_suggestion_page=True)
            elif request.method == "POST":
                fc = formcontext.ApplicationFormFactory.get_form_context(form_data=request.form)
                if fc.validate():
                    fc.finalise()
                    return redirect(url_for('doaj.suggestion_thanks', _anchor='thanks'))
                else:
                    return fc.render_template(edit_suggestion_page=True)

        # managing editor's application form (DONE)
        elif example == "admin":
            ap = models.Suggestion.pull(id)
            if request.method == "GET":
                fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=ap)
                return fc.render_template(edit_suggestion_page=True)
            elif request.method == "POST":
                fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", form_data=request.form, source=ap)
                if fc.validate():
                    try:
                        fc.finalise()
                        flash('Application updated.', 'success')
                        for a in fc.alert:
                            flash_with_url(a, "success")
                        return redirect(url_for("admin.suggestion_page", suggestion_id=ap.id, _anchor='done'))
                    except formcontext.FormContextException as e:
                        flash(e.message)
                        return redirect(url_for("admin.suggestion_page", suggestion_id=ap.id, _anchor='cannot_edit'))
                else:
                    return fc.render_template(edit_suggestion_page=True)

        # editor's application form (DONE)
        elif example == "editor":
            ap = models.Suggestion.pull(id)
            if request.method == "GET":
                fc = formcontext.ApplicationFormFactory.get_form_context(role="editor", source=ap)
                return fc.render_template(edit_suggestion_page=True)
            elif request.method == "POST":
                fc = formcontext.ApplicationFormFactory.get_form_context(role="editor", form_data=request.form, source=ap)
                if fc.validate():
                    try:
                        fc.finalise()
                        flash('Application updated.', 'success')
                        for a in fc.alert:
                            flash_with_url(a, "success")
                        return redirect(url_for("editor.suggestion_page", suggestion_id=ap.id, _anchor='done'))
                    except formcontext.FormContextException as e:
                        flash(e.message)
                        return redirect(url_for("editor.suggestion_page", suggestion_id=ap.id, _anchor='cannot_edit'))
                else:
                    return fc.render_template(edit_suggestion_page=True)

        # associate editor's application form (DONE)
        elif example == "associate_editor":
            ap = models.Suggestion.pull(id)
            if request.method == "GET":
                fc = formcontext.ApplicationFormFactory.get_form_context(role="associate_editor", source=ap)
                return fc.render_template(edit_suggestion_page=True)
            elif request.method == "POST":
                fc = formcontext.ApplicationFormFactory.get_form_context(role="associate_editor", form_data=request.form, source=ap)
                if fc.validate():
                    try:
                        fc.finalise()
                        flash('Application updated.', 'success')
                        for a in fc.alert:
                            flash_with_url(a, "success")
                        return redirect(url_for("editor.suggestion_page", suggestion_id=ap.id, _anchor='done'))
                    except formcontext.FormContextException as e:
                        flash(e.message)
                        return redirect(url_for("editor.suggestion_page", suggestion_id=ap.id, _anchor='cannot_edit'))
                else:
                    return fc.render_template(edit_suggestion_page=True)

        # publisher's re-application form (DONE)
        elif example == "publisher":
            ap = models.Suggestion.pull(id)
            if request.method == "GET":
                fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=ap)
                return fc.render_template(edit_suggestion_page=True)
            elif request.method == "POST":
                fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", form_data=request.form, source=ap)
                if fc.validate():
                    try:
                        fc.finalise()
                        flash('Re-application updated.', 'success')
                        for a in fc.alert:
                            flash_with_url(a, "success")
                        return redirect(url_for("publisher.reapplication_page", suggestion_id=ap.id, _anchor='done'))
                    except formcontext.FormContextException as e:
                        flash(e.message)
                        return redirect(url_for("publisher.reapplication_page", suggestion_id=ap.id, _anchor='cannot_edit'))
                else:
                    return fc.render_template(edit_suggestion_page=True)

    elif context_type == 'journal':
        if example == 'admin':
            ap = models.Journal.pull(id)
            if request.method == "GET":
                fc = formcontext.JournalFormFactory.get_form_context(role="admin", source=ap)
                return fc.render_template(edit_suggestion_page=True)  # TODO change param
            elif request.method == "POST":
                fc = formcontext.JournalFormFactory.get_form_context(role="admin", form_data=request.form, source=ap)
                if fc.validate():
                    try:
                        fc.finalise()
                        flash('Journal updated.', 'success')
                        for a in fc.alert:
                            flash_with_url(a, "success")
                        return redirect(url_for("admin.suggestion_page", journal_id=ap.id, _anchor='done'))  # TODO change url target
                    except formcontext.FormContextException as e:
                        flash(e.message)
                        return redirect(url_for("admin.suggestion_page", journal_id=ap.id, _anchor='cannot_edit'))  # TODO change URL target
                else:
                    return fc.render_template(edit_suggestion_page=True)  # TODO change param
        elif example == 'editor':
            pass
        elif example == 'associate_editor':
            pass

    abort(404)

# Redirects from previous DOAJ app.
# RJ: I have decided to put these here so that they can be managed 
# alongside the DOAJ codebase.  I know they could also go into the
# nginx config, but there is a chance that they will get lost or forgotten
# some day, whereas this approach doesn't have that risk.
@app.route("/doaj")
def legacy():
    func = request.values.get("func")
    if func == "csv":
        return redirect(url_for('doaj.csv_data')), 301
    elif func == "rss":
        return redirect(url_for('atom.feed')), 301
    elif func == "browse" or func == 'byPublicationFee  ':
        return redirect(url_for('doaj.search')), 301
    abort(404)

@app.route("/doaj2csv")
def another_legacy_csv_route():
    return redirect("/csv"), 301

@app.route("/schemas/doajArticles.xsd")
def legacy_doaj_XML_schema():
    schema_fn = 'doajArticles.xsd'
    return send_file(
            os.path.join(app.config.get("STATIC_DIR"), "doaj", schema_fn),
            mimetype="application/xml", as_attachment=True, attachment_filename=schema_fn
            )

@login_manager.user_loader
def load_account_for_login_manager(userid):
    out = models.Account.pull(userid)
    return out

# FIXME: this used to calculate the site stats on request, but for the time being
# this is an unnecessary overhead, so taking it out.  Will need to put something
# equivalent back in when we do the admin area
@app.context_processor
def set_current_context():
    """ Set some template context globals. """
    '''
    Inserts variables into every template this blueprint renders.  This
    one deals with the announcement in the header, which can't be built
    into the template directly, as various styles are applied only if a
    header is present on the page. It also makes the list of DOAJ
    sponsors available and may include similar minor pieces of
    information.
    '''
    return {
        'heading_title': '',
        'heading_text': '',
        'sponsors': SPONSORS,
        'settings': settings,
        'statistics' : models.JournalArticle.site_statistics(),
        "current_user": current_user,
        "app" : app
        }
    # return dict(current_user=current_user, app=app)

@app.before_request
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    if remote_user:
        user = models.Account.pull(remote_user)
        if user:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif 'api_key' in request.values:
        res = models.Account.query(q='api_key:"' + request.values['api_key'] + '"')['hits']['hits']
        if len(res) == 1:
            user = models.Account.pull(res[0]['_source']['id'])
            if user:
                login_user(user, remember=False)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(401)
def page_not_found(e):
    return render_template('401.html'), 401
        

if __name__ == "__main__":
    pycharm_debug = app.config.get('DEBUG_PYCHARM', False)
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d':
            pycharm_debug = True

    if pycharm_debug:
        app.config['DEBUG'] = False
        import pydevd
        pydevd.settrace(app.config.get('DEBUG_PYCHARM_SERVER', 'localhost'), port=app.config.get('DEBUG_PYCHARM_PORT', 6000), stdoutToServer=True, stderrToServer=True)

    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=app.config['PORT'])
