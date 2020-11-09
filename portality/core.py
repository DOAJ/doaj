import os
import threading

from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_cors import CORS
from jinja2 import FileSystemLoader
from lxml import etree

from portality import settings, constants
from portality.bll import exceptions
from portality.error_handler import setup_error_logging
from portality.lib import es_data_mapping

import esprit

login_manager = LoginManager()


@login_manager.user_loader
def load_account_for_login_manager(userid):
    from portality import models
    out = models.Account.pull(userid)
    return out


def create_app():
    app = Flask(__name__)
    configure_app(app)
    setup_error_logging(app)
    setup_jinja(app)
    app.config["LOAD_CROSSREF_THREAD"] = threading.Thread(target=load_crossref_schema, args=(app, ), daemon=True)
    app.config["LOAD_CROSSREF_THREAD"].start()
    login_manager.init_app(app)
    CORS(app)
    initialise_apm(app)
    DebugToolbarExtension(app)
    return app


def configure_app(app):
    """
    Configure the DOAJ from:
     a) the settings.py file
     b) the <env>.cfg file
     c) the local secrets config in app.cfg

    Later imports have precedence, so e.g. app.cfg will override the same setting in production.cfg and settings.py.
    """

    # import for settings.py
    app.config.from_object(settings)

    # import from <env>.cfg
    here = os.path.dirname(os.path.abspath(__file__))
    app.config['DOAJENV'] = get_app_env(app)
    config_path = os.path.join(os.path.dirname(here), app.config['DOAJENV'] + '.cfg')
    print('Running in ' + app.config['DOAJENV'])  # the app.logger is not set up yet (?)
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path)
        print('Loaded environment config from ' + config_path)

    # import from app.cfg
    config_path = os.path.join(os.path.dirname(here), 'app.cfg')
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path)
        print('Loaded secrets config from ' + config_path)


def get_app_env(app):
    if not app.config.get('VALID_ENVIRONMENTS'):
        raise Exception('VALID_ENVIRONMENTS must be set in the config. There shouldn\'t be a reason to change it in different set ups, or not have it.')

    env = os.getenv('DOAJENV')
    if not env:
        envpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../.env')
        if os.path.exists(envpath):
            with open(envpath, 'r') as f:
                env = f.readline().strip()

    if not env or env not in app.config['VALID_ENVIRONMENTS']:
        raise Exception(
"""
Set the DOAJENV environment variable when running the app, guessing is futile and fraught with peril.
DOAJENV=test python portality/app.py
to run the app will do.
Or use the supervisord options - put this in the config: environment= DOAJENV="test" .

Finally, you can create a file called .env with the text e.g. 'dev' in the root of the repo.
Recommended only for dev environments so you don't have to bother specifying it each time you run a script or test.

Valid values are: {valid_doajenv_vals}

You can put environment-specific secret settings in <environment>.cfg , e.g. dev.cfg .

The environment specified in the DOAJENV environment variable will override that specified in the
application configuration (settings.py or app.cfg).
""".format(valid_doajenv_vals=', '.join(app.config['VALID_ENVIRONMENTS']))
        )
    return env


def load_crossref_schema(app):
    schema_path = app.config["SCHEMAS"].get("crossref")

    if not app.config.get("CROSSREF_SCHEMA"):
        try:
            schema_doc = etree.parse(schema_path)
            schema = etree.XMLSchema(schema_doc)
            app.config["CROSSREF_SCHEMA"] = schema
        except Exception as e:
            raise exceptions.IngestException(
                message="There was an error attempting to load schema from " + schema_path, inner=e)


def create_es_connection(app):
    # temporary logging config for debugging index-per-type
    #import logging
    #esprit.raw.configure_logging(logging.DEBUG)

    # make a connection to the index
    if app.config['ELASTIC_SEARCH_INDEX_PER_TYPE']:
        conn = esprit.raw.Connection(host=app.config['ELASTIC_SEARCH_HOST'], index='')
    else:
        conn = esprit.raw.Connection(app.config['ELASTIC_SEARCH_HOST'], app.config['ELASTIC_SEARCH_DB'])

    return conn


def mutate_mapping(conn, type, mapping):
    """ When we are using an index-per-type connection change the mappings to be keyed 'doc' rather than the type """
    if conn.index_per_type:
        try:
            mapping[esprit.raw.INDEX_PER_TYPE_SUBSTITUTE] = mapping.pop(type)
        except KeyError:
            # Allow this mapping through unaltered if it isn't keyed by type
            pass

        # Add the index prefix to the mapping as we create the type
        type = app.config['ELASTIC_SEARCH_DB_PREFIX'] + type
    return type


def put_mappings(conn, mappings):
    # get the ES version that we're working with
    es_version = app.config.get("ELASTIC_SEARCH_VERSION", "1.7.5")

    # for each mapping (a class may supply multiple), create a mapping, or mapping and index
    for key, mapping in iter(mappings.items()):
        altered_key = mutate_mapping(conn, key, mapping)
        ix = conn.index or altered_key
        if not esprit.raw.type_exists(conn, altered_key, es_version=es_version):
            r = esprit.raw.put_mapping(conn, altered_key, mapping, es_version=es_version)
            print("Creating ES Type + Mapping in index {0} for {1}; status: {2}".format(ix, key, r.status_code))
        else:
            print("ES Type + Mapping already exists in index {0} for {1}".format(ix, key))


def initialise_index(app, conn):
    if not app.config['INITIALISE_INDEX']:
        app.logger.warn('INITIALISE_INDEX config var is not True, initialise_index command cannot run')
        return

    if app.config.get("READ_ONLY_MODE", False) and app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        app.logger.warn("System is in READ-ONLY mode, initialise_index command cannot run")
        return

    # get the app mappings
    mappings = es_data_mapping.get_mappings(app)

    # Send the mappings to ES
    put_mappings(conn, mappings)


def initialise_apm(app):
    if app.config.get('ENABLE_APM', False):
        from elasticapm.contrib.flask import ElasticAPM
        app.logger.info("Configuring Elastic APM")
        apm = ElasticAPM(app, logging=True)


def setup_jinja(app):
    '''Add jinja extensions and other init-time config as needed.'''

    app.jinja_env.add_extension('jinja2.ext.do')
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    app.jinja_env.globals['getattr'] = getattr
    app.jinja_env.globals['type'] = type
    app.jinja_env.globals['constants'] = constants
    app.jinja_env.loader = FileSystemLoader([app.config['BASE_FILE_PATH'] + '/templates',
                                             os.path.dirname(app.config['BASE_FILE_PATH']) + '/static_content/_site',
                                             os.path.dirname(app.config['BASE_FILE_PATH']) + '/static_content/_includes',
                                             os.path.dirname(app.config['BASE_FILE_PATH']) + '/static_content/_layouts'])


    # a jinja filter that prints to the Flask log
    def jinja_debug(text):
        print(text)
        return ''
    app.jinja_env.filters['debug']=jinja_debug


app = create_app()
es_connection = create_es_connection(app)
