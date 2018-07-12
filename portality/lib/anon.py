import hashlib
from faker import Faker

from portality.core import app

fake = Faker()


def anon_email(email):
    if not email:
        return email

    return hashlib.sha256(app.config['ANON_SALT'] + email).hexdigest() + '@example.com'


def basic_hash(content):
    if not content:
        return content
    return hashlib.sha256(app.config['ANON_SALT'] + content).hexdigest()


def anon_name():
    return fake.name()
