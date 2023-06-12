import json
import re
import urllib.error
import urllib.parse
import urllib.request

from flask import Blueprint, request, make_response
from flask import render_template, abort, redirect, url_for, send_file, jsonify
from flask_login import current_user, login_required

from portality import constants
from portality import dao
from portality import models
from portality import store
from portality.core import app
from portality.decorators import ssl_required, api_key_required
from portality.forms.application_forms import JournalFormFactory
from portality.lcc import lcc_jstree
from portality.lib import plausible
from portality.ui.messages import Messages

# ~~DOAJ:Blueprint~~
blueprint = Blueprint('doaj', __name__)


@blueprint.route("/")
def home():
    news = models.News.latest(app.config.get("FRONT_PAGE_NEWS_ITEMS", 5))
    recent_journals = models.Journal.recent(max=16)
    return render_template('doaj/index.html', news=news, recent_journals=recent_journals)


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
    resp.set_cookie(app.config.get("CONSENT_COOKIE_KEY"), Messages.CONSENT_COOKIE_VALUE, max_age=31536000, samesite=None, secure=True)
    return resp


@blueprint.route("/dismiss_site_note")
def dismiss_site_note():
    cont = request.values.get("continue")
    if cont is not None:
        resp = redirect(cont)
    else:
        resp = make_response()
    # set a cookie that lasts for one year
    resp.set_cookie(app.config.get("SITE_NOTE_KEY"), app.config.get("SITE_NOTE_COOKIE_VALUE"), max_age=app.config.get("SITE_NOTE_SLEEP"), samesite=None, secure=True)
    return resp


@blueprint.route("/news")
def news():
    return redirect("https://blog.doaj.org")


@blueprint.route("/fqw_hit", methods=['POST'])
def fqw_hit():
    page = request.form.get('embedding_page')
    if page is not None:
        plausible.send_event(app.config.get('GA_CATEGORY_FQW', 'FQW'),
                             action=app.config.get('GA_ACTION_FQW', 'hit'),
                             label=request.form.get('embedding_page'))

    # No content response, whether data there or not.
    return '', 204


@blueprint.route("/search/journals", methods=["GET"])
def journals_search():
    return render_template("doaj/journals_search.html", lcc_tree=lcc_jstree)


@blueprint.route("/search/articles", methods=["GET"])
def articles_search():
    return render_template("doaj/articles_search.html", lcc_tree=lcc_jstree)


@blueprint.route("/search", methods=['GET'])
def search():
    # If there are URL params, check if we need to redirect to articles rather than journals
    if request.values:
        # Flat search the query params as string so we don't have to traverse all the way down the decoded json.
        if re.search(r'\"_type\"\s*:\s*\"article\"', request.values.get('source', '')):
            return redirect(url_for("doaj.articles_search"), 301)
    return redirect(url_for("doaj.journals_search"), 301)


@blueprint.route("/search", methods=['POST'])
def search_post():
    """ Redirect a query from the box on the index page to the search page. """
    if request.form.get('origin') != 'ui':
        abort(400)                                              # bad request - we must receive searches from our own UI

    ref = request.form.get("ref")
    if ref is None:
        abort(400)  # Referrer is required

    ct = request.form.get("content-type")
    kw = request.form.get("keywords")
    field = request.form.get("fields")

    if kw is None:
        kw = request.form.get("q")  # back-compat for the simple search widget

    # lhs for journals, rhs for articles
    field_map = {
        "all" : (None, None),
        "title" : ("bibjson.title", "bibjson.title"),
        "abstract" : (None, "bibjson.abstract"),
        "subject" : ("index.classification", "index.classification"),
        "author" : (None, "bibjson.author.name"),
        "issn" : ("index.issn.exact", None),
        "publisher" : ("bibjson.publisher.name", None)
    }
    default_field_opts = field_map.get(field, None)
    default_field = None

    route = ""
    if not ct or ct == "journals":
        route = url_for("doaj.journals_search")
        if default_field_opts:
            default_field = default_field_opts[0]
    elif ct == "articles":
        route = url_for("doaj.articles_search")
        if default_field_opts:
            default_field = default_field_opts[1]
    else:
        abort(400)

    query = dao.Facetview2.make_query(kw, default_field=default_field, default_operator="AND")

    return redirect(route + '?source=' + urllib.parse.quote(json.dumps(query)) + "&ref=" + urllib.parse.quote(ref))

#############################################

