from flask import Blueprint, request, abort, make_response
from flask.ext.login import current_user

from portality import models as models
from portality.core import app

from lxml import etree
from datetime import datetime, timedelta

blueprint = Blueprint('feed', __name__)


@blueprint.route('/<path:path>/feed')
@blueprint.route('/feed')
@blueprint.route('/feed/<title>')
def feed(path=None, title=None):
    # atom feeds require query strings, even if it is just "*"
    if path or request.path == '/feed':
        if request.path == '/feed':
            path = '/'
        else:
            path = '/' + path
        rec = models.Pages.pull_by_url(path)
        if rec is not None and 'feed' in rec.data and rec.data['feed'] != "":
            title = rec.data.get("title", "untitled")
            return get_feed_resp(title, rec.data["feed"], request)
        else:
            abort(404)
            
    elif title and 'q' in request.values:
        return get_feed_resp(title, request.values['q'], request)
        
    else:
        abort(404)


def get_feed_resp(title, query, req):
    # get the records from elasticsearch
    # build an elastic search query, which gives us all accessible, visible pages 
    # which conform to the supplied query string.  We obtain a maximum of 20 entries
    # or the amount in the configuration
    qtype = app.config.get('FEED_INDEX',"Pages")[0].capitalize() + app.config.get('FEED_INDEX',"Pages")[1:]
    klass = getattr(models, qtype )
    qs = {
        "query": {
            "bool": {
                "must": [
                    {"query_string": { "query": query }}
                ]
            }
        },
        "size": app.config.get('MAX_FEED_ENTRIES',20)
    }

    if 'sort' not in qs and app.config.get('DEFAULT_SORT',False):
        if qtype.lower() in app.config['DEFAULT_SORT'].keys():
            qs['sort'] = app.config['DEFAULT_SORT'][qtype.lower()]

    if current_user.is_anonymous() and app.config.get('ANONYMOUS_SEARCH_TERMS',False):
        if qtype.lower() in app.config['ANONYMOUS_SEARCH_TERMS'].keys():
            qs['query']['bool']['must'] = qs['query']['bool']['must'] + app.config['ANONYMOUS_SEARCH_TERMS'][qtype.lower()]

    resp = klass().query(q=qs)
    records = [r.get("_source") for r in resp.get("hits", {}).get("hits", []) if "_source" in r]
    
    # reconstruct the original request url (urgh, why is this always such a pain)
    url = app.config.get("BASE_URL","") + req.path + "?q=" + query
    
    # make a new atom feed object
    af = AtomFeed(title, url)
    
    # for each of the records, if the date is newer than the max age, add it to 
    # the feed.  Since all the objects are in the correct order, as soon as we
    # hit a date that's out of range we can stop processing all the rest.
    newer_than = None
    if app.config.get('MAX_FEED_ENTRY_AGE',False):
        newer_than = datetime.now() - timedelta(seconds=app.config['MAX_FEED_ENTRY_AGE'])
    for record in records:
        lu = record.get("last_updated")
        if lu is not None:
            dr = datetime.strptime(lu, "%Y-%m-%d %H%M")
            if newer_than is None or (newer_than is not None and dr >= newer_than):
                af.add_entry(record)
            else:
                break
        
    # serialise and respond with the atom xml
    resp = make_response(af.serialise())
    resp.mimetype = "application/atom+xml"
    return resp

