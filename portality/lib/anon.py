import hashlib
from faker import Faker

from portality.core import app

fake = Faker()


def anon_email(email):
    if not email:
        return email

    return hashlib.sha256(app.config['ANON_SALT'] + email.encode('utf-8')).hexdigest() + '@example.com'


def basic_hash(content):
    if not content:
        return content
    return hashlib.sha256(app.config['ANON_SALT'].encode('utf-8') + content.encode('utf-8')).hexdigest()


def anon_name():
    return fake.name()
