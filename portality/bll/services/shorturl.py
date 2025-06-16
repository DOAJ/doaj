import random
import string
from typing import Optional
from urllib.parse import urlparse

from portality import models
from portality.core import app
from portality.models.shortened_url import AliasQuery, UrlQuery, CountWithinDaysQuery

class UrlShortenerLimitExceeded(Exception):
    pass

class InvalidURL(Exception):
    pass


class ShortUrlService:
    ALIAS_CHARS = string.ascii_letters + string.digits

    def check_url_count(self, days=7, limit=100_000):
        n_created = models.ShortenedUrl.hit_count(CountWithinDaysQuery(
            app.config.get("URLSHORT_LIMIT_WITHIN_DAYS", days)
        ).query())
        n_created_limit = app.config.get("URLSHORT_LIMIT", limit)

        if n_created >= n_created_limit:
            msg = f"Url shortener limit reached: [{n_created=}] >= [{n_created_limit=}]"
            app.logger.warning(msg)
            raise UrlShortenerLimitExceeded(msg)

    def validate_url(self, url):
        # validate url
        hostname = urlparse(url).hostname
        if not any((hostname == d or hostname.endswith(f".{d}"))
                   for d in app.config.get("URLSHORT_ALLOWED_SUPERDOMAINS", [])):
            msg = f"Invalid url shorten request: {url}"
            app.logger.warning(msg)
            raise InvalidURL(msg)

    def get_short_url(self, url: str, throttled=True, validate=True) -> models.ShortenedUrl:
        """
        create or find a shorted url from the given url

        Parameters
        ----------
        url

        Returns
        -------
            shortened URL
        """
        if throttled:
            self.check_url_count()

        if validate:
            self.validate_url(url)

        shortened_url = self.find_shortened_url(url)
        if shortened_url:
            return shortened_url

        alias = self.create_new_alias()
        record = models.ShortenedUrl(url=url, alias=alias)
        record.save()
        return record

    def create_new_alias(self, n_retry=5) -> str:
        alias_len = app.config.get("URLSHORT_ALIAS_LENGTH", 6)
        for _ in range(n_retry):
            alias = ''.join(random.sample(self.ALIAS_CHARS, alias_len))
            cnt = models.ShortenedUrl.hit_count(UrlQuery(alias).query())
            if cnt == 0:
                return alias

        raise ValueError('Could not create a unique alias')

    def find_shortened_url(self, url: str) -> Optional[models.ShortenedUrl]:
        """ find the shorted url from the given url """

        aliases = models.ShortenedUrl.q2obj(q=AliasQuery(url).query())

        if len(aliases) == 0:
            return None

        if len(aliases) > 1:
            app.logger.warning(f'More than one alias found for url[{url}] n[{len(aliases)}]')

        return aliases[0]

    def find_url_by_alias(self, alias: str) -> Optional[str]:
        """ find the original url from the given alias """

        urls = models.ShortenedUrl.q2obj(q=UrlQuery(alias).query())
        n_url = len(urls)
        if n_url == 0:
            return None
        if n_url > 1:
            app.logger.warning(f'More than one URL found for alias[{alias}] n[{n_url}]')

        return urls[0]
