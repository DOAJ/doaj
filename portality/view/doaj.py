from flask import Blueprint, request, make_response
from flask import render_template, abort, redirect, url_for, send_file, jsonify
from flask.ext.login import current_user, login_required
import urllib

from portality import dao
from portality import models
from portality.core import app
from portality.decorators import ssl_required, write_required
from portality import blog
from portality.formcontext import formcontext
from portality.lcc import lcc_jstree

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


@blueprint.route("/search", methods=['GET'])
def search():
    return render_template('doaj/search.html', search_page=True, facetviews=['public.journalarticle.facetview'])


@blueprint.route("/search", methods=['POST'])
def search_post():
    if request.form.get('origin') != 'ui':
        abort(501)  # not implemented

    filters = None
    if not (request.form.get('include_journals') and request.form.get('include_articles')):
        filters = []
        if request.form.get('include_journals'):
            filters.append(dao.Facetview2.make_term_filter("_type", "journal"))
        elif request.form.get('include_articles'):
            filters.append(dao.Facetview2.make_term_filter("_type", "article"))

    query = dao.Facetview2.make_query(request.form.get("q"), filters=filters, default_operator="AND")
    return redirect(url_for('.search') + '?source=' + urllib.quote(json.dumps(query)))


@blueprint.route("/subjects")
def subjects():
    return render_template("doaj/subjects.html", subject_page=True, lcc_jstree=json.dumps(lcc_jstree))


@blueprint.route("/application/new", methods=["GET", "POST"])
@write_required
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
    prefix = request.args.get('q', '').lower()
    if not prefix:
        return jsonify({'suggestions': [{"id": "", "text": "No results found"}]})  # select2 does not understand 400, which is the correct code here...

    m = models.lookup_model(doc_type)
    if not m:
        return jsonify({'suggestions': [{"id": "", "text": "No results found"}]})  # select2 does not understand 404, which is the correct code here...

    size = request.args.get('size', 5)
    return jsonify({'suggestions': m.autocomplete(field_name, prefix, size=size)})
    # you shouldn't return lists top-level in a JSON response:
    # http://flask.pocoo.org/docs/security/#json-security


@blueprint.route("/toc")
def list_journals():
    js = models.Journal.all_in_doaj(page_size=1000, minified=True)
    return render_template("doaj/journals.html", journals=js)


@blueprint.route("/toc/<identifier>")
@blueprint.route("/toc/<identifier>/<volume>")
@blueprint.route("/toc/<identifier>/<volume>/<issue>")
def toc(identifier=None, volume=None, issue=None):
    # identifier may be the journal id or an issn
    if len(identifier) == 9:
        js = models.Journal.find_by_issn(identifier, in_doaj=True)
        if len(js) > 1:
            abort(400)                             # really this is a 500 - we have more than one journal with this issn
        if len(js) == 0:
            abort(404)
        journal = js[0]
    else:
        journal = models.Journal.pull(identifier)  # Returns None on fail

    if journal is None:
        abort(404)

    # get the bibjson that we will render the ToC around
    bibjson = journal.bibjson()

    # The issn we are using to build the TOC
    issn = bibjson.get_preferred_issn()

    # Add the volume and issue to query if present in path
    if volume:
        filters = [dao.Facetview2.make_term_filter('bibjson.journal.volume.exact', volume)]
        if issue:
            filters += [dao.Facetview2.make_term_filter('bibjson.journal.number.exact', issue)]
        q = dao.Facetview2.make_query(filters=filters)

        return redirect(url_for('doaj.toc', identifier=issn) + '?source=' + dao.Facetview2.url_encode_query(q))

    return render_template('doaj/fv_toc.html',
                           journal=journal,
                           bibjson=bibjson,
                           search_page=True,
                           toc_issn=issn,
                           facetviews=['public.journaltocarticles.facetview'])


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

###############################################################
# The various static endpoints
###############################################################


@blueprint.route("/about")
def about():
    return render_template('doaj/about.html')


@blueprint.route("/contact")
def contact():
    return render_template("doaj/contact.html")


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


@blueprint.route("/bestpractice")
def bestpractice():
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


@blueprint.route("/supportDoaj")
def support_doaj():
    return render_template("doaj/supportDoaj.html")


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
