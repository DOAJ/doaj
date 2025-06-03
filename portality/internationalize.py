from urllib.parse import urlencode

from flask import g, request, redirect, url_for, session
from flask_babel import Babel

DEFAULT_LOCALE = "en"
DEFAULT_TIMEZONE = "UTC"
LANGUAGES = ['en', 'fr']
INCLUDE_ROUTES = {
        'apply'
    }

def locale_middleware_with_query_params():
    # Get locale from query parameter instead of URL path
    lang = request.args.get('lang', DEFAULT_LOCALE)
    if lang not in LANGUAGES:
        lang = DEFAULT_LOCALE
    g.lang = lang  # Store in flask.g for easy access
    return None  # Continue with request

def redirect_url(lang: str = DEFAULT_LOCALE):
    query_params = request.args.to_dict()
    query_params.pop('lang', None)  # remove lang from query params which is not required
    url_to_redirect = f"/{lang}{request.path}"
    if query_params:
        url_to_redirect = f"{url_to_redirect}?{urlencode(query_params)}"
    return redirect(url_to_redirect)

def locale_middleware():
    try:
        # Redirect for included routes
        if request.path and any(request.path.startswith(f'/{route}') for route in INCLUDE_ROUTES):
            # update selected language
            lang = request.args.get('lang')
            if lang:
                if lang in LANGUAGES:
                    session['lang'] = lang
                return redirect_url(lang)

            if get_url_locale() is None:
                return redirect_url(get_session_locale())

    except RuntimeError:
        pass
    return None

def get_url_locale():
    # Get locale from URL
    path_parts = request.path.split('/')
    if len(path_parts) > 1:
        url_locale = path_parts[1]
        if url_locale in LANGUAGES:
            session['lang'] = url_locale
            return url_locale
    return None

def get_session_locale():
    if 'lang' in session:
        lang = session.get('lang')
        if lang in LANGUAGES:
            return lang
    session['lang'] = DEFAULT_LOCALE
    return DEFAULT_LOCALE

def get_locale():
    lang = get_url_locale()
    if lang is None:
        return get_session_locale()

    return lang

def get_timezone():
    user = getattr(g, 'user', None)
    if user is not None:
        return user.timezone

    return DEFAULT_TIMEZONE


def url_for_other_page(endpoint, **kwargs):
    if 'lang' not in kwargs:
        kwargs['lang'] = g.get('lang', DEFAULT_LOCALE)
    return url_for(endpoint, **kwargs)

def internationalize(app):
    # Initialize internationalization using Flask-Babel
    app.config['BABEL_DEFAULT_LOCALE'] = DEFAULT_LOCALE  # Default
    app.config['BABEL_DEFAULT_TIMEZONE'] = DEFAULT_TIMEZONE
    app.config['LANGUAGES'] = LANGUAGES
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = "translations"

    app.babel = Babel(app, locale_selector=get_locale, timezone_selector=get_timezone)

    # Add locale middleware
    app.before_request(locale_middleware)

    # Add to template context
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page

