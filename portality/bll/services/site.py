from portality.core import app
from portality import models
from portality.store import StoreFactory, prune_container
from datetime import datetime
from portality.lib.argvalidate import argvalidate

from portality.bll import exceptions

from lxml import etree
import re

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
        NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        urlset = etree.Element(NS + "urlset", nsmap=NSMAP)

        counter = 0

        # do the static pages
        statics = app.config.get("STATIC_PAGES", [])
        for path, change in statics:
            if path.startswith("/"):
                path = path[1:]
            stat_loc = base_url + path
            url = etree.SubElement(urlset, NS + "url")
            loc = etree.SubElement(url, NS + "loc")
            loc.text = stat_loc
            cf = etree.SubElement(url, NS + "changefreq")
            cf.text = change
            counter += 1

        # do all the journal ToCs
        for j in models.Journal.all_in_doaj():

            # first create an entry purely for the journal
            toc_loc = base_url + "toc/" + j.toc_id
            lastmod = j.last_updated

            url = etree.SubElement(urlset, NS + "url")
            loc = etree.SubElement(url, NS + "loc")
            loc.text = toc_loc
            if lastmod is not None:
                lm = etree.SubElement(url, NS + "lastmod")
                lm.text = lastmod
            cf = etree.SubElement(url, NS + "changefreq")
            cf.text = toc_changefreq
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
                return sorted(filelist, key=lambda x: datetime.strptime(re.match(rx, x).groups(1)[0], '%Y%m%d_%H%M'), reverse=True)
            def filter(filename):
                return filename.startswith("sitemap__")
            action_register += prune_container(mainStore, container_id, sort, filter=filter, keep=2)

        # update the ES record to point to the new file
        # ~~->Cache:Feature~~
        models.Cache.cache_sitemap(url)
        return url, action_register