class AtomFeed(object):
    ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
    ATOM = "{%s}" % ATOM_NAMESPACE
    NSMAP = {None : ATOM_NAMESPACE}

    def __init__(self, title, url):
        self.title = title + " - " + app.config['SERVICE_NAME']
        self.url = url
        self.generator = app.config.get('FEED_GENERATOR',"")
        self.icon = app.config.get('BASE_URL',"") + "/static/favicon.ico"
        self.logo = app.config.get("FEED_LOGO","")
        self.link = app.config.get('BASE_URL',"")
        self.rights = app.config.get('FEED_LICENCE',"")
        self.last_updated = None
        
        self.entries = {}
    
    def add_entry(self, page):
        lu = page.get("last_updated")
        last_updated = None
        if lu is not None:
            dr = datetime.strptime(lu, "%Y-%m-%d %H%M")
            last_updated = datetime.strftime(dr, "%Y-%m-%dT%H:%M:%SZ")
            if self.last_updated is None or dr > self.last_updated:
                self.last_updated = dr
        
        entry = {}
        entry['author'] = page.get("author", app.config["SERVICE_NAME"])
        entry["categories"] = page.get("tags", [])
        entry["content_src"] = app.config['BASE_URL'] + page.get("url")
        entry["id"] = "urn:uuid:" + page.get("id")
        entry['alternate'] = app.config['BASE_URL'] + page.get("url")
        entry['rights'] = app.config['FEED_LICENCE']
        entry['summary'] = page.get("excerpt") if page.get("excerpt") is not None and page.get("excerpt") != "" else "No summary available"
        entry['title'] = page.get("title", "untitled")
        entry['updated'] = last_updated
        
        if last_updated in self.entries:
            self.entries[last_updated].append(entry)
        else:
            self.entries[last_updated] = [entry]
        
    def serialise(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
        
        feed = etree.Element(self.ATOM + "feed", nsmap=self.NSMAP)
        
        title = etree.SubElement(feed, self.ATOM + "title")
        title.text = self.title
        
        if self.generator is not None:
            generator = etree.SubElement(feed, self.ATOM + "generator")
            generator.text = self.generator
        
        icon = etree.SubElement(feed, self.ATOM + "icon")
        icon.text = self.icon
        
        if self.logo is not None:
            logo = etree.SubElement(feed, self.ATOM + "logo")
            logo.text = self.logo
        
        self_link = etree.SubElement(feed, self.ATOM + "link")
        self_link.set("rel", "self")
        self_link.set("href", self.url)
        
        link = etree.SubElement(feed, self.ATOM + "link")
        link.set("rel", "related")
        link.set("href", self.link)
        
        rights = etree.SubElement(feed, self.ATOM + "rights")
        rights.text = self.rights
        
        updated = etree.SubElement(feed, self.ATOM + "updated")
        dr = datetime.strftime(self.last_updated, "%Y-%m-%dT%H:%M:%SZ")
        updated.text = dr
        
        entry_dates = self.entries.keys()
        entry_dates.sort(reverse=True)
        for ed in entry_dates:
            es = self.entries.get(ed)
            for e in es:
                self._serialise_entry(feed, e)
        
        tree = etree.ElementTree(feed)
        return etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="utf-8")
    
    def _serialise_entry(self, feed, e):
        entry = etree.SubElement(feed, self.ATOM + "entry")
        
        author = etree.SubElement(entry, self.ATOM + "author")
        name = etree.SubElement(author, self.ATOM + "name")
        name.text = e['author']
        if e['author'] != app.config['SERVICE_NAME']:
            puri = etree.SubElement(author, self.ATOM + "uri")
            puri.text = app.config["BASE_URL"] + "/people/" + e['author']
        
        for cat in e.get("categories", []):
            c = etree.SubElement(entry, self.ATOM + "category")
            c.set("term", cat)
        
        cont = etree.SubElement(entry, self.ATOM + "content")
        cont.set("src", e['content_src'])
        
        id = etree.SubElement(entry, self.ATOM + "id")
        id.text = e['id']
        
        # this is not strictly necessary, as we have an atom:content element, but it can't harm
        alt = etree.SubElement(entry, self.ATOM + "link")
        alt.set("rel", "alternate")
        alt.set("href", e['alternate'])
        
        rights = etree.SubElement(entry, self.ATOM + "rights")
        rights.text = e['rights']
        
        summary = etree.SubElement(entry, self.ATOM + "summary")
        summary.text = e['summary']
        
        title = etree.SubElement(entry, self.ATOM + "title")
        title.text = e['title']
        
        updated = etree.SubElement(entry, self.ATOM + "updated")
        updated.text = e['updated']
        
        
