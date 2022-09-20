from setuptools import setup, find_packages
import sys

# Install for development or CI with pip install -e .[test] to get pytest, coverage, and selenium extras.

setup(
    name='doaj',
    version='6.2.5',
    packages=find_packages(),
    install_requires=[
        "awscli==1.20.50",
        "bagit==1.8.1",
        "boto3==1.18.50",
        "elastic-apm==5.2.2",
        "elasticsearch==7.13.0",
        "esprit==0.1.0",   # legacy for scripts etc (phasing out)
        "faust==1.10.4",
        "Faker==2.0.3",
        "feedparser==6.0.8",
        "itsdangerous==2.0.1",     # fixme: unpinned dependency of flask, 2.1.0 is causing an import error 'json'
        "jinja2<3.1.0",            # fixme: unpinned dependency of flask, import error on 'escape'
        "Flask==1.1.1",
        "Flask-Cors==3.0.8",
        "Flask-DebugToolbar==0.10.1",
        "Flask-Login==0.4.1",
        "Flask-Mail==0.9.1",
        "Flask-Swagger==0.2.13",
        "Flask-WTF==0.14.2",
        "freezegun==0.3.12",
        "GitPython==2.1.14",
        "gunicorn==19.9.0",
        "huey==1.10.5",  # upgrading to 1.11 / 2.x requires work
        "libsass==0.20.1",
        "LinkHeader==0.4.3",
        "lxml==4.8.0",
        "Markdown==3.1.1",
        "markdown-full-yaml-metadata==2.0.1",
        "markdown-link-attr-modifier==0.2.0",
        "mdx_truly_sane_lists==1.2",
        "openpyxl~=3.0.3",  # this package is needed for script only https://github.com/DOAJ/doajPM/issues/2433
        "parameterized==0.7.0",
        "psutil==5.6.3",
        "pycountry==19.8.18",
        "python-dateutil==2.8.0",  # something else already installs this, so just note we need it without an explicit version freeze
        "pytz==2019.3",
        "redis==3.3.11",
        "requests==2.22.0",
        "responses==0.10.6",
        "rstr==2.2.6",
        "tzlocal==2.0.0",
        "Unidecode==1.1.1",
        "Werkzeug==0.16.0",
        "WTForms==2.2.1",
    ] + (["setproctitle==1.1.10"] if "linux" in sys.platform else []),
    extras_require={"test": ["pytest", "pytest-cov", "pytest-xdist", "selenium"]},
    url='http://cottagelabs.com/',
    author='Cottage Labs',
    author_email='us@cottagelabs.com',
    description='Directory of Open Access Journals website and software',
    license='Apache 2.0',
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
