from setuptools import setup, find_packages
import sys

# Install for development or CI with pip install -e .[test] to get pytest, coverage, and selenium extras.

setup(
    name='doaj',
    version='6.3.2',
    packages=find_packages(),
    install_requires=[
        "awscli==1.20.50",
        "bagit==1.8.1",
        "boto3==1.18.50",
        "elastic-apm==5.2.2",
        "elasticsearch==7.13.0",
        "faust-streaming==0.9.5",  # Note: This is a maintained fork of the abandoned robinhood/faust
        "Faker==2.0.3",
        "feedparser==6.0.8",
        "itsdangerous==2.0.1",     # fixme: unpinned dependency of flask, 2.1.0 is causing an import error 'json'
        "jinja2<3.1.0",            # fixme: unpinned dependency of flask, import error on 'escape'
        "Flask~=2.1.2",
        "Flask-Cors==3.0.8",
        "Flask-DebugToolbar==0.13.1",
        "Flask-Login==0.6.1",
        "Flask-Mail==0.9.1",
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
        "markdown-link-attr-modifier==0.2.1",
        "mdx_truly_sane_lists==1.2",
        "openpyxl~=3.0.3",  # this package is needed for script only https://github.com/DOAJ/doajPM/issues/2433
        "parameterized==0.7.0",
        "psutil==5.6.3",
        #"pycountry==22.3.5",  # FIXME: pycountry on pypi is quite outdated (2022-03-05, missing e.g. Türkiye)
        "pycountry @ git+https://github.com/DOAJ/pycountry.git@30a23571951cf4eb98939a961ac96d1c2b64a3d8#egg=pycountry",
        "python-dateutil==2.8.0",  # something else already installs this, so just note we need it without an explicit version freeze
        "pytz==2019.3",
        "redis==3.3.11",
        "requests==2.22.0",
        "responses==0.10.6",
        "rstr==2.2.6",
        "tzlocal==2.0.0",
        "Unidecode==1.1.1",

        # Flask2 required >=2.0.*, Flask-Login required <=2.0.*
        "Werkzeug~=2.0.0",
        "WTForms==2.2.1",
        "esprit @ git+https://github.com/CottageLabs/esprit.git@edda12177effa0945d99302f0d453b22503e335b#egg=esprit",
        "dictdiffer @ git+https://github.com/CottageLabs/dictdiffer.git@cc86c1ca1a452169b1b2e4a0cb5fc9e6125bc572#egg=dictdiffer",
        "flask-swagger @ git+https://github.com/DOAJ/flask-swagger.git@f1dbf918d9903a588eed3cce2a87eeccc9f8cc0e#egg=flask-swagger"
    ] + (["setproctitle==1.1.10"] if "linux" in sys.platform else []),
    extras_require={
        "test": ["pytest", "pytest-cov", "pytest-xdist", "selenium==3.141",  # prevent backtracking through all versions
                 "combinatrix @ git+https://github.com/CottageLabs/combinatrix.git@740d255f0050d53a20324df41c08981499bb292c#egg=combinatrix"],
        "docs": [
            "featuremap @ git+https://github.com/CottageLabs/FeatureMap.git@cb52c345b942e50726767b1a7190f1a01b81e722#egg=featuremap",
            "testbook @ git+https://github.com/CottageLabs/testbook.git@15a7c0cc25d951d989504d84c2ef3e24caaf56e9#egg=testbook"]
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
)
