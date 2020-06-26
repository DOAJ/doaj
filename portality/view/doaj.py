from flask import Blueprint, request, flash, make_response
from flask import render_template, abort, redirect, url_for, send_file, jsonify
from flask_login import current_user, login_required
import urllib.request, urllib.parse, urllib.error
from jinja2.exceptions import TemplateNotFound

from portality import dao
from portality import models
from portality import blog
from portality.core import app
from portality.decorators import ssl_required, write_required
from portality.formcontext import formcontext
from portality.lcc import lcc_jstree
from portality.view.forms import ContactUs
from portality.app_email import send_contact_form
from portality.lib import analytics
from portality.ui.messages import Messages

import json
import os

blueprint = Blueprint('doaj', __name__)


@blueprint.route("/")
def home():
    news = blog.News.latest(app.config.get("FRONT_PAGE_NEWS_ITEMS", 5))
    return render_template('doaj/index.html', news=news)

@blueprint.route('/login/')
def login():
    return redirect(url_for('account.login'))

@blueprint.route("/cookie_consent")
def cookie_consent():
    cont = request.values.get("continue")
    if cont is not None:
        resp = redirect(cont)
    else:
        resp = make_response()
    # set a cookie that lasts for one year
    resp.set_cookie(app.config.get("CONSENT_COOKIE_KEY"), Messages.CONSENT_COOKIE_VALUE, max_age=31536000)
    return resp


@blueprint.route("/news")
def news():
    news = blog.News.latest(app.config.get("NEWS_PAGE_NEWS_ITEMS", 20))
    return render_template('doaj/news.html', news=news, blog_url=app.config.get("BLOG_URL"))


# @blueprint.route("/widgets")
# def widgets():
#     return render_template('doaj/widgets.html',
#                            env=app.config.get("DOAJENV"),
#                            widget_filename_suffix='' if app.config.get('DOAJENV') == 'production' else '_' + app.config.get('DOAJENV', '')
#                            )

@blueprint.route("/ssw_demo")
def ssw_demo():
    return render_template('doaj/ssw_demo.html',
                           env=app.config.get("DOAJENV"),
                           widget_filename_suffix='' if app.config.get('DOAJENV') == 'production' else '_' + app.config.get('DOAJENV', '')
                           )

@blueprint.route("/fqw_demo")
def fqw_demo():
    return render_template('doaj/fqw_demo.html',
                           env=app.config.get("DOAJENV"),
                           widget_filename_suffix='' if app.config.get('DOAJENV') == 'production' else '_' + app.config.get('DOAJENV', '')
                           )



@blueprint.route("/fqw_hit", methods=['POST'])
def fqw_hit():
    page = request.form.get('embedding_page')
    if page is not None:
        fqw_event = analytics.GAEvent(
            category=app.config.get('GA_CATEGORY_FQW', 'FQW'),
            action=app.config.get('GA_ACTION_FQW', 'hit'),
            label=request.form.get('embedding_page')
        )
        fqw_event.submit()

    # No content response, whether data there or not.
    return '', 204

@blueprint.route("/search", methods=['GET'])
def search():
    return render_template('doaj/search.html')


@blueprint.route("/search", methods=['POST'])
def search_post():
    """ Redirect a query from the box on the index page to the search page. """
    if request.form.get('origin') != 'ui':
        abort(400)                                              # bad request - we must receive searches from our own UI

    filters = None
    if not (request.form.get('include_journals') and request.form.get('include_articles')):
        filters = []
        if request.form.get('include_journals'):
            filters.append(dao.Facetview2.make_term_filter("_type", "journal"))
        elif request.form.get('include_articles'):
            filters.append(dao.Facetview2.make_term_filter("_type", "article"))

    query = dao.Facetview2.make_query(request.form.get("q"), filters=filters, default_operator="AND")
    ref = request.form.get("ref")
    if ref is None:
        abort(400)                                                                                # Referrer is required
    else:
        return redirect(url_for('.search') + '?source=' + urllib.parse.quote(json.dumps(query)) + "&ref=" + urllib.parse.quote(ref))


@blueprint.route("/subjects")
def subjects():
    return render_template("doaj/subjects.html", subject_page=True, lcc_jstree=json.dumps(lcc_jstree))


