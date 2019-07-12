# -*- coding: UTF-8 -*-
# the comment above is for the Python interpreter, there are Unicode
# characters written straight into this source file

import pycountry
import json
import sys
import os

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    from portality.ordereddict import OrderedDict
else:
    from collections import OrderedDict

# countries
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", 'country-codes.json'), 'rb') as f:
    countries = json.loads(f.read())
countries_dict = OrderedDict(sorted(countries.items(), key=lambda x: x[1]['name']))
countries = countries_dict.items()

country_options = [('','')]
country_options_two_char_code_index = []

CURRENCY_DEFAULT = ''
currency_options = [(CURRENCY_DEFAULT, CURRENCY_DEFAULT)]
currency_options_code_index = []
currency_name_opts = []

for code, country_info in countries:        # FIXME: a bit of a mess - would be better to have an object that just gave us the answers on demand
    country_options.append((code, country_info['name']))
    country_options_two_char_code_index.append(code)
    if 'currency_alphabetic_code' in country_info and 'currency_name' in country_info:
        if country_info['currency_alphabetic_code'] not in currency_options_code_index:
            # prevent duplicates in the currency options by checking if
            # that currency has already been added - multiple countries
            # use the same currency after all (GBP, EUR..)
            currency_options.append(
                (
                    country_info['currency_alphabetic_code'],
                    country_info['currency_alphabetic_code'] + ' - ' + country_info['currency_name']
                )
            )
            currency_name_opts.append(
                (
                    country_info['currency_alphabetic_code'],
                    country_info['currency_name']
                )
            )
            currency_options_code_index.append(country_info['currency_alphabetic_code'])

currencies_dict = dict(currency_options)
currency_name_map = dict(currency_name_opts)

# Gather the languages with 2-character codes (ISO639-1)
language_options = []
language_options_two_char_code_index = []
for l in sorted(pycountry.languages, key=lambda x: x.name):
    try:
        language_options.append((l.alpha_2.upper(), l.name))
        language_options_two_char_code_index.append(l.alpha_2.upper())
    except AttributeError:
        continue

# license rights by license type
licenses = {
    # the titles and types are made to match the current values of
    # journals in the DOAJ for now - they can be cleaned up but it might
    # not be such a small job
    # Also DOAJ currently assumes type and title are the same.
    "CC BY": {'BY': True, 'NC': False, 'ND': False, 'SA': False, 'form_label': 'CC BY'},
    "CC BY-SA": {'BY': True, 'NC': False, 'ND': False, 'SA': True, 'form_label': 'CC BY-SA'},
    "CC BY-NC": {'BY': True, 'NC': True, 'ND': False, 'SA': False, 'form_label': 'CC BY-NC'},
    "CC BY-ND": {'BY': True, 'NC': False, 'ND': True, 'SA': False, 'form_label': 'CC BY-ND'},
    "CC BY-NC-ND": {'BY': True, 'NC': True, 'ND': True, 'SA': False, 'form_label': 'CC BY-NC-ND'},
    "CC BY-NC-SA": {'BY': True, 'NC': True, 'ND': False, 'SA': True, 'form_label': 'CC BY-NC-SA'},
}

for lic_type, lic_info in licenses.iteritems():
    lic_info['type'] = lic_type  # do not change this - the top-level keys in the licenses dict should always be == to the "type" of each license object
    lic_info['title'] = lic_type

license_dict = OrderedDict(sorted(licenses.items(), key=lambda x: x[1]['type']))

main_license_options = []
for lic_type, lic_info in license_dict.iteritems():
    main_license_options.append((lic_type, lic_info['form_label']))


def name_for_lang(rep):
    """ Get the language name from a representation of the language"""
    try:
        return pycountry.languages.lookup(rep).name
    except LookupError:
        return rep


def get_country_code(current_country, fail_if_not_found=False):
    """ Get the two-character country code for a given country name """
    try:
        return pycountry.countries.lookup(current_country).alpha_2
    except LookupError:
        return None if fail_if_not_found else current_country


def get_country_name(code):
    """ Get the name of a country from its two-character code """
    try:
        return pycountry.countries.lookup(code).name
    except LookupError:
        return code  # return what was passed in if not found


def get_currency_name(code):
    """ get the name of a currency from its code """
    try:
        cur = pycountry.currencies.lookup(code)
        return '{code} - {name}'.format(code=cur.alpha_3, name=cur.name)
    except LookupError:
        return code  # return what was passed in if not found


def get_currency_code(name):
    """ Retrieve a currency code by the currency name """
    try:
        return pycountry.currencies.lookup(name).alpha_3
    except LookupError:
        return None
