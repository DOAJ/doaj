from flask import Blueprint, request, flash, make_response
from flask import render_template, abort, redirect, url_for, send_file, jsonify
from flask_login import current_user, login_required
import urllib

from portality import dao
from portality import models
from portality import blog
from portality.core import app
from portality.decorators import ssl_required, write_required, cookie_consent
from portality.formcontext import formcontext
from portality.lcc import lcc_jstree
from portality.view.forms import ContactUs
from portality.app_email import send_contact_form
from portality.lib import analytics

import json
import os

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

blueprint = Blueprint('doaj', __name__)


@blueprint.route("/")
def home():
    news = blog.News.latest(app.config.get("FRONT_PAGE_NEWS_ITEMS", 5))
    return render_template('doaj/index.html', news=news)

@blueprint.route("/cookie_consent")
def cookie_consent():
    resp = make_response()
    resp.set_cookie("doaj-consent", "Delete this cookie to revoke your consent")
    return resp


@blueprint.route("/news")
def news():
    news = blog.News.latest(app.config.get("NEWS_PAGE_NEWS_ITEMS", 20))
    return render_template('doaj/news.html', news=news, blog_url=app.config.get("BLOG_URL"))


@blueprint.route("/widgets")
def widgets():
    return render_template('doaj/widgets.html',
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
    return render_template('doaj/search.html', search_page=True, facetviews=['public.journalarticle.facetview'])


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
        return redirect(url_for('.search') + '?source=' + urllib.quote(json.dumps(query)) + "&ref=" + urllib.quote(ref))


@blueprint.route("/subjects")
def subjects():
    return render_template("doaj/subjects.html", subject_page=True, lcc_jstree=json.dumps(lcc_jstree))


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
            return redirect(url_for('doaj.suggestion_thanks', _anchor='thanks'))
        else:
            return fc.render_template(edit_suggestion_page=True)


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
def suggestion_thanks():
    return render_template('doaj/suggest_thanks.html')
    

@blueprint.route("/csv")
@analytics.sends_ga_event(event_category=app.config.get('GA_CATEGORY_JOURNALCSV', 'JournalCSV'), event_action=app.config.get('GA_ACTION_JOURNALCSV', 'Download'))
def csv_data():
    """
    with futures.ProcessPoolExecutor(max_workers=1) as executor:
        result = executor.submit(get_csv_data).result()
    return result
    """
    csv_file = models.Cache.get_latest_csv()
    csv_path = os.path.join(app.config.get("CACHE_DIR"), "csv", csv_file)
    return send_file(csv_path, mimetype="text/csv", as_attachment=True, attachment_filename=csv_file)


@blueprint.route("/sitemap.xml")
def sitemap():
    sitemap_file = models.Cache.get_latest_sitemap()
    sitemap_path = os.path.join(app.config.get("CACHE_DIR"), "sitemap", sitemap_file)
    return send_file(sitemap_path, mimetype="application/xml", as_attachment=False, attachment_filename="sitemap.xml")


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


@blueprint.route("/toc")
def list_journals():
    js = models.Journal.all_in_doaj(page_size=1000)
    return render_template("doaj/journals.html", journals=js)


@blueprint.route("/toc/<identifier>")
@blueprint.route("/toc/<identifier>/<volume>")
@blueprint.route("/toc/<identifier>/<volume>/<issue>")
def toc(identifier=None, volume=None, issue=None):
    # identifier may be the journal id or an issn
    journal = None
    issn_ref = False
    if len(identifier) == 9:
        js = models.Journal.find_by_issn(identifier, in_doaj=True)
        if len(js) > 1:
            abort(400)                             # really this is a 500 - we have more than one journal with this issn
        if len(js) == 0:
            abort(404)
        journal = js[0]

        issn_ref = True     # just a flag so we can check if we were requested via issn
    else:
        journal = models.Journal.pull(identifier)  # Returns None on fail

    if journal is None:
        abort(404)

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
                           search_page=True, toc_issns=journal.bibjson().issns(), facetviews=['public.journaltocarticles.facetview'])


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

        send_contact_form(form)
        flash("Thank you for your feedback which has been received by the DOAJ Team.", "success")
        form = ContactUs()
        return render_template("doaj/contact.html", form=form)

###############################################################
# The various static endpoints
###############################################################


@blueprint.route("/about")
def about():
    return render_template('doaj/about.html')

@blueprint.route("/publishers")
def publishers():
    return render_template('doaj/publishers.html')


@blueprint.route("/faq")
def faq():
    return render_template("doaj/faq.html")


@blueprint.route("/features")
def features():
    return render_template("doaj/features.html")


@blueprint.route("/features/oai_doaj/1.0/")
def doajArticles_oai_namespace_page():
    return render_template("doaj/doajArticles_oai_namespace.html")


@blueprint.route("/oainfo")
def oainfo():
    return render_template("doaj/oainfo.html")


@blueprint.route("/<cc>/mejorespracticas")
@blueprint.route("/<cc>/boaspraticas")
@blueprint.route("/<cc>/bestpractice")
@blueprint.route("/<cc>/editionsavante")
@blueprint.route("/bestpractice")
def bestpractice(cc=None):
    # FIXME: if we go for full multilingual support, it would be better to put this in the template
    # loader and have it check for templates in the desired language, and provide fall-back
    if cc is not None and cc in ["es", "pt", "fa", "fr", "kr", "uk", "ca", "tr", "hi"]:
        return render_template("doaj/i18n/" + cc + "/bestpractice.html")
    return render_template("doaj/bestpractice.html")


@blueprint.route("/members")
def members():
    return render_template("doaj/members.html")


@blueprint.route("/membership")
def membership():
    return render_template("doaj/membership.html")


@blueprint.route("/sponsors")
def sponsors():
    return render_template("doaj/our_sponsors.html")


@blueprint.route("/volunteers")
def volunteers():
    return render_template("doaj/volunteers.html")


@blueprint.route("/support")
def support():
    return render_template("doaj/support.html")


@blueprint.route("/publishermembers")
def publishermembers():
    return render_template("doaj/publishermembers.html")


@blueprint.route("/suggest", methods=['GET'])
def suggest():
    return redirect(url_for('.suggestion'), code=301)


@blueprint.route("/support_thanks")
def support_doaj_thanks():
    return render_template("doaj/support_thanks.html")


@blueprint.route("/translated")
def translated():
    return render_template("doaj/translated.html")


@blueprint.route("/googlebdb21861de30fe30.html")
def google_webmaster_tools():
    return 'google-site-verification: googlebdb21861de30fe30.html'


# an informational page about content licensing rights
@blueprint.route('/rights')
def rights():
    return render_template('doaj/rights.html')


# A page about the SCOSS partnership
@blueprint.route('/scoss')
def scoss():
    return render_template('doaj/scoss.html')


# A page about privacy information
@blueprint.route('/privacy')
def privacy():
    return render_template('doaj/privacy.html')
