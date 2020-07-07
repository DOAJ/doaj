import pycountry
from collections import OrderedDict


def _generate_country_options():
    """Gather the countries with 2-character codes"""
    country_options_ = [('', '')]

    for co in sorted(pycountry.countries, key=lambda x: x.name):
        try:
            country_options_.append((co.alpha_2.upper(), co.name))
        except AttributeError:
            continue
    return country_options_


def _generate_currency_options():
    currency_options_ = [(CURRENCY_DEFAULT, CURRENCY_DEFAULT)]

    for cu in sorted(pycountry.currencies, key=lambda x: x.alpha_3):
        try:
            currency_options_.append((cu.alpha_3, '{code} - {name}'.format(code=cu.alpha_3, name=cu.name)))
        except AttributeError:
            continue

    return currency_options_


def _generate_language_options():
    """ Gather the languages with 2-character codes (ISO 639-2b) """
    language_options_ = []
    for l in sorted(pycountry.languages, key=lambda x: x.name):
        try:
            language_options_.append((l.alpha_2.upper(), l.name))
        except AttributeError:
            continue

    return language_options_


def _generate_license_options():
    """ Licenses and their rights """
    licenses_ = {
        # The titles and types are made to match the current values of journals in the DOAJ.
        # DOAJ currently assumes type and title are the same.
        "CC BY": {'BY': True, 'NC': False, 'ND': False, 'SA': False, 'form_label': 'CC BY', "url" : "https://creativecommons.org/licenses/by/4.0/"},
        "CC BY-SA": {'BY': True, 'NC': False, 'ND': False, 'SA': True, 'form_label': 'CC BY-SA', "url" : "https://creativecommons.org/licenses/by-sa/4.0/"},
        "CC BY-ND": {'BY': True, 'NC': False, 'ND': True, 'SA': False, 'form_label': 'CC BY-ND', "url" : "https://creativecommons.org/licenses/by-nd/4.0/"},
        "CC BY-NC": {'BY': True, 'NC': True, 'ND': False, 'SA': False, 'form_label': 'CC BY-NC', "url" : "https://creativecommons.org/licenses/by-nc/4.0/"},
        "CC BY-NC-SA": {'BY': True, 'NC': True, 'ND': False, 'SA': True, 'form_label': 'CC BY-NC-SA', "url" : "https://creativecommons.org/licenses/by-nc-sa/4.0/"},
        "CC BY-NC-ND": {'BY': True, 'NC': True, 'ND': True, 'SA': False, 'form_label': 'CC BY-NC-ND', "url" : "https://creativecommons.org/licenses/by-nc-nd/4.0/"},
        "CC0" : {'BY': False, 'NC': False, 'ND': False, 'SA': False, 'form_label': 'CC0', "url" : "https://creativecommons.org/publicdomain/zero/1.0/"},
        "Public domain" : {'BY': False, 'NC': False, 'ND': False, 'SA': False, 'form_label': 'CC BY', "url" : "https://creativecommons.org/publicdomain/mark/1.0/"},
    }

    # The top-level keys in the licenses dict should always be == to the "type" of each license object
    for lic_type, lic_info in licenses_.items():
        lic_info['type'] = lic_type
        lic_info['title'] = lic_type

    license_dict_ = OrderedDict(sorted(list(licenses_.items()), key=lambda x: x[1]['type']))

    main_license_options_ = []
    for lic_type, lic_info in license_dict_.items():
        main_license_options_.append((lic_type, lic_info['form_label']))

    return licenses_, license_dict_, main_license_options_


####################################################
# Datasets for export
####################################################

# COUNTRIES
# country_options is a list of tuples, [(2-char_code, name)] for 2-char codes (ISO 3166).
country_options = _generate_country_options()

# CURRENCIES
CURRENCY_DEFAULT = ''
# currency_options is a list of tuples, [(3-char_code, '3-char_code - name')] for all currencies.
currency_options = _generate_currency_options()

# LANGUAGES
language_options = _generate_language_options()

# LICENSES
# licenses contains a dict with each license's permissions. license_dict is ordered by the name of the licenses.
# main_license_options is a list of tuples [(license_type, label)] for use in dropdown menus.
licenses, license_dict, main_license_options = _generate_license_options()


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
