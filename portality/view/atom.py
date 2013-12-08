from flask import Blueprint, request, abort, make_response
from flask.ext.login import current_user

from portality import models as models
from portality.core import app

from lxml import etree
from datetime import datetime, timedelta
import urllib

blueprint = Blueprint('atom', __name__)

@blueprint.route('/feed')
def feed():
    max_size = app.config.get("MAX_FEED_ENTRIES", 20)
    max_age = app.config.get("MAX_FEED_ENTRY_AGE", 2592000)
    from_date = (datetime.now() - timedelta(0, max_age)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    dao = models.AtomRecord()
    records = dao.list_records(from_date, max_size)
    
    title = app.config.get("FEED_TITLE", "untitled")
    url = request.base_url
    generator = app.config.get('FEED_GENERATOR',"")
    icon = app.config.get("FEED_LOGO","")
    logo = app.config.get("FEED_LOGO","")
    link = app.config.get('BASE_URL',"")
    rights = app.config.get('FEED_LICENCE',"")
    
    xwalk = AtomCrosswalk()
    f = AtomFeed(title, url, generator, icon, logo, link, rights)
    
    for record in records:
        entry = xwalk.crosswalk(record)
        f.add_entry(entry)
        
    # serialise and respond with the atom xml
    resp = make_response(f.serialise())
    resp.mimetype = "application/atom+xml"
    return resp

class AtomCrosswalk(object):
    def crosswalk(self, atom_record):
        entry = {}
        b = atom_record.bibjson()
        
        if b.publisher is not None:
            entry["author"] = b.publisher
        elif b.provider is not None:
            entry["author"] = b.provider
        else:
            entry["author"] = app.config.get("SERVICE_NAME")
        
        cats = []
        for subs in b.subjects():
            scheme = subs.get("scheme")
            term = subs.get("term")
            cats.append(scheme + ":" + term)
        entry["categories"] = cats
        
        query = urllib.urlencode([("source", '{"query":{"bool":{"must":[{"term":{"id":"' + atom_record.id + '"}}]}}}')])
        content_src = app.config['BASE_URL'] + "/search?" + query
        entry["content_src"] = content_src
        
        entry["id"] = "urn:uuid:" + atom_record.id
        
        urls = b.get_urls(urltype="homepage")
        if len(urls) > 0:
            entry['alternate'] = urls[0]
        
        entry['rights'] = app.config['FEED_LICENCE']
        
        entry['summary'] = b.title
        entry['title'] = b.title
        entry['updated'] = atom_record.last_updated
        
        return entry

class AtomFeed(object):
    ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
    ATOM = "{%s}" % ATOM_NAMESPACE
    NSMAP = {None : ATOM_NAMESPACE}

    def __init__(self, title, url, generator, icon, logo, link, rights):
        self.title = title
        self.url = url
        self.generator = generator
        self.icon = icon
        self.logo = logo
        self.link = link
        self.rights = rights
        self.last_updated = None
        self.entries = {}
    
    def add_entry(self, entry):
        # update the "last_updated" property if necessary
        lu = entry.get("updated")
        dr = datetime.strptime(lu, "%Y-%m-%dT%H:%M:%SZ")
        if self.last_updated is None or dr > self.last_updated:
            self.last_updated = dr
        
        # record the entries by date
        if lu in self.entries:
            self.entries[lu].append(entry)
        else:
            self.entries[lu] = [entry]
        
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
        
        
