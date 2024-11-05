import re
import os
from datetime import datetime

from lxml import etree

from portality import models
from portality.bll import exceptions
from portality.core import app
from portality.lib import nav, dates
from portality.lib.argvalidate import argvalidate
from portality.lib.dates import FMT_DATETIME_SHORT, FMT_DATETIME_STD
from portality.store import StoreFactory, prune_container
from portality.util import get_full_url_safe
from portality.view.doaj import sitemap

NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
IN_DOAJ = {
    "query": {
        "bool": {
            "must": [
                {"term": {"admin.in_doaj": True}}
            ]
        }
    }
}
NMSP = "http://www.sitemaps.org/schemas/sitemap/0.9"
MAX_FILE_SIZE = (49 * 1024 * 1024)
MAX_URL_COUNT = 49000

class SitemapGenerator:

    def __init__(self, filename_prefix, temp_store, main_store, container_id):
        self.file_idx = 0
        self.url_count = 0
        self.current_file_path = None
        self.current_filename = None
        self.file = None
        self.sitemap_files = []
        self.filename_prefix = filename_prefix
        self.temp_store = temp_store
        self.main_store = main_store
        self.container_id = container_id
        self.change_freq = app.config.get("TOC_CHANGEFREQ", "monthly")
        self.create_sitemap_file()

    def add_url(self, url, lastmod=None):
        self.write_url_element(url, lastmod=lastmod)
        self.check_and_finalize_file()
        self.url_count += 1

    def write_url_element(self, loc, lastmod=None):
        url_ele = f"""
    <url>
        <loc>{loc}</loc>
        <changefreq>{self.change_freq}</changefreq>"""
        if lastmod is not None:
            url_ele += f"\n        <lastmod>{lastmod}</lastmod>"
        url_ele += "\n    </url>"
        self.file.write(url_ele)

    def create_sitemap_file(self):
        self.current_filename = f'{self.filename_prefix}_{self.file_idx}_utf8.xml'
        self.current_file_path = os.path.join(self.temp_store, self.current_filename)
        self.file =  open(self.current_file_path, "w")
        self.file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.file.write('<urlset xmlns="'+NMSP+'">')
        self.file_idx += 1

    def finalize_sitemap_file(self):
        self.file.write('\n</urlset>\n')
        self.file.close()
        self.main_store.store(self.container_id, self.current_filename, source_path=self.current_file_path)
        self.sitemap_files.append(self.main_store.url(self.container_id, self.current_filename))

    def check_and_finalize_file(self):
        file_size = os.path.getsize(self.current_file_path)
        if file_size >= MAX_FILE_SIZE or self.url_count >= MAX_URL_COUNT:
            self.finalize_sitemap_file()
            self.create_sitemap_file()
            self.url_count = 0

    def get_url_count(self):
        return self.url_count

    def get_sitemap_files(self):
        return self.sitemap_files

