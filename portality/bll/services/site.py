import re
import os
from datetime import datetime

from portality import models
from portality.bll import exceptions
from portality.core import app
from portality.lib import nav, dates
from portality.lib.argvalidate import argvalidate
from portality.lib.dates import FMT_DATETIME_SHORT, FMT_DATETIME_STD
from portality.store import StoreFactory, prune_container
from portality.util import get_full_url_safe
from collections.abc import Iterable

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

class ChunkedURLListFileGenerator(Iterable):
    def __init__(self, directory, filename_prefix, temp_store, main_store, container_id, max_file_size=MAX_FILE_SIZE, max_url_count=MAX_URL_COUNT):
        self.file_idx = 0
        self.url_count = 0
        self.current_file_path = None
        self.current_filename = None
        self.file = None
        self.max_file_size = max_file_size
        self.max_url_count = max_url_count
        self.directory = directory
        self.filename_prefix = filename_prefix
        self.temp_store = temp_store
        self.main_store = main_store
        self.container_id = container_id
        self.files = []

        self.create_file()

    def add_url(self, url, lastmod=None):
        self.write_url_element(url, lastmod=lastmod)
        self.check_and_finalize_file()
        self.url_count += 1

    def create_file(self):
        self.current_filename = os.path.join(self.directory, f'{self.filename_prefix}_{self.file_idx}_utf8.xml')
        self.current_file_path = os.path.join(self.temp_store, self.current_filename)
        self.file = open(self.current_file_path, "w")
        self.file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.write_list_start_tag()
        self.file_idx += 1

    def check_and_finalize_file(self):
        file_size = os.path.getsize(self.current_file_path)
        if file_size >= self.max_file_size or self.url_count >= self.max_url_count:
            self.finalize_file()
            self.create_file()
            self.url_count = 0

    def finalize_file(self):
        self.write_list_end_tag()
        self.file.close()
        self.main_store.store(self.container_id, self.current_filename, source_path=self.current_file_path)
        self.files.append(self.main_store.url(self.container_id, self.current_filename))

    def get_url_count(self):
        return self.url_count

    def get_files(self):
        return self.files

    def __iter__(self):
        return iter(self.files)

    ###########################################
    ## functions to be implemented by subclasses

    def write_url_element(self, loc, lastmod=None):
        raise NotImplementedError("Subclasses must implement write_url_element")

    def write_list_start_tag(self):
        raise NotImplementedError("Subclasses must implement write_list_start_tag")

    def write_list_end_tag(self):
        raise NotImplementedError("Subclasses must implement write_list_end_tag")


class SitemapGenerator(ChunkedURLListFileGenerator):

    def __init__(self, directory, filename_prefix, temp_store, main_store, container_id):
        super(SitemapGenerator, self).__init__(directory, filename_prefix, temp_store, main_store, container_id)
        self.change_freq = app.config.get("TOC_CHANGEFREQ", "monthly")

    def write_url_element(self, loc, lastmod=None):
        url_ele = f"""
    <url>
        <loc>{loc}</loc>
        <changefreq>{self.change_freq}</changefreq>"""
        if lastmod is not None:
            url_ele += f"\n        <lastmod>{lastmod}</lastmod>"
        url_ele += "\n    </url>"
        self.file.write(url_ele)

    def write_list_start_tag(self):
        self.file.write('<urlset xmlns="'+NMSP+'">')

    def write_list_end_tag(self):
        self.file.write('\n</urlset>\n')


class SitemapIndexGenerator(ChunkedURLListFileGenerator):

    def __init__(self, directory, filename_prefix, temp_store, main_store, container_id):
        max_entries = app.config.get("SITEMAP_INDEX_MAX_ENTRIES", 50000)
        super(SitemapIndexGenerator, self).__init__(directory, filename_prefix, temp_store, main_store, container_id, max_url_count=max_entries)

    def write_url_element(self, loc, lastmod=None):
        self.file.write(f"    <sitemap>\n")
        self.file.write(f"        <loc>{loc}</loc>\n")
        if lastmod is not None:
            self.file.write(f"        <lastmod>{lastmod}</lastmod>\n")
        self.file.write(f"    </sitemap>\n")

    def write_list_start_tag(self):
        self.file.write('<sitemapindex xmlns="' + NMSP + '">\n')

    def write_list_end_tag(self):
        self.file.write('\n</sitemapindex>\n')


class SiteService(object):

    @staticmethod
    def sitemap(prune: bool = True):
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
        directory = 'sitemap_doaj_' + run_start_time
        filename_prefix = "sitemap"
        container_id = app.config.get("STORE_CACHE_CONTAINER")

        total_static_pages = 0
        total_journals_count = 0
        total_articles_count = 0

        # ~~->FileStore:Feature~~
        tmpStore = StoreFactory.tmp()
        mainStore = StoreFactory.get("cache")

        # temporary directory
        tmp_store_dir = tmpStore.path(container_id, '', create_container=True)
        # Create the directories if they don't exist
        os.makedirs(os.path.join(tmp_store_dir,directory) , exist_ok=True)

        sitemap_generator = SitemapGenerator(directory, filename_prefix, tmp_store_dir, mainStore, container_id)

        # Generating URLs for static pages
        _entries = nav.get_nav_entries()
        _routes = nav.yield_all_route(_entries)
        _urls = (get_full_url_safe(r) for r in _routes)
        _urls = filter(None, _urls)
        _urls = set(_urls)
        _urls = sorted(_urls)

        # static pages
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
            sitemap_generator.finalize_file()

        # Create sitemap index file(s)
        sitemap_files = sitemap_generator.get_files()
        lastmod_date = dates.now_str(FMT_DATETIME_STD)

        sitemap_prefix = "sitemap_index"
        index_generator = SitemapIndexGenerator(directory, sitemap_prefix, tmp_store_dir, mainStore, container_id)

        for i, sitemap_file in enumerate(sitemap_files):
            public_url = f"{base_url}sitemap{i}.xml"
            index_generator.add_url(public_url, lastmod=lastmod_date)
            models.Cache.cache_nth_sitemap(i, sitemap_file)

        # check the last index
        if index_generator.get_url_count() > 0:
            index_generator.finalize_file()

        index_files = index_generator.get_files()
        models.Cache.cache_sitemap_indexes(index_files)

        # Delete any additional maps from previous cache. Usually this may not be the situation but check
        # Count up any additional cached sitemaps we find and delete them.
        next_sitemap_ix = len(sitemap_files)
        while True:
            cache = models.Cache.pull("sitemap" + str(next_sitemap_ix))
            if cache:
                cache.delete()
            else:
                break
            next_sitemap_ix += 1

        # Prune old sitemap files if required
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

            action_register += prune_container(mainStore, container_id, sort, filter=_filter, keep=2, is_directory=True)
            action_register += prune_container(tmpStore, container_id, sort, filter=_filter, keep=2)

        action_register.append(f"Static pages count : {total_static_pages}")
        action_register.append(f"Journal URLs count : {total_journals_count}")
        action_register.append(f"Article URLs count : {total_articles_count}")

        return index_files, action_register