# FIXME: this should really live somewhere else more appropirate to who can access it
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

    fc = JournalFormFactory.context("readonly")
    fc.processor(source=j)
    return fc.render_template(obj=j, lcc_tree=lcc_jstree)


@blueprint.route("/csv")
@plausible.pa_event(app.config.get('GA_CATEGORY_JOURNALCSV', 'JournalCSV'),
                    action=app.config.get('GA_ACTION_JOURNALCSV', 'Download'))
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
    sitemap_url = models.Cache.get_latest_sitemap()
    if sitemap_url is None:
        abort(404)
    if sitemap_url.startswith("/"):
        sitemap_url = "/store" + sitemap_url
    return redirect(sitemap_url, code=307)


@blueprint.route("/public-data-dump/<record_type>")
@api_key_required
def public_data_dump_redirect(record_type):
    if not current_user.has_role(constants.ROLE_PUBLIC_DATA_DUMP):
        abort(404)

    target_data = models.Cache.get_public_data_dump().get(record_type, {})
    if target_data is None:
        abort(404)

    main_store = store.StoreFactory.get(constants.STORE__SCOPE__PUBLIC_DATA_DUMP)
    store_url = main_store.temporary_url(target_data.get("container"),
                                         target_data.get("filename"),
                                         timeout=app.config.get("PUBLIC_DATA_DUMP_URL_TIMEOUT", 3600))

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
    """ Table of Contents page for a journal. identifier may be the journal id or an issn """
    # If this route is changed, update JOURNAL_TOC_URL_FRAG in settings.py (partial ToC page link for journal CSV)

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


#~~->Article:Page~~
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

    return render_template('doaj/article.html', article=article, journal=journal, page={"highlight" : True})

# Not using this form for now but we might bring it back later
# @blueprint.route("/contact/", methods=["GET", "POST"])
# def contact():
#     if request.method == "GET":
#         form = ContactUs()
#         if current_user.is_authenticated:
#             form.email.data = current_user.email
#         return render_template("doaj/contact.html", form=form)
#     elif request.method == "POST":
#         prepop = request.values.get("ref")
#         form = ContactUs(request.form)
#
#         if current_user.is_authenticated and (form.email.data is None or form.email.data == ""):
#             form.email.data = current_user.email
#
#         if prepop is not None:
#             return render_template("doaj/contact.html", form=form)
#
#         if not form.validate():
#             return render_template("doaj/contact.html", form=form)
#
#         data = _verify_recaptcha(form.recaptcha_value.data)
#         if data["success"]:
#             send_contact_form(form)
#             flash("Thank you for your feedback which has been received by the DOAJ Team.", "success")
#             form = ContactUs()
#             return render_template("doaj/contact.html", form=form)
#         else:
#             flash("Your form could not be submitted,", "error")
#             return render_template("doaj/contact.html", form=form)


###############################################################
# The various static endpoints
###############################################################

@blueprint.route("/googlebdb21861de30fe30.html")
def google_webmaster_tools():
    return 'google-site-verification: googlebdb21861de30fe30.html'


@blueprint.route("/accessibility/")
def accessibility():
    return render_template("layouts/static_page.html", page_frag="/legal/accessibility.html")


@blueprint.route("/privacy/")
def privacy():
    return render_template("layouts/static_page.html", page_frag="/legal/privacy.html")


@blueprint.route("/contact/")
def contact():
    return render_template("layouts/static_page.html", page_frag="/legal/contact.html")


@blueprint.route("/terms/")
def terms():
    return render_template("layouts/static_page.html", page_frag="/legal/terms.html")


@blueprint.route("/media/")
def media():
    """
    ~~Media:WebRoute~~
    """
    return render_template("layouts/static_page.html", page_frag="/legal/media.html")


@blueprint.route("/support/")
def support():
    return render_template("layouts/static_page.html", page_frag="/support/index.html")


@blueprint.route("/support/sponsors/")
def sponsors():
    return render_template("layouts/static_page.html", page_frag="/support/sponsors.html")


@blueprint.route("/support/publisher-supporters/")
def publisher_supporters():
    return render_template("layouts/static_page.html", page_frag="/support/publisher-supporters.html")


@blueprint.route("/support/supporters/")
def supporters():
    return render_template("layouts/static_page.html", page_frag="/support/supporters.html")


@blueprint.route("/support/thank-you/")
def application_thanks():
    return render_template("layouts/static_page.html", page_frag="/support/thank-you.html")


