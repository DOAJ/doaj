import re
from datetime import datetime

from lxml import etree

from portality import models
from portality.bll import exceptions
from portality.core import app
from portality.lib import nav
from portality.lib.argvalidate import argvalidate
from portality.store import StoreFactory, prune_container
from portality.util import get_full_url_safe

NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def create_simple_sub_element(parent, element_name, text=None):
    """ create and attach simple text element to argument *parent*
    """
    loc = etree.SubElement(parent, NS + element_name)
    if text is not None:
        loc.text = text
    return loc


def create_url_element(parent, loc, change_freq, lastmod=None):
    """ create and attach url element to argument *parent*
    """
    url_ele = etree.SubElement(parent, NS + "url")

    create_simple_sub_element(url_ele, 'loc', loc)
    if lastmod is not None:
        create_simple_sub_element(url_ele, "lastmod", lastmod)
    create_simple_sub_element(url_ele, "changefreq", change_freq)

    return url_ele


class SiteService(object):
    def sitemap(self, prune: bool = True):
        """
        Generate the sitemap
        ~~Sitemap:Feature~~
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("csv", [
            {"arg": prune, "allow_none": False, "arg_name": "prune"}
        ], exceptions.ArgumentException)

        action_register = []

        base_url = app.config.get("BASE_URL")
        if not base_url.endswith("/"):
            base_url += "/"

        # ~~-> FileStoreTemp:Feature~~
        filename = 'sitemap__doaj_' + datetime.strftime(datetime.utcnow(), '%Y%m%d_%H%M') + '_utf8.xml'
        container_id = app.config.get("STORE_CACHE_CONTAINER")
        tmpStore = StoreFactory.tmp()
        out = tmpStore.path(container_id, filename, create_container=True, must_exist=False)

        toc_changefreq = app.config.get("TOC_CHANGEFREQ", "monthly")

        NSMAP = {None: "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urlset = etree.Element(NS + "urlset", nsmap=NSMAP)

        counter = 0

        # do the static pages
        _entries = nav.get_nav_entries()
        _routes = nav.yield_all_route(_entries)
        _urls = (get_full_url_safe(r) for r in _routes)
        _urls = filter(None, _urls)
        _urls = set(_urls)
        _urls = sorted(_urls)
        for u in _urls:
            create_url_element(urlset, u, toc_changefreq)
            counter += 1

        # do all the journal ToCs
        for j in models.Journal.all_in_doaj():
            # first create an entry purely for the journal
            toc_loc = base_url + "toc/" + j.toc_id
            create_url_element(urlset, toc_loc, toc_changefreq, lastmod=j.last_updated)
            counter += 1

        # log to the screen
        action_register.append("{x} urls written to sitemap".format(x=counter))

        # save it into the temp store
        tree = etree.ElementTree(urlset)
        with open(out, "wb") as f:
            tree.write(f, encoding="UTF-8", xml_declaration=True, pretty_print=True)

        # ~~->FileStore:Feature~~
        mainStore = StoreFactory.get("cache")
        try:
            mainStore.store(container_id, filename, source_path=out)
            url = mainStore.url(container_id, filename)
        finally:
            tmpStore.delete_file(container_id,
                                 filename)  # don't delete the container, just in case someone else is writing to it

        action_register.append("Sitemap written to store with url {x}".format(x=url))

        # remove all but the two latest sitemaps
        if prune:
            def sort(filelist):
                rx = "sitemap__doaj_(.+?)_utf8.xml"
                return sorted(filelist,
                              key=lambda x: datetime.strptime(re.match(rx, x).groups(1)[0], '%Y%m%d_%H%M'),
                              reverse=True)

            def _filter(filename):
                return filename.startswith("sitemap__")

            action_register += prune_container(mainStore, container_id, sort, filter=_filter, keep=2)

        # update the ES record to point to the new file
        # ~~->Cache:Feature~~
        models.Cache.cache_sitemap(url)
        return url, action_register
