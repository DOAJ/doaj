"""
Compare new and old pycountry options lists

Procedure:
* run this script with -w

    python pycountry_options_compare.py -w

* update pycountry

    pip install --upgrade pycountry

* run this script again with -w

    python pycountry_options_compare.py -w

You should have 2 sets of output files suffixed with the differing pycountry versions e.g.

    country_options_19.8.18.json
    country_options_22.3.5.json
    currency_options_19.8.18.json
    currency_options_22.3.5.json
    language_options_19.8.18.json
    language_options_22.3.5.json

* run this script with option -c to make the comparison

    python pycountry_options_compare.py -c

* optionally specify the versions numbers to compare: --old, --new

    python pycountry_options_compare.py -c -o 22.3.5 -n 22.3.6.dev0

"""

import json
from portality.datasets import country_options, currency_options, language_options
import pycountry
from importlib.metadata import version


def writeout():
    """ Write current pycountry version's options out to files """
    for x, y in [('country_options', country_options),
                 ('currency_options', currency_options),
                 ('language_options', language_options)]:
        with open(x + '_' + version('pycountry') + '.json', 'w') as f:
            json.dump(y, f)


def compare(old_ver, new_ver):
    """ Compare two sets of versioned options list files """
    with open(f'country_options_{old_ver}.json', 'r') as a, open(f'currency_options_{old_ver}.json', 'r') as b, open(f'language_options_{old_ver}.json', 'r') as c:
        old_country_codes = set([tuple(co) for co in json.load(a)])
        old_currency_codes = set([tuple(cu) for cu in json.load(b)])
        old_language_codes = set([tuple(la) for la in json.load(c)])

    with open(f'country_options_{new_ver}.json', 'r') as x, open(f'currency_options_{new_ver}.json', 'r') as y, open(f'language_options_{new_ver}.json', 'r') as z:
        country_codes = set([tuple(co) for co in json.load(x)])
        currency_codes = set([tuple(cu) for cu in json.load(y)])
        language_codes = set([tuple(la) for la in json.load(z)])

    codes = {'countries added': list(country_codes.difference(old_country_codes)),
             'countries removed': list(old_country_codes.difference(country_codes)),
             'currencies added': list(currency_codes.difference(old_currency_codes)),
             'currencies removed': list(old_currency_codes.difference(currency_codes)),
             'languages added': list(language_codes.difference(old_language_codes)),
             'languages removed': list(old_language_codes.difference(language_codes))}

    print(json.dumps(codes, indent=2, ensure_ascii=False))


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("-w", "--write", help="Write out current options list", action='store_true')
    grp.add_argument("-c", "--compare", help="Compare two version sets of dataset options", action='store_true')
    parser.add_argument("-o", "--old", help="Old version suffix to read", default='19.8.18', required=False)
    parser.add_argument("-n", "--new", help="New version suffix to read", default='22.3.5', required=False)

    args = parser.parse_args()

    if args.write:
        writeout()

    if args.compare:
        compare(old_ver=args.old, new_ver=args.new)
