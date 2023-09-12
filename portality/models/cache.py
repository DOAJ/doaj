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
        returnable = rec is not None
        if rec is not None:
            if rec.is_stale():
                returnable = False

        # if the cache exists and is in date (or is otherwise returnable), then explicilty build the
        # cache object and return it.  If we are read-only mode, then we always return the current stats
        # since the cache won't be allowed to store the regenerated ones
        try:
            if returnable or app.config.get("READ_ONLY_MODE", False):
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
    def cache_sitemap(cls, url):
        cobj = cls(**{
            "filename" : url
        })
        cobj.set_id("sitemap")
        cobj.save()

    @classmethod
    def get_latest_sitemap(cls):
        rec = cls.pull("sitemap")
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

    def is_stale(self):
        if not self.last_updated:
            lu = DEFAULT_TIMESTAMP_VAL
        else:
            lu = self.last_updated

        lu = dates.parse(lu)
        now = dates.now()
        dt = now - lu

        # compatibility with Python 2.6
        if hasattr(dt, 'total_seconds'):
            total_seconds = dt.total_seconds()
        else:
            total_seconds = (dt.microseconds + (dt.seconds + dt.days * 24 * 3600) * 10**6) / 10**6

        return total_seconds > app.config.get("SITE_STATISTICS_TIMEOUT")

    def marked_regen(self):
        return self.data.get("regen", False)
