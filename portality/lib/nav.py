from typing import Iterable

from portality.core import app


def yield_all_route(entries: Iterable[dict]) -> Iterable[str]:
    """
    :param entries:
    :return: iterable of route name (endpoint)
    """

    for e in entries:
        if 'route' in e:
            yield e['route']
        if 'entries' in e:
            yield from yield_all_route(e['entries'])


def get_nav_entries() -> Iterable[dict]:
    return app.jinja_env.globals.get("data", {}).get('nav', {}).get('entries', [])
