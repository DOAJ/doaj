from setuptools import setup, find_packages
import sys

setup(
    name='doaj',
    version='3.1.7',
    packages=find_packages(),
    install_requires=[
        "Werkzeug==0.16.0",
        "Flask==1.1.1",
        "Flask-Login==0.4.1",
        "WTForms==2.2.1",
        "Flask-WTF==0.14.2",
        "Flask-Mail==0.9.1",
        "requests==2.22.0",
        "Markdown==3.1.1",
        "GitPython==2.1.14",
        "lxml==4.4.1",
        "feedparser==5.2.1",
        "tzlocal==2.0.0",
        "pytz==2019.3",
        "pycountry==19.8.18",
        "esprit==0.1.0",
        "nose==1.3.7",
        "Unidecode==1.1.1",
        "Flask-Swagger==0.2.13",
        "Flask-Cors==3.0.8",
        "LinkHeader==0.4.3",
        # "universal-analytics-python", # No Python 3 support
        "openpyxl~=3.0.3",  # this package is needed for script only https://github.com/DOAJ/doajPM/issues/2433
        "psutil==5.6.3",
        "huey==1.10.5",  # upgrading to 1.11 / 2.x requires work
        "redis==3.3.11",
        "rstr==2.2.6",
        "freezegun==0.3.12",
        "responses==0.10.6",
        "Faker==2.0.3",
        "python-dateutil==2.8.0",  # something else already installs this, so just note we need it without an explicit version freeze
        # for deployment
        "gunicorn==19.9.0",
        "elastic-apm==5.2.2",
        "parameterized==0.7.0",
        "awscli==1.16.269",
        "boto3==1.10.5",
        "Flask-DebugToolbar==0.10.1"
    ] + (["setproctitle==1.1.10"] if "linux" in sys.platform else []),
    url='http://cottagelabs.com/',
    author='Cottage Labs',
    author_email='us@cottagelabs.com',
    description='Directory of Open Access Journals website and software',
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: Copyheart',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
