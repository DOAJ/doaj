from functools import wraps
from flask import g, request, redirect, url_for, session
from flask_babel import Babel

DEFAULT_LOCALE = "en"
DEFAULT_TIMEZONE = "UTC"
LANGUAGES = ['en', 'fr']

def locale_middleware_with_query_params():
    # Get locale from query parameter instead of URL path
    lang = request.args.get('lang', DEFAULT_LOCALE)
    if lang not in LANGUAGES:
        lang = DEFAULT_LOCALE
    g.lang = lang  # Store in flask.g for easy access
    return None  # Continue with request


def locale_middleware():
    # List of routes that should not be prefixed with locale
    EXEMPT_ROUTES = {
        'static',
        'api',
        '_status',
        'status',
        'our_static'
    }

    # Don't redirect for exempt routes
    if request.path.startswith('/static') or any(request.path.startswith(f'/{route}') for route in EXEMPT_ROUTES):
        return

    # Get locale from URL
    path_parts = request.path.split('/')
    if len(path_parts) > 1:
        url_locale = path_parts[1]
        if url_locale in LANGUAGES:
            return  # Valid locale in URL, continue normally

    # No valid locale in URL, redirect to default locale
    return redirect(f"/{DEFAULT_LOCALE}{request.path}")

def get_locale():
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    # return request.accept_languages.best_match(['de', 'fr', 'en'])
    # Extract the language code from the URL path
    lang = request.path.split('/')[1]
    if lang in LANGUAGES:
        return lang
    return DEFAULT_LOCALE

def get_session_locale():
    lang = DEFAULT_LOCALE
    if 'lang' in session:
        lang = session.get('lang')
    if lang in LANGUAGES:
        return lang
    return DEFAULT_LOCALE

def get_timezone():
    user = getattr(g, 'user', None)
    if user is not None:
        return user.timezone


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

    babel = Babel(app, locale_selector=get_session_locale, timezone_selector=get_timezone)

    # Add locale middleware
    app.before_request(locale_middleware_with_query_params)

    # Add to template context
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page

