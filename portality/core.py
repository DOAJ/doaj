import os, requests, json
from functools import wraps

from flask import Flask
from flask import request, redirect, url_for, flash, render_template

from portality import settings
from portality.error_handler import setup_error_logging
from flask.ext.login import LoginManager, current_user
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    configure_app(app)
    if app.config['INITIALISE_INDEX']: initialise_index(app)
    setup_error_logging(app)
    setup_jinja(app)
    login_manager.setup_app(app)
    return app

def configure_app(app):
    app.config.from_object(settings)
    # parent directory
    here = os.path.dirname(os.path.abspath( __file__ ))
    config_path = os.path.join(os.path.dirname(here), 'app.cfg')
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path)

    app.config['DOAJENV'] = get_app_env(app)
    config_path = os.path.join(os.path.dirname(here), app.config['DOAJENV'] + '.cfg')
    print 'Running in ' + app.config['DOAJENV']  # the app.logger is not set up yet (?)
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path)
        print 'Loaded final config from ' + config_path

def get_app_env(app):
    if not app.config.get('VALID_ENVIRONMENTS'):
        raise Exception('VALID_ENVIRONMENTS must be set in the config. There shouldn\'t be a reason to change it in different set ups, or not have it.')

    env = os.getenv('DOAJENV')
    if not env:
        env = app.config.get('DOAJENV')

    if not env:
        raise Exception(
"""
Set the DOAJENV environment variable when running the app please, guessing is futile and fraught with peril.
DOAJENV=test python portality/app.py
to run the app will do.
Or use the supervisord options - put this in the config: environment= DOAJENV="test" .

Finally, the least preferred approach is to put DOAJENV="dev" in app.cfg in the root of the repo.
Only do this for dev environments so you don't have to bother specifying it each time.

Valid values are: {valid_doajenv_vals}

You can put environment-specific secret settings in <environment>.cfg , e.g. dev.cfg .

The environment specified in the DOAJENV environment variable will override that specified in the
application configuration (settings.py or app.cfg).
""".format(valid_doajenv_vals=', '.join(app.config['VALID_ENVIRONMENTS']))
        )

    return env


def initialise_index(app):
    if app.config.get("READ_ONLY_MODE", False):
        app.logger.warn("System is in READ-ONLY mode, initialise_index command cannot run")
        return

    mappings = app.config["MAPPINGS"]
    i = str(app.config['ELASTIC_SEARCH_HOST']).rstrip('/')
    i += '/' + app.config['ELASTIC_SEARCH_DB']
    for key, mapping in mappings.iteritems():
        # im = i + '/' + key + '/_mapping'  # es 0.x
        im = i + "/_mapping/" + key         # es 1.x
        typeurl = i + "/" + key
        # exists = requests.get(im)         # es 0.x
        exists = requests.head(typeurl)     # es 1.x
        if exists.status_code != 200:
            ri = requests.post(i)
            r = requests.put(im, json.dumps(mapping))
            print key, r.status_code


def setup_jinja(app):
    '''Add jinja extensions and other init-time config as needed.'''

    app.jinja_env.add_extension('jinja2.ext.do')
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    app.jinja_env.globals['getattr'] = getattr
    app.jinja_env.globals['type'] = type

    # a jinja filter that prints to the Flask log
    def jinja_debug(text):
        print text
        return ''
    app.jinja_env.filters['debug']=jinja_debug

app = create_app()


# misc stuff available for importing anywhere

# a decorator to be used elsewhere (or in this file) in the app,
# anywhere where a view f() should be served only over SSL
def ssl_required(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if app.config.get("SSL"):
            if request.is_secure:
                return fn(*args, **kwargs)
            else:
                return redirect(request.url.replace("http://", "https://"))
        
        return fn(*args, **kwargs)
            
    return decorated_view

def restrict_to_role(role):
    if current_user.is_anonymous():
        flash('You are trying to access a protected area. Please log in first.', 'error')
        return redirect(url_for('account.login', next=request.url))

    if not current_user.has_role(role):
        flash('You do not have permission to access this area of the site.', 'error')
        return redirect(url_for('doaj.home'))

def write_required(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if app.config.get("READ_ONLY_MODE", False):
            return render_template("doaj/readonly.html")

        return fn(*args, **kwargs)

    return decorated_view
