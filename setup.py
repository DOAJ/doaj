from setuptools import setup, find_packages
import sys

setup(
    name = 'doaj',
    version = '2.12.3',
    packages = find_packages(),
    install_requires = [
        "werkzeug==0.14.1",
        "Flask==1.0.1",
        "Flask-Login==0.4.1",
        "Flask-WTF==0.14.2",
        "Flask-Mail==0.9.1",
        "requests==2.18.4",
        "markdown",
        "gitpython",
        "lxml",
        "nose",
        "feedparser",
        "tzlocal",
        "pytz",
        "futures==2.1.6",
        "esprit==0.0.3",
        "nose",
        "unidecode",
        "Flask-Swagger==0.2.13",
        "flask-cors==3.0.4",
        "LinkHeader==0.4.3",
        "universal-analytics-python==0.2.4",
        "huey==1.7.0",
        "redis==2.10.5",
        "rstr==2.2.5",
        "freezegun==0.3.10",
        "responses==0.9.0",
        "python-dateutil",  # something else already installs this, so just note we need it without an explicit version freeze
        "pid==2.1.1",
        "Fabric==1.14.0",
        # for deployment
        "gunicorn",
        "newrelic",
        "parameterized==0.6.1"
    ] + (["setproctitle"] if "linux" in sys.platform else []),

    url = 'http://cottagelabs.com/',
    author = 'Cottage Labs',
    author_email = 'us@cottagelabs.com',
    description = 'A web API layer over an ES backend, with various useful views',
    license = 'Copyheart',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: Copyheart',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