"""
@blueprint.route("/application/new", methods=["GET", "POST"])
@write_required()
def suggestion():
    if request.method == "GET":
        fc = formcontext.ApplicationFormFactory.get_form_context()
        return fc.render_template(edit_suggestion_page=True)
    elif request.method == "POST":
        fc = formcontext.ApplicationFormFactory.get_form_context(form_data=request.form)
        if fc.validate():
            fc.finalise()
            return redirect(url_for('doaj.application_thanks', _anchor='thanks'))
        else:
            return fc.render_template(edit_suggestion_page=True)
"""

from portality.forms.application_forms import ApplicationFormFactory

@blueprint.route("/application/new", methods=["GET", "POST"])
@blueprint.route("/application/new/<draft_id>", methods=["GET", "POST"])
@write_required()
@login_required
def public_application(draft_id=None):
    fc = ApplicationFormFactory.context("public")

    if request.method == "GET":
        if draft_id is None:
            return fc.render_template()
        draft_application = models.DraftApplication.pull(draft_id)
        if draft_application is None:
            abort(404)
        if draft_application.owner != current_user.id:
            abort(404)
        fc.processor(source=draft_application)
        return fc.render_template(obj=draft_application)

    elif request.method == "POST":
        draft = request.form.get("draft")
        async_def = request.form.get("async")
        processor = fc.processor(formdata=request.form)

        if draft is not None:
            draft_application = None
            if draft_id is not None:
                draft_application = models.DraftApplication.pull(draft_id)
                if draft_application is None:
                    abort(404)
                if draft_application.owner != current_user.id:
                    abort(404)

            draft_application = processor.draft(current_user._get_current_object(), id=draft_id)
            if async_def is not None:
                return make_response(json.dumps({"id": draft_application.id}), 200)
            else:
                return redirect(url_for('doaj.draft_saved'))
        else:
            if processor.validate():
                processor.finalise(current_user._get_current_object())
                return redirect(url_for('doaj.application_thanks'))
            else:
                return fc.render_template()


#############################################

@blueprint.route("/journal/readonly/<journal_id>", methods=["GET"])
@login_required
@ssl_required
def journal_readonly(journal_id):
    if (
        not current_user.has_role("admin")
        or not current_user.has_role("editor")
        or not current_user.has_role("associate_editor")
    ):
        abort(401)

    j = models.Journal.pull(journal_id)
    if j is None:
        abort(404)

    fc = formcontext.JournalFormFactory.get_form_context(role='readonly', source=j)
    return fc.render_template(edit_journal_page=True)


@blueprint.route("/application/thanks", methods=["GET"])
def application_thanks():
    return render_template('doaj/application_thanks.html')


@blueprint.route("/application/draft", methods=["GET"])
def draft_saved():
    return render_template("doaj/draft_saved.html")


@blueprint.route("/csv")
@analytics.sends_ga_event(event_category=app.config.get('GA_CATEGORY_JOURNALCSV', 'JournalCSV'), event_action=app.config.get('GA_ACTION_JOURNALCSV', 'Download'))
def csv_data():
    csv_info = models.Cache.get_latest_csv()
    if csv_info is None:
        abort(404)
    store_url = csv_info.get("url")
    if store_url is None:
        abort(404)
    if store_url.startswith("/"):
        store_url = "/store" + store_url
    return redirect(store_url, code=307)


@blueprint.route("/sitemap.xml")
def sitemap():
    sitemap_file = models.Cache.get_latest_sitemap()
    sitemap_path = os.path.join(app.config.get("CACHE_DIR"), "sitemap", sitemap_file)
    return send_file(sitemap_path, mimetype="application/xml", as_attachment=False, attachment_filename="sitemap.xml")


# @blueprint.route("/public-data-dump")
# def public_data_dump():
#     data_dump = models.Cache.get_public_data_dump()
#     show_article = data_dump.get("article", {}).get("url") is not None
#     article_size = data_dump.get("article", {}).get("size")
#     show_journal = data_dump.get("journal", {}).get("url") is not None
#     journal_size = data_dump.get("journal", {}).get("size")
#     return render_template("doaj/public_data_dump.html",
#                            show_article=show_article,
#                            article_size=article_size,
#                            show_journal=show_journal,
#                            journal_size=journal_size)


