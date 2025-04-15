# ~~Anonymisation:Feature~~
from faker import Faker

from portality.core import app

fake = Faker()


def anon_email(email):
    if not email:
        return email

    return basic_hash(email) + '@example.com'


def basic_hash(content):
    if not content:
        return content
    return hex(hash(app.config['ANON_SALT']) + hash(content))[2:]


def anon_name():
    return fake.name()
