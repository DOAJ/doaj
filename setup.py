from setuptools import setup, find_packages
import sys

setup(
    name='doaj',
    version='3.0.3',
    packages=find_packages(),
    install_requires=[
        "werkzeug",
        "Flask",
        "Flask-Login",
        "Flask-WTF",
        "Flask-Mail",
        "requests",
        "markdown",
        "gitpython",
        "lxml",
        "nose",
        "feedparser",
        "tzlocal",
        "pytz",
        "pycountry",
        "futures",
        "esprit",
        "nose",
        "unidecode",
        "Flask-Swagger",
        "flask-cors",
        "LinkHeader",
#        "universal-analytics-python",                                          # No Python 3 support
        "psutil==5.6.3",
        "huey==1.10.5",                                                          # upgrading to 1.11 / 2.x requires work
        "redis",
        "rstr",
        "freezegun",
        "responses",
        "Faker",
        "python-dateutil",  # something else already installs this, so just note we need it without an explicit version freeze
        # for deployment
        "gunicorn",
        "elastic-apm[flask]",
        "parameterized",
        "awscli",
        "boto3",
        "flask-debugtoolbar"
    ] + (["setproctitle"] if "linux" in sys.platform else []),
<<<<<<< HEAD
    url = 'http://cottagelabs.com/',
    author = 'Cottage Labs',
    author_email = 'us@cottagelabs.com',
    description = 'Directory of Open Access Journals website and software',
    license = 'Copyheart',
    classifiers = [
=======
    url='http://cottagelabs.com/',
    author='Cottage Labs',
    author_email='us@cottagelabs.com',
    description='Directory of Open Access Journals website and software',
    license='Copyheart',
    classifiers=[
>>>>>>> e9b8d58088f1a878139c5427e5168d9d8f551ed6
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: Copyheart',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