@blueprint.route("/public-data-dump/<record_type>")
def public_data_dump_redirect(record_type):
    store_url = models.Cache.get_public_data_dump().get(record_type, {}).get("url")
    if store_url is None:
        abort(404)
    if store_url.startswith("/"):
        store_url = "/store" + store_url
    return redirect(store_url, code=307)


@blueprint.route("/store/<container>/<filename>")
def get_from_local_store(container, filename):
    if not app.config.get("STORE_LOCAL_EXPOSE", False):
        abort(404)

    from portality import store
    localStore = store.StoreFactory.get(None)
    file_handle = localStore.get(container, filename)
    return send_file(file_handle, mimetype="application/octet-stream", as_attachment=True, attachment_filename=filename)


@blueprint.route('/autocomplete/<doc_type>/<field_name>', methods=["GET", "POST"])
def autocomplete(doc_type, field_name):
    prefix = request.args.get('q', '')
    if not prefix:
        return jsonify({'suggestions': [{"id": "", "text": "No results found"}]})  # select2 does not understand 400, which is the correct code here...

    m = models.lookup_model(doc_type)
    if not m:
        return jsonify({'suggestions': [{"id": "", "text": "No results found"}]})  # select2 does not understand 404, which is the correct code here...

    size = request.args.get('size', 5)

    filter_field = app.config.get("AUTOCOMPLETE_ADVANCED_FIELD_MAPS", {}).get(field_name)

    suggs = []
    if filter_field is None:
        suggs = m.autocomplete(field_name, prefix, size=size)
    else:
        suggs = m.advanced_autocomplete(filter_field, field_name, prefix, size=size, prefix_only=False)

    return jsonify({'suggestions': suggs})
    # you shouldn't return lists top-level in a JSON response:
    # http://flask.pocoo.org/docs/security/#json-security

@blueprint.route("/toc/<identifier>")
@blueprint.route("/toc/<identifier>/<volume>")
@blueprint.route("/toc/<identifier>/<volume>/<issue>")
def toc(identifier=None, volume=None, issue=None):
    # identifier may be the journal id or an issn
    journal = None
    issn_ref = False

    if identifier is None:
        abort(404)

    if len(identifier) == 9:
        js = models.Journal.find_by_issn(identifier, in_doaj=True)

        if len(js) > 1:
            abort(400)  # really this is a 500 - we have more than one journal with this issn
        if len(js) == 0:
            abort(404)
        journal = js[0]

        if journal is None:
            abort(400)

        issn_ref = True  # just a flag so we can check if we were requested via issn
    elif len(identifier) == 32:
        js = models.Journal.pull(identifier)  # Returns None on fail

        if js is None or not js.is_in_doaj():
            abort(404)
        journal = js
    else:
        abort(400)

    # get the bibjson record that we're going to render
    bibjson = journal.bibjson()

    # The issn we are using to build the TOC
    issn = bibjson.get_preferred_issn()

    # now redirect to the canonical E-ISSN if one is available

    if issn_ref:  # the journal is referred to by an ISSN
        # if there is an E-ISSN (and it's not the one in the request), redirect to it
        eissn = bibjson.get_one_identifier(bibjson.E_ISSN)
        if eissn and identifier != eissn:
            return redirect(url_for('doaj.toc', identifier=eissn, volume=volume, issue=issue), 301)

        # if there's no E-ISSN, but there is a P-ISSN (and it's not the one in the request), redirect to the P-ISSN
        if not eissn:
            pissn = bibjson.get_one_identifier(bibjson.P_ISSN)
            if pissn and identifier != pissn:
                return redirect(url_for('doaj.toc', identifier=pissn, volume=volume, issue=issue), 301)

        # Add the volume and issue to query if present in path
        if volume:
            filters = [dao.Facetview2.make_term_filter('bibjson.journal.volume.exact', volume)]
            if issue:
                filters += [dao.Facetview2.make_term_filter('bibjson.journal.number.exact', issue)]
            q = dao.Facetview2.make_query(filters=filters)

            return redirect(url_for('doaj.toc', identifier=issn) + '?source=' + dao.Facetview2.url_encode_query(q))

        # The journal has neither a PISSN or an EISSN. Yet somehow
        # issn_ref is True, the request was referring to the journal
        # by its ISSN. Not sure how this could ever happen, but just
        # continue loading the data and do nothing else in such a
        # case.

    else:  # the journal is NOT referred to by any ISSN

        # if there is an E-ISSN, redirect to it
        # if not, but there is a P-ISSN, redirect to it
        # if neither ISSN is present, continue loading the page
        issn = bibjson.get_one_identifier(bibjson.E_ISSN)
        if not issn:
            issn = bibjson.get_one_identifier(bibjson.P_ISSN)
        if issn:
            return redirect(url_for('doaj.toc', identifier=issn, volume=volume, issue=issue), 301)

        # let it continue loading if we only have the hex UUID for the journal (no ISSNs)
        # and the user is referring to the toc page via that ID

    # get the continuations for this journal, future and past
    future_journals = journal.get_future_continuations()
    past_journals = journal.get_past_continuations()

    # extract the bibjson, which is what the template is after, and whether the record is in doaj
    #future = [j.bibjson() j for j in future_journals]
    #past = [j.bibjson() for j in past_journals]

    # now render all that information
    return render_template('doaj/toc.html', journal=journal, bibjson=bibjson, future=future_journals, past=past_journals,
                           toc_issns=journal.bibjson().issns())


