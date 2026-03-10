""" The cache contains file metadata for the sitemap, journal csv, and the public data dump. It also holds site stats
 for the front page """

from portality.dao import DomainObject
from portality.core import app
from portality.lib import dates
from portality.lib.dates import DEFAULT_TIMESTAMP_VAL


class Cache(DomainObject):
    __type__ = "cache"

    @classmethod
    def get_site_statistics(cls):
        rec = cls.pull("site_statistics")
        if rec is not None:
            try:
                return {
                    "journals": rec.data.get("journals"),
                    "countries": rec.data.get("countries"),
                    "abstracts": rec.data.get("abstracts"),
                    "no_apc": rec.data.get("no_apc"),
                    "new_journals": rec.data.get("new_journals")
                }
            except AttributeError:
                pass    # Return None below

        # if we get to here, then we don't return the cache
        return None

    @classmethod
    def cache_site_statistics(cls, stats):
        cobj = cls(**stats)
        cobj.set_id("site_statistics")
        cobj.save()

    @classmethod
    def cache_csv(cls, url):
        cobj = cls(**{
            "url": url
        })
        cobj.set_id("csv")
        cobj.save()

    @classmethod
    def get_latest_csv(cls):
        return cls.pull("csv")

    @classmethod
    def cache_nth_sitemap(cls, n, url):
        cobj = cls(**{
            "filename": url
        })
        cobj.set_id("sitemap"+str(n))
        cobj.save()

    @classmethod
    def get_sitemap(cls, n):
        rec = cls.pull("sitemap"+str(n))
        if rec is None:
            return None
        return rec.get("filename")

    @classmethod
    def cache_sitemap_indexes(cls, urls):
        """Cache multiple sitemap index URLs"""
        for idx, url in enumerate(urls):
            cobj = cls(**{
                "filename": url
            })
            cobj.set_id(f"sitemap_index_{idx}")
            cobj.save()

    @classmethod
    def get_sitemap_index(cls, n):
        """Get a specific sitemap index URL"""
        rec = cls.pull(f"sitemap_index_{n}")
        if rec is None:
            return None
        return rec.get("filename")

    @classmethod
    def cache_public_data_dump(cls, article_container, article_filename, article_url, article_size,
                                    journal_container, journal_filename, journal_url, journal_size):
        cobj = cls(**{
            "article": {
                "container": article_container,
                "filename": article_filename,
                "url" : article_url,
                "size" : article_size
            },
            "journal": {
                "container": journal_container,
                "filename": journal_filename,
                "url" : journal_url,
                "size" : journal_size
            }
        })
        cobj.set_id("public_data_dump")
        cobj.save()

    @classmethod
    def get_public_data_dump(cls):
        return cls.pull("public_data_dump")

    def marked_regen(self):
        return self.data.get("regen", False)
