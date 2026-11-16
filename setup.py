from setuptools import setup, find_packages
import sys

# Install for development or CI with pip install -e .[test] to get pytest, coverage, and selenium extras.

setup(
    name='doaj',
    version='8.7.7',
    python_requires='>=3.12',
    packages=find_packages(),
    install_requires=[
        "awscli==1.46.3",
        "bagit==1.9.0",
        "beautifulsoup4",
        "boto3==1.44.3",
        "cryptography~=50.0",
        "elastic-apm==6.26.2",
        "elasticsearch==7.13.0",
        "faker==40.54.0",
        "feedparser==6.0.14",
        "jinja2~=3.1.6",
        "jsonpath-ng~=1.16",
        "flask==3.1.3",
        "Werkzeug~=3.1",
        "Flask-Babel==4.0.0",
        "Flask-Cors==6.0.5",
        "Flask-DebugToolbar==0.16.0",
        "Flask-Login==0.6.3",
        "Flask-Mail==0.10.0",
        "Flask-WTF==1.3.0",
        "wtforms<3",        # FIXME: deprecations prevent upgrade
        "email_validator~=2.4.0",
        "freezegun==1.5.5",
        "gunicorn==27.0.1",
        "huey~=3.5.4",
        "libsass==0.23.0",
        "LinkHeader==0.4.3",
        "lxml==6.1.3",
        "Markdown==3.11.3",
        "markdown-full-yaml-metadata==2.2.1",
        "markdown-link-attr-modifier==0.2.1",
        "mdx_truly_sane_lists==1.3",
        "numpy<2",    # Elasticsearch==7.13.0 requires numpy<2, and we can't upgrade our ES library while we are on OSS
        "openpyxl~=3.1.5",  # this package is needed for script only https://github.com/DOAJ/doajPM/issues/2433
        "parameterized~=0.9.0",
        "psutil==7.2.2",
        "pycountry==26.2.16",  # TODO: pycountry can get behind debian lists, so we may flip back to our fork later
        #"pycountry @ git+https://github.com/DOAJ/pycountry.git@caf24adc255bccc968a16d44702e8cd6a115dd50#egg=pycountry",
        "python-dateutil",  # something else already installs this; note we need it without an explicit version freeze
        "pytz==2026.6",
        "redis==8.1.0",
        "requests~=2.34.2",
        "responses==0.26.3",
        "rstr~=3.2.2",
        "setuptools~=84.2",
        "tzlocal~=5.4.5",
        "Unidecode~=1.4.0",

        "dictdiffer @ git+https://github.com/CottageLabs/dictdiffer.git@cc86c1ca1a452169b1b2e4a0cb5fc9e6125bc572#egg=dictdiffer",
        "flask-swagger @ git+https://github.com/DOAJ/flask-swagger.git@f1dbf918d9903a588eed3cce2a87eeccc9f8cc0e#egg=flask-swagger",

        # priorities list generation
        'gspread~=6.2.1',
        'oauth2client~=4.1.3',
        'pandas~=3.0.6',  # pandas lets us generate URLs for linkcheck
        'gspread-dataframe~=4.0.0',
        'gspread-formatting~=1.2.1',

    ] + (["setproctitle==1.3.8"] if "linux" in sys.platform else []),
    extras_require={
        # prevent backtracking through all versions
        "test": ["pytest~=9.2.0",
                 "pytest-cov~=7.1.0",
                 "pytest-xdist~=3.8.0",
                 "selenium==4.32.0",
                 "combinatrix @ git+https://github.com/CottageLabs/combinatrix.git@c96e6035244e29d4709fff23103405c17cd04a13#egg=combinatrix",
                 "bs4==0.0.2",   # beautifulsoup for HTML parsing
                 'openapi-spec-validator~=0.9.0',
                 "cryptography~=50.0", # for ad-hoc https
                 ],

        # additional test dependencies for the test-extras target
        "test-ex": ["pytest-randomly~=5.1.0", ],
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
