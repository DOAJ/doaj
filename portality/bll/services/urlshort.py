import random
import string
from typing import Optional

from portality import models
from portality.core import app
from portality.models.url_shortener import AliasQuery, UrlQuery
from portality.util import url_for

# global current status of the alias length
ALIAS_CHARS = string.ascii_letters + string.digits


def add_url_shortener(url: str) -> str:
    """
    create or find a shorted url from the given url

    Parameters
    ----------
    url

    Returns
    -------
        shortened URL
    """

    shortened_url = find_shortened_url(url)
    if shortened_url:
        return shortened_url

    alias = create_new_alias()
    models.UrlShortener(url=url, alias=alias).save()

    return parse_shortened_url(alias)


def create_new_alias(n_retry=5) -> str:
    alias_len = app.config.get("URLSHORT_ALIAS_LENGTH")
    for _ in range(n_retry):
        alias = ''.join(random.sample(ALIAS_CHARS, alias_len))
        cnt = models.UrlShortener.hit_count(UrlQuery(alias).query())
        if cnt == 0:
            return alias

    raise ValueError('Could not create a unique alias')


def find_shortened_url(url: str) -> Optional[str]:
    """ find the shorted url from the given url """

    aliases = models.UrlShortener.q2obj(q=AliasQuery(url).query())

    if len(aliases) == 0:
        return None

    if len(aliases) > 1:
        app.logger.warning(f'More than one alias found for url[{url}] n[{len(aliases)}]')

    return parse_shortened_url(aliases[0].alias)


def find_url_by_alias(alias: str) -> Optional[str]:
    """ find the original url from the given alias """

    urls = models.UrlShortener.q2obj(q=UrlQuery(alias).query())
    n_url = len(urls)
    if n_url == 0:
        return None
    if n_url > 1:
        app.logger.warning(f'More than one URL found for alias[{alias}] n[{n_url}]')

    return urls[0].url


def parse_shortened_url(alias: str) -> str:
    """ parse the shortened url from the given alias """
    return app.config.get("BASE_URL") + url_for('doaj.shortened_url', alias=alias)
