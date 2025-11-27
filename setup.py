from setuptools import setup, find_packages
import sys

# Install for development or CI with pip install -e .[test] to get pytest, coverage, and selenium extras.

setup(
    name='doaj',
    version='8.4.0',
    packages=find_packages(),
    install_requires=[
        "awscli==1.34.25",
        "bagit==1.8.1",
        "beautifulsoup4",
        "boto3==1.35.25",
        "cryptography~=42.0",
        "elastic-apm==6.24.0",
        "elasticsearch==7.13.0",
        "Faker==2.0.3",
        "feedparser==6.0.11",
        "jinja2~=3.1.4",
        "jsonpath-ng~=1.6",
        "flask<3",
        "Werkzeug<3.0",   # FIXME: we have passwords using plain sha1 that are undecodable after 3.0
        "Flask-Cors==5.0.0",
        "Flask-DebugToolbar==0.15.1",
        "Flask-Login==0.6.3",
        "Flask-Mail==0.10.0",
        "Flask-WTF==1.1.2",
        "wtforms<3",        # FIXME: deprecations prevent upgrade
        "email_validator~=2.2.0",
        "freezegun==1.5.1",
        "gunicorn==23.0.0",
        "huey~=2.5.2",
        "libsass==0.23.0",
        "LinkHeader==0.4.3",
        "lxml==5.3.0",
        "Markdown==3.7.0",
        "markdown-full-yaml-metadata==2.2.1",
        "markdown-link-attr-modifier==0.2.1",
        "mdx_truly_sane_lists==1.3",
        "numpy<2",    # Elasticsearch==7.13.0 requires numpy<2, and we can't upgrade our ES library while we are on OSS
        "openpyxl~=3.1.5",  # this package is needed for script only https://github.com/DOAJ/doajPM/issues/2433
        "parameterized~=0.9.0",
        "psutil==5.9.8",
        "pycountry==24.6.1",  # TODO: pycountry can get behind debian lists, so we may flip back to our fork later
        #"pycountry @ git+https://github.com/DOAJ/pycountry.git@caf24adc255bccc968a16d44702e8cd6a115dd50#egg=pycountry",
        "python-dateutil",  # something else already installs this; note we need it without an explicit version freeze
        "pytz==2024.2",
        "redis==3.3.11",
        "requests~=2.32.3",
        "responses==0.10.6",
        "rstr~=3.2.2",
        "tzlocal~=5.2.0",
        "Unidecode~=1.3.8",

        "dictdiffer @ git+https://github.com/CottageLabs/dictdiffer.git@cc86c1ca1a452169b1b2e4a0cb5fc9e6125bc572#egg=dictdiffer",
        "flask-swagger @ git+https://github.com/DOAJ/flask-swagger.git@f1dbf918d9903a588eed3cce2a87eeccc9f8cc0e#egg=flask-swagger",

        # priorities list generation
        'gspread~=5.10.0',
        'oauth2client~=4.1.3',
        'pandas~=2.0.1',  # pandas lets us generate URLs for linkcheck
        'gspread-dataframe~=3.3.1',
        'gspread-formatting~=1.1.2',

    ] + (["setproctitle==1.1.10"] if "linux" in sys.platform else []),
    extras_require={
        # prevent backtracking through all versions
        "test": ["pytest~=8.3.3",
                 "pytest-cov~=5.0.0",
                 "pytest-xdist~=3.6.1",
                 "selenium==4.25.0",
                 "combinatrix @ git+https://github.com/CottageLabs/combinatrix.git@c96e6035244e29d4709fff23103405c17cd04a13#egg=combinatrix",
                 "bs4==0.0.2",   # beautifulsoup for HTML parsing
                 'openapi-spec-validator~=0.5',
                 "cryptography~=42.0", # for ad-hoc https
                 ],

        # additional test dependencies for the test-extras target
        "test-ex": ["pytest-randomly", ],
        "docs": [
            "featuremap @ git+https://github.com/CottageLabs/FeatureMap.git@060e256a3e397518ed02111debf1605a9e05f34c#egg=featuremap",
            "testbook @ git+https://github.com/CottageLabs/testbook.git@edede0987fe2f9fe806bbc74b635f415ab645166#egg=testbook"]
    },
    url='https://cottagelabs.com/',
    author='Cottage Labs',
    author_email='us@cottagelabs.com',
    description='Directory of Open Access Journals website and software',
    license='Apache 2.0',
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': [
            'manage-bgjobs = portality.scripts.manage_background_jobs:main',
        ],
    },

)