class SiteService(object):

    def sitemap(self, prune: bool = True):
        """
        Generate the sitemap
        ~~Sitemap:Feature~~
        :return:
        """
        argvalidate("csv", [
            {"arg": prune, "allow_none": False, "arg_name": "prune"}
        ], exceptions.ArgumentException)

        action_register = []
        base_url = app.config.get("BASE_URL")
        if not base_url.endswith("/"):
            base_url += "/"

        run_start_time = dates.now_str(FMT_DATETIME_SHORT)
        lastmod_date = dates.now_str(FMT_DATETIME_STD)

        filename_prefix = 'sitemap_doaj_' + run_start_time
        cache_container_id = app.config.get("STORE_CACHE_CONTAINER")
        container_id = os.path.join(cache_container_id,filename_prefix)

        total_static_pages = 0
        total_journals_count = 0
        total_articles_count = 0

        # ~~->FileStore:Feature~~
        tmpStore = StoreFactory.tmp()
        mainStore = StoreFactory.get("cache")

        # temporary directory
        tmp_store_dir = tmpStore.path(container_id, '', create_container=True)
        # Create the directories if they don't exist
        os.makedirs(tmp_store_dir, exist_ok=True)

        sitemap_generator = SitemapGenerator(filename_prefix, tmp_store_dir, mainStore, container_id)

        # Generating URLs for static pages
        _entries = nav.get_nav_entries()
        _routes = nav.yield_all_route(_entries)
        _urls = (get_full_url_safe(r) for r in _routes)
        _urls = filter(None, _urls)
        _urls = set(_urls)
        _urls = sorted(_urls)

        #static pages
        for u in _urls:
            sitemap_generator.add_url(u)
            total_static_pages += 1

        # Generating URLs for journals and articles
        for j in models.Journal.all_in_doaj():
            toc_loc = base_url + "toc/" + j.toc_id
            sitemap_generator.add_url(toc_loc, lastmod=j.last_updated)
            toc_art_loc = base_url + "toc/" + j.toc_id + "/articles"
            sitemap_generator.add_url(toc_art_loc)
            total_journals_count += 1

        # Generating URLs for articles
        for a in models.Article.iterate(q=IN_DOAJ, keepalive='5m'):
            article_loc = base_url + "article/" + a.id
            sitemap_generator.add_url(article_loc, lastmod=a.last_updated)
            total_articles_count += 1

        # check last sitemap
        if sitemap_generator.get_url_count() > 0:
            sitemap_generator.finalize_sitemap_file()

        # Create sitemap index file
        sitemap_index_filename = f'sitemap_index_doaj_{run_start_time}_utf8.xml'
        sitemap_index_path = os.path.join(tmp_store_dir, sitemap_index_filename)
        with open(sitemap_index_path, "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            sitemap_count = 0
            for sitemap_url in sitemap_generator.get_sitemap_files():
                f.write(f"    <sitemap>\n")
                f.write(f"        <loc>{base_url}sitemap{sitemap_count}.xml</loc>\n")
                f.write(f"        <lastmod>{lastmod_date}</lastmod>\n")
                f.write(f"    </sitemap>\n")
                # Cache the sitemap
                models.Cache.cache_nth_sitemap(sitemap_count, sitemap_url)
                sitemap_count += 1
            f.write('</sitemapindex>\n')

            # Delete any previous cache. Usually this may not be the situation but check
            # if there are any previous sitemap available and delete
            while True:
                cache = models.Cache.pull("sitemap"+str(sitemap_count))
                if cache:
                    cache.delete()
                else:
                    break
                sitemap_count += 1


        mainStore.store(container_id, sitemap_index_filename, source_path=sitemap_index_path)
        index_url = mainStore.url(container_id, sitemap_index_filename)

        action_register.append("Sitemap index written to store with url {x}".format(x=index_url))

        # Prune old sitemaps if required
        if prune:
            def sort(filelist):
                rx = r"^sitemap_doaj_(\d{8})_(\d{4})"

                matched_dates = [
                    (filename, datetime.strptime(match.groups()[0]+"_"+match.groups()[1], FMT_DATETIME_SHORT))
                    for filename in filelist
                    if (match := re.match(rx, filename))
                ]
                return [x for x, _ in sorted(matched_dates, key=lambda x: x[1], reverse=True)]


            def _filter(filename):
                return filename.startswith("sitemap_")

            action_register += prune_container(mainStore, cache_container_id, sort, filter=_filter, keep=2)
            action_register += prune_container(tmpStore, cache_container_id, sort, filter=_filter, keep=2)

        # Update the cache record to point to the new sitemap index and all sitemaps
        models.Cache.cache_sitemap(index_url)

        action_register.append(f"Static pages count : {total_static_pages}")
        action_register.append(f"Journal URLs count : {total_journals_count}")
        action_register.append(f"Article URLs count : {total_articles_count}")

        return index_url, action_register
