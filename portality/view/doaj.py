from flask import Blueprint, request, abort, make_response
from flask import render_template, abort, redirect, url_for, flash, send_file, jsonify
from flask.ext.login import current_user

from portality import dao
from portality import models
from portality.core import app
from portality import blog
from portality.view.forms import SuggestionForm, other_val, digital_archiving_policy_specific_library_value
from portality.suggestion import SuggestionFormXWalk, suggestion_form
from portality.datasets import countries_dict
from portality import lock

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
    return render_template('doaj/search.html',
               search_page=True,
               facetviews=['journals_and_articles']
           )

@blueprint.route("/search", methods=['POST'])
def search_post():
    if request.form.get('origin') != 'ui':
        abort(501)  # not implemented

    terms = {'_type': []}
    if request.form.get('include_journals') and request.form.get('include_articles'):
        terms = {}  # the default anyway
    elif request.form.get('include_journals'):
        terms['_type'].append('journal')
    elif request.form.get('include_articles'):
        terms['_type'].append('article')

    qobj = dao.DomainObject.make_query(q=request.form.get('q'), terms=terms)
    return redirect(url_for('.search') + '?source=' + json.dumps(qobj))  # can't pass source as keyword param to url_for as usual, will urlencode the query object

@blueprint.route("/application/new", methods=["GET", "POST"])
def suggestion():
    form = SuggestionForm(request.form)
    form.editor.choices = [("","")]

    redirect_url_on_success = url_for('doaj.suggestion_thanks', _anchor='thanks')
    # meaningless anchor to replace #first_problem used on the form
    # anchors persist between 3xx redirects to the same resource
    # (/application)

    return suggestion_form(form, request, 'doaj/suggestion.html', success_url=redirect_url_on_success)

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
def toc(identifier=None, volume=None):
    # identifier may be the journal id or an issn
    journal = None
    jid = identifier # track the journal id - this may be an issn, in which case this will get overwritten
    if len(identifier) == 9:
        js = models.Journal.find_by_issn(identifier)
        if len(js) > 1:
            abort(400) # really this is a 500 - we have more than one journal with this issn
        if len(js) == 0:
            abort(404)
        journal = js[0]
        jid = journal.id
    else:
        journal = models.Journal.pull(identifier)
    if journal is None:
        abort(404)
    
    all_volumes = models.JournalVolumeToC.list_volumes(jid)
    all_volumes = _sort_volumes(all_volumes)
    
    if volume is None and len(all_volumes) > 0:
        volume = all_volumes[0]
    
    table = None
    if volume is not None:
        table = models.JournalVolumeToC.get_toc(jid, volume)
        if table is None:
            abort(404)
    
    return render_template('doaj/toc.html', journal=journal, table=table, volumes=all_volumes, current_volume=volume, countries=countries_dict)

def _sort_volumes(volumes):
    numeric = []
    non_numeric = []
    nmap = {}
    for v in volumes:
        try:
            # try to convert n to an int
            vint = int(v)

            # remember the original string (it may have leading 0s)
            try:
                nmap[vint].append(v)
            except KeyError:
                nmap[vint] = [v]
                numeric.append(vint)
        except:
            non_numeric.append(v)

    numeric.sort(reverse=True)
    non_numeric.sort(reverse=True)

    # convert the integers back to their string representation
    return reduce(lambda x, y: x+y, [nmap[n] for n in numeric], []) + non_numeric


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
