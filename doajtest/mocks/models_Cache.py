class InMemoryCache(object):
    __type__ = "cache"
    __memory__ = {}

    @classmethod
    def get_site_statistics(cls):
        return None

    @classmethod
    def cache_site_statistics(cls, stats):
        pass

    @classmethod
    def cache_csv(cls, url):
        cls.__memory__["csv"] = {
            "url": url
        }

    @classmethod
    def get_latest_csv(cls):
        return cls.__memory__["csv"]

    @classmethod
    def cache_sitemap(cls, filename):
        cls.__memory__["sitemap"] = {
            "filename" : filename
        }

    @classmethod
    def cache_nth_sitemap(cls, n, url):
        cls.__memory__["sitemap" + str(n)] = {
            "filename": url
        }

    @classmethod
    def get_sitemap(cls, n):
        return cls.__memory__["sitemap" + str(n)]

    @classmethod
    def get_latest_sitemap(cls):
        return cls.__memory__["sitemap"]

    @classmethod
    def cache_public_data_dump(cls, article_url, article_size, journal_url, journal_size):
        cls.__memory__["public_data_dump"] = {
            "article": {"url" : article_url, "size" : article_size},
            "journal": {"url" : journal_url, "size" : journal_size}
        }

    @classmethod
    def get_public_data_dump(cls):
        return cls.__memory__["public_data_dump"]

    def is_stale(self):
        pass

    def marked_regen(self):
        pass

    @classmethod
    def pull(cls, id):
        return cls.__memory__.get(id)

class ModelCacheMockFactory(object):
    @classmethod
    def in_memory(cls):
        return InMemoryCache