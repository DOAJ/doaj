import pycountry
import sys

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    from portality.ordereddict import OrderedDict
else:
    from collections import OrderedDict

# Gather the countries with 2-character codes
country_options = [('', '')]
country_options_two_char_code_index = []

for co in sorted(pycountry.countries, key=lambda x: x.name):
    try:
        country_options.append((co.alpha_2.upper(), co.name))
        country_options_two_char_code_index.append(co.alpha_2.upper())
    except AttributeError:
        continue

# currencies
CURRENCY_DEFAULT = ''
currency_options = [(CURRENCY_DEFAULT, CURRENCY_DEFAULT)]
currency_options_code_index = []
currency_name_opts = []

for cu in sorted(pycountry.currencies, key=lambda x: x.alpha_3):
    try:
        currency_options.append((cu.alpha_3, '{code} - {name}'.format(code=cu.alpha_3, name=cu.name)))
        currency_name_opts.append((cu.alpha_3, cu.name))
        currency_options_code_index.append(cu.alpha_3)
    except AttributeError:
        continue

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

# do not change this - the top-level keys in the licenses dict should always be == to the "type" of each license object
for lic_type, lic_info in licenses.items():
    lic_info['type'] = lic_type
    lic_info['title'] = lic_type

license_dict = OrderedDict(sorted(list(licenses.items()), key=lambda x: x[1]['type']))

main_license_options = []
for lic_type, lic_info in license_dict.items():
    main_license_options.append((lic_type, lic_info['form_label']))


def language_for(rep):
    """ Get the entire language entry for a given representation """
    try:
        return pycountry.languages.lookup(rep)
    except LookupError:
        return None


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
