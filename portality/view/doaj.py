from flask import Blueprint, request, abort, make_response
from flask import render_template, abort, redirect, url_for, flash, send_file, jsonify
from flask.ext.login import current_user, login_required
import urllib
from copy import deepcopy

from portality import dao
from portality import models
from portality.core import app, ssl_required, write_required
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

    query = dao.Facetview2.make_query(request.form.get("q"), filters=filters)
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
    prefix = request.args.get('q','').lower()
    if not prefix:
        return jsonify({'suggestions':[{"id":"", "text": "No results found"}]})  # select2 does not understand 400, which is the correct code here...

    m = models.lookup_model(doc_type)
    if not m:
        return jsonify({'suggestions':[{"id":"", "text": "No results found"}]})  # select2 does not understand 404, which is the correct code here...

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
    # check for a browser js request for more volume/issue data
    bjsr = request.args.get('bjsr',False)
    bjsri = request.args.get('bjsri',False)
    
    # identifier may be the journal id or an issn
    journal = None
    issn_ref = False
    if len(identifier) == 9:
        js = models.Journal.find_by_issn(identifier, in_doaj=True)
        if len(js) > 1:
            abort(400) # really this is a 500 - we have more than one journal with this issn
        if len(js) == 0:
            abort(404)
        journal = js[0]

        bibjson = journal.bibjson()
        
        # if there is an E-ISSN (and it's not the one in the request), redirect to it
        # if not, but there is a P-ISSN (and it's not the one in the request), redirect to the P-ISSN
        eissn = bibjson.get_one_identifier(bibjson.E_ISSN)
        if eissn and identifier != eissn:
                return redirect(url_for('doaj.toc', identifier=eissn, volume=volume, issue=issue), 301)
        
        if not eissn:
            pissn = bibjson.get_one_identifier(bibjson.P_ISSN)
            if pissn and identifier != pissn:
                return redirect(url_for('doaj.toc', identifier=pissn, volume=volume, issue=issue), 301)

        issn_ref = True     # just a flag so we can check if we were requested via issn
    else:
        journal = models.Journal.pull(identifier)
        if journal is None:
            abort(404)

        # if there is an E-ISSN, redirect to it
        # if not, but there is a P-ISSN, redirect to it
        # if neither ISSN is present, continue loading the page
        bibjson = journal.bibjson()
        issn = bibjson.get_one_identifier(bibjson.E_ISSN)
        if not issn:
            issn = bibjson.get_one_identifier(bibjson.P_ISSN)
        if issn:
            return redirect(url_for('doaj.toc', identifier=issn, volume=volume, issue=issue), 301)
        # let it continue loading if we only have the hex UUID for the journal (no ISSNs)
        # and the user is referring to the toc page via that ID
    if journal is None:
        abort(404)

    # get the bibjson that we will render the ToC around - default to the most recent version's
    # bibjson, and then if we were passed an issn get the historical version if one exists (if
    # one doesn't it is the current version we want)
    bibjson = journal.bibjson()
    if issn_ref:
        histbibjson = journal.get_history_for(identifier)
        if histbibjson is not None:
            bibjson = histbibjson

    # get the issns for this specific continuation
    issns = bibjson.issns()

    # build the volumes and issues
    all_issues = None
    all_volumes = None
    
    if volume is None or not bjsr:
        all_volumes = models.Article.list_volumes(issns)
        if volume is None and not bjsr and len(all_volumes) > 0: volume = all_volumes[0]

    if (issue is None or (not bjsr and not bjsri)) and volume is not None:
        all_issues = models.Article.list_volume_issues(issns, volume)
        if len(all_issues) == 0: all_issues = ["unknown"]
        if issue is None: issue = all_issues[0]

    articles = None
    if volume is not None and issue is not None:
        articles = models.Article.get_by_volume_issue(issns, volume, issue) 
        if (articles is None or len(articles) == 0):
            abort(404)

    if bjsr:
        res = {"articles": articles}
        if bjsri: res["issues"] = all_issues
        resp = make_response( json.dumps(res) )
        resp.mimetype = "application/json"
        return resp
    else:
        # get the continuations for this bibjson record, future and past
        issn = bibjson.get_one_identifier(bibjson.E_ISSN)
        if issn is None:
            issn = bibjson.get_one_identifier(bibjson.P_ISSN)
        future, past = journal.get_history_around(issn)

        return render_template('doaj/toc.html', journal=journal, bibjson=bibjson, future=future, past=past,
                               articles=articles, volumes=all_volumes, current_volume=volume,
                               issues=all_issues, current_issue=issue)

@blueprint.route("/article/<identifier>")
def article_page(identifier=None):
    # identifier must be the article id
    article = models.Article.pull(identifier)

    if article is None:
        abort(404)

    # find the related journal record
    journal = None
    issns = article.bibjson().issns()
    for issn in issns:
        journals = models.Journal.find_by_issn(issns[0])
        if len(journals) > 0:
            journal = journals[0]

    return render_template('doaj/article.html', article=article, journal=journal)

###############################################################
## The various static endpoints
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