@blueprint.route("/apply/guide/")
def guide():
    return render_template("layouts/static_page.html", page_frag="/apply/guide.html")


@blueprint.route("/apply/seal/")
def seal():
    return render_template("layouts/static_page.html", page_frag="/apply/seal.html")


@blueprint.route("/apply/transparency/")
def transparency():
    return render_template("layouts/static_page.html", page_frag="/apply/transparency.html")


@blueprint.route("/apply/why-index/")
def why_index():
    return render_template("layouts/static_page.html", page_frag="/apply/why-index.html")

# TODO: Uncomment when ready for public access  - S.E. 2022-03-14
# @blueprint.route("/apply/publisher-responsibilities/")
# def publisher_responsibilities():
#     return render_template("layouts/static_page.html", page_frag="/apply/publisher-responsibilities.html")


@blueprint.route("/apply/copyright-and-licensing/")
def copyright_and_licensing():
    return render_template("layouts/static_page.html", page_frag="/apply/copyright-and-licensing.html")


@blueprint.route("/docs/oai-pmh/")
def oai_pmh():
    return render_template("layouts/static_page.html", page_frag="/docs/oai-pmh.html")


@blueprint.route('/docs/api/')
def docs():
    return redirect(url_for('api_v3.docs'))


@blueprint.route("/docs/xml/")
def xml():
    return render_template("layouts/static_page.html", page_frag="/docs/xml.html")


@blueprint.route("/docs/widgets/")
def widgets():
    return render_template("layouts/static_page.html", page_frag="/docs/widgets.html", base_url=app.config.get('BASE_URL'))


@blueprint.route("/docs/public-data-dump/")
def public_data_dump():
    return render_template("layouts/static_page.html", page_frag="/docs/public-data-dump.html")


@blueprint.route("/docs/openurl/")
def openurl():
    return render_template("layouts/static_page.html", page_frag="/docs/openurl.html")


@blueprint.route("/docs/faq/")
def faq():
    return render_template("layouts/static_page.html", page_frag="/docs/faq.html")


@blueprint.route("/about/")
def about():
    return render_template("layouts/static_page.html", page_frag="/about/index.html")

@blueprint.route("/at-20/")
def at_20():
    return render_template("layouts/static_page.html", page_frag="/about/at-20.html")

@blueprint.route("/about/ambassadors/")
def ambassadors():
    return render_template("layouts/static_page.html", page_frag="/about/ambassadors.html")


@blueprint.route("/about/advisory-board-council/")
def abc():
    return render_template("layouts/static_page.html", page_frag="/about/advisory-board-council.html")


@blueprint.route("/about/volunteers/")
def volunteers():
    return render_template("layouts/static_page.html", page_frag="/about/volunteers.html")


@blueprint.route("/about/team/")
def team():
    return render_template("layouts/static_page.html", page_frag="/about/team.html")


@blueprint.route("/preservation/")
def preservation():
    return render_template("layouts/static_page.html", page_frag="/preservation/index.html")


# LEGACY ROUTES
@blueprint.route("/subjects")
def subjects():
    # return render_template("doaj/subjects.html", subject_page=True, lcc_jstree=json.dumps(lcc_jstree))
    return redirect(url_for("doaj.journals_search"), 301)


@blueprint.route("/application/new")
def old_application():
    return redirect(url_for("apply.public_application", **request.args), code=308)


@blueprint.route("/<cc>/mejorespracticas")
@blueprint.route("/<cc>/boaspraticas")
@blueprint.route("/<cc>/bestpractice")
@blueprint.route("/<cc>/editionsavante")
@blueprint.route("/bestpractice")
@blueprint.route("/oainfo")
def bestpractice(cc=None):
    return redirect(url_for("doaj.transparency", **request.args), code=308)


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


# @blueprint.route("/public-data-dump/<record_type>")
# def old_public_data_dump(record_type):
#     return redirect(url_for("doaj.public_data_dump", **request.args), code=308)


@blueprint.route("/openurl/help")
def old_openurl():
    return redirect(url_for("doaj.openurl", **request.args), code=308)


@blueprint.route("/faq")
def old_faq():
    return redirect(url_for("doaj.faq", **request.args), code=308)


@blueprint.route("/publishers")
def publishers():
    return redirect(url_for("doaj.guide", **request.args), code=308)


# Redirects necessitated by new templates
@blueprint.route("/password-reset/")
def new_password_reset():
    return redirect(url_for('account.forgot'), code=301)
