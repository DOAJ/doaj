from setuptools import setup, find_packages

setup(
    name = 'portality',
    version = '0.4',
    packages = find_packages(),
    install_requires = [
        "Flask==0.8",
        "Flask-Login",
        "Flask-WTF",
        "pyes==0.16",
        "requests",
    ],
    url = 'http://cottagelabs.com/',
    author = 'Cottage Labs',
    author_email = 'us@cottagelabs.com',
    description = 'All the bits for a web frontend',
    license = 'AGPL',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)

