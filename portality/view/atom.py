from flask import Blueprint, request, make_response

from portality import models as models
from portality.core import app
from portality.lib import analytics
from portality.crosswalks.atom import AtomCrosswalk

from lxml import etree
from datetime import datetime, timedelta

blueprint = Blueprint('atom', __name__)


@blueprint.route('/feed')
@analytics.sends_ga_event(app.config.get('GA_CATEGORY_ATOM', 'Atom'), app.config.get('GA_ACTION_ACTION', 'Feed Request'))
def feed():
    # get the feed for this base_url (which is just used to set the metadata of
    # the feed, but we want to do this outside of a request context so it
    # is testable)
    f = get_feed(request.base_url)

    # serialise and respond with the atom xml
    resp = make_response(f.serialise())
    resp.mimetype = "application/atom+xml"
    return resp


def get_feed(base_url=None):
    """
    Main method for generating the feed.  Gets all of the settings
    out of config and returns the feed object, which can then
    be serialised and delivered by the web layer

    :param base_url:    The base url to include in the feed metadata
    :return:    AtomFeed object
    """
    max_size = app.config.get("MAX_FEED_ENTRIES", 20)
    max_age = app.config.get("MAX_FEED_ENTRY_AGE", 2592000)
    from_date = (datetime.now() - timedelta(0, max_age)).strftime("%Y-%m-%dT%H:%M:%SZ")

    dao = models.AtomRecord()
    records = dao.list_records(from_date, max_size)

    title = app.config.get("FEED_TITLE", "untitled")
    url = base_url
    generator = app.config.get('FEED_GENERATOR', "")
    icon = app.config.get("FEED_LOGO", "")
    logo = app.config.get("FEED_LOGO", "")
    link = app.config.get('BASE_URL', "")
    rights = app.config.get('FEED_LICENCE', "")

    xwalk = AtomCrosswalk()
    f = AtomFeed(title, url, generator, icon, logo, link, rights)

    for record in records:
        entry = xwalk.crosswalk(record)
        f.add_entry(entry)

    return f


class AtomFeed(object):
    ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
    ATOM = "{%s}" % ATOM_NAMESPACE
    NSMAP = {None: ATOM_NAMESPACE}

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
        
        entry_dates = list(self.entries.keys())
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

        if "related" in e:
            rel = etree.SubElement(entry, self.ATOM + "link")
            rel.set("rel", "related")
            rel.set("href", e['related'])
        
        rights = etree.SubElement(entry, self.ATOM + "rights")
        rights.text = e['rights']
        
        summary = etree.SubElement(entry, self.ATOM + "summary")
        summary.set("type", "text")
        summary.text = e['summary']
        
        title = etree.SubElement(entry, self.ATOM + "title")
        title.text = e['title']
        
        updated = etree.SubElement(entry, self.ATOM + "updated")
        updated.text = e['updated']
