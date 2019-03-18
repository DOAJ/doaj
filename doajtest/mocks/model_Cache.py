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
    def cache_csv(cls, filename):
        pass

    @classmethod
    def get_latest_csv(cls):
        pass

    @classmethod
    def cache_sitemap(cls, filename):
        pass

    @classmethod
    def get_latest_sitemap(cls):
        pass

    @classmethod
    def cache_public_data_dump(cls, article_url, article_size, journal_url, journal_size):
        cls.__memory__["public_data_dump"] = {
            "article": {"url" : article_url, "size" : article_size},
            "journal": {"url" : journal_url, "size" : journal_size}
        }

    @classmethod
    def get_public_data_dump(cls):
        return cls.__memory__["public_data_dump"]

    def mark_for_regen(self):
        pass

    def is_stale(self):
        pass

    def marked_regen(self):
        pass

class ModelCacheMockFactory(object):
    @classmethod
    def in_memory(cls):
        return InMemoryCache