@blueprint.route("/article/<identifier>")
def article_page(identifier=None):
    # identifier must be the article id
    article = models.Article.pull(identifier)

    if article is None or not article.is_in_doaj():
        abort(404)

    # find the related journal record
    journal = None
    issns = article.bibjson().issns()
    more_issns = article.bibjson().journal_issns
    for issn in issns + more_issns:
        journals = models.Journal.find_by_issn(issn)
        if len(journals) > 0:
            journal = journals[0]

    return render_template('doaj/article.html', article=article, journal=journal)

@blueprint.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "GET":
        form = ContactUs()
        if current_user.is_authenticated:
            form.email.data = current_user.email
        return render_template("doaj/contact.html", form=form)
    elif request.method == "POST":
        prepop = request.values.get("ref")
        form = ContactUs(request.form)

        if current_user.is_authenticated and (form.email.data is None or form.email.data == ""):
            form.email.data = current_user.email

        if prepop is not None:
            return render_template("doaj/contact.html", form=form)

        if not form.validate():
            return render_template("doaj/contact.html", form=form)

        data = _verify_recaptcha(form.recaptcha_value.data)
        if data["success"]:
            send_contact_form(form)
            flash("Thank you for your feedback which has been received by the DOAJ Team.", "success")
            form = ContactUs()
            return render_template("doaj/contact.html", form=form)
        else:
            flash("Your form could not be submitted,", "error")
            return render_template("doaj/contact.html", form=form)

def _verify_recaptcha(g_recaptcha_response):
    with urllib.request.urlopen('https://www.google.com/recaptcha/api/siteverify?secret=' + app.config.get("RECAPTCHA_SECRET_KEY") + '&response=' + g_recaptcha_response) as url:
        data = json.loads(url.read().decode())
        return data

@app.route('/get_site_key')
def get_site_key():
    return app.config.get('RECAPTCHA_SITE_KEY')
###############################################################
# The various static endpoints
###############################################################


@blueprint.route("/googlebdb21861de30fe30.html")
def google_webmaster_tools():
    return 'google-site-verification: googlebdb21861de30fe30.html'


@blueprint.route("/support/")
def support():
    return render_template("layouts/static_page.html", page_frag="/support/index-fragment/index.html")


@blueprint.route("/sponsorship/")
def sponsors():
    return render_template("layouts/static_page.html", page_frag="support/sponsors-fragment/index.html")


@blueprint.route("/support/publisher-supporters/")
def publisher_supporters():
    return render_template("layouts/static_page.html", page_frag="/support/publisher-supporters-fragment/index.html")


@blueprint.route("/support/supporters/")
def supporters():
    return render_template("layouts/static_page.html", page_frag="/support/supporters-fragment/index.html")

