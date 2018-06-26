import hashlib
from portality.core import app


def anon_email(email):
    return hashlib.sha256(app.config['ANON_SALT'] + email).hexdigest() + '@example.com'


def basic_hash(id_):
    return hashlib.sha256(app.config['ANON_SALT'] + id_).hexdigest()


def anon_name(name):
    return 'Stacy ' + basic_hash(name)