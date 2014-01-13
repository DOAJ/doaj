import os, requests, json
from flask import Flask

from portality import settings, secret_settings
from flask.ext.login import LoginManager, current_user
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    configure_app(app)
    if app.config['INITIALISE_INDEX']: initialise_index(app)
    setup_error_logging(app)
    login_manager.setup_app(app)
    return app

def configure_app(app):
    app.config.from_object(settings)
    app.config.from_object(secret_settings)
    # parent directory
    here = os.path.dirname(os.path.abspath( __file__ ))
    config_path = os.path.join(os.path.dirname(here), 'app.cfg')
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path)

def initialise_index(app):
    mappings = app.config["MAPPINGS"]
    i = str(app.config['ELASTIC_SEARCH_HOST']).rstrip('/')
    i += '/' + app.config['ELASTIC_SEARCH_DB']
    for key, mapping in mappings.iteritems():
        im = i + '/' + key + '/_mapping'
        exists = requests.get(im)
        if exists.status_code != 200:
            ri = requests.post(i)
            r = requests.put(im, json.dumps(mapping))
            print key, r.status_code

def setup_error_logging(app):
    if not app.debug:
        # Custom logging WILL BE IGNORED by Flask if app.debug == True -
        # even if you remove the condition above this comment.
        import logging, sys
        ADMINS = app.config.get('ADMINS', [])
        if not ADMINS:
            e = app.config.get('ADMIN_EMAIL')
            if e:
                if isinstance(e, basestring):
                    ADMINS = [e]
                elif isinstance(e, list):
                    ADMINS = e
        if ADMINS and not app.config.get('SUPPRESS_ERROR_EMAILS'):
            from logging.handlers import SMTPHandler
            import platform
            hostname = platform.uname()[1]
            mail_handler = SMTPHandler('mailtrap.io',
                                       'server-error@' + hostname,
                                       ADMINS,
                                       'DOAJ Flask Error',
                                       credentials=('doaj-errors-265cc22d4983a31c', 'd8788b4007fd9cc6')
                           )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        # send errors to stderr, supervisord will capture them in the app's
        # error log
        send_errors_to_supervisor = logging.StreamHandler(sys.stderr)
        send_errors_to_supervisor.setLevel(logging.ERROR)
        app.logger.addHandler(send_errors_to_supervisor)

app = create_app()