@blueprint.route("/apply/guide/")
def guide():
    return render_template("layouts/static_page.html", page_frag="/apply/guide-fragment/index.html")


@blueprint.route("/apply/seal/")
def seal():
    return render_template("layouts/static_page.html", page_frag="/apply/seal-fragment/index.html")


@blueprint.route("/apply/transparency/")
def transparency():
    return render_template("layouts/static_page.html", page_frag="/apply/transparency-fragment/index.html")


@blueprint.route("/apply/why-index/")
def why_index():
    return render_template("layouts/static_page.html", page_frag="/apply/why-index-fragment/index.html")


@blueprint.route("/docs/oai-pmh/")
def oai_pmh():
    return render_template("layouts/static_page.html", page_frag="/docs/oai-pmh-fragment/index.html")


@blueprint.route('/docs/api/')
def docs():
    return render_template('api/v2/api_docs.html')


@blueprint.route("/docs/xml/")
def xml():
    return render_template("layouts/static_page.html", page_frag="/docs/xml-fragment/index.html")


@blueprint.route("/docs/widgets/")
def widgets():
    return render_template("layouts/static_page.html", page_frag="/docs/widgets-fragment/index.html")


@blueprint.route("/docs/public-data-dump/")
def public_data_dump():
    return render_template("layouts/static_page.html", page_frag="/docs/public-data-dump-fragment/index.html")


@blueprint.route("/docs/openurl/")
def openurl():
    return render_template("layouts/static_page.html", page_frag="/docs/openurl-fragment/index.html")


@blueprint.route("/about/")
def about():
    return render_template("layouts/static_page.html", page_frag="/about/index-fragment/index.html")


@blueprint.route("/about/ambassadors/")
def ambassadors():
    return render_template("layouts/static_page.html", page_frag="/about/ambassadors-fragment/index.html")


@blueprint.route("/about/advisory-board-council/")
def abc():
    return render_template("layouts/static_page.html", page_frag="/about/advisory-board-council-fragment/index.html")


@blueprint.route("/about/volunteers/")
def volunteers():
    return render_template("layouts/static_page.html", page_frag="/about/volunteers-fragment/index.html")


@blueprint.route("/about/faq/")
def faq():
    return render_template("layouts/static_page.html", page_frag="/about/faq-fragment/index.html")


@blueprint.route("/about/team/")
def team():
    return render_template("layouts/static_page.html", page_frag="/about/team-fragment/index.html")


# LEGACY ROUTES
@blueprint.route("/<cc>/mejorespracticas")
@blueprint.route("/<cc>/boaspraticas")
@blueprint.route("/<cc>/bestpractice")
@blueprint.route("/<cc>/editionsavante")
@blueprint.route("/bestpractice")
@blueprint.route("/oainfo")
def bestpractice(cc=None):
    return redirect(url_for("doaj.transparency", **request.args), code=308)


@blueprint.route("/suggest", methods=['GET'])
def suggest():
    return redirect(url_for('.suggestion', **request.args), code=301)


@blueprint.route("/membership")
def membership():
    return redirect(url_for("doaj.support", **request.args), code=308)


@blueprint.route("/publishermembers")
def old_sponsors():
    return redirect(url_for("doaj.sponsors", **request.args), code=308)


@blueprint.route("/members")
def members():
    return redirect(url_for("doaj.supporters", **request.args), code=308)


@blueprint.route('/features')
def features():
    return redirect(url_for("doaj.xml", **request.args), code=308)


# @blueprint.route('/widgets')
# def old_widgets():
#     return redirect(url_for("doaj.widgets", **request.args), code=308)


@blueprint.route("/public-data-dump/<record_type>")
def old_public_data_dump(record_type):
    return redirect(url_for("doaj.public_data_dump", **request.args), code=308)


@blueprint.route("/openurl/help")
def old_openurl():
    return redirect(url_for("doaj.openurl", **request.args), code=308)


@blueprint.route("/faq")
def old_faq():
    return redirect(url_for("doaj.faq", **request.args), code=308)


@blueprint.route("/privacy")
def privacy():
    return render_template("layouts/static_page.html")


@blueprint.route("/publishers")
def publishers():
    return render_template("layouts/static_page.html")
