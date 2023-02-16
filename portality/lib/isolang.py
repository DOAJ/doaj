from typing import Optional

import pycountry


def find(lang: str):
    """ Look up a language preferably by alpha2 code, or any of its attributes

    :param lang: A code or name, etc. to retrieve the language record
    :return: a dictionary equivalent to the pycountry representation of a record
    """
    return _as_dict(find_raw(lang))


def find_raw(lang: str):
    """
    Look up a language preferably by alpha2 code, or any of its attributes

    :param lang: A code or name, etc. to retrieve the language record
    :return: the pycountry representation of a language
    """

    language = pycountry.languages.get(alpha_2=lang)
    if language is None:
        try:
            return pycountry.languages.lookup(lang)
        except LookupError:
            return None
    return language


def _as_dict(language_object: pycountry.Languages):
    """ Get a dict representing a language """
    # Previously we had a list of ISO_639_2b (bibliographic) languages in datasets.py represented e.g.
    # [u"wel", u"cym", u"cy", u"Welsh", u"gallois"] - now we have pycountry, so we favour the bibliographic name when
    # available. French is no longer present.

    if language_object is None:
        return None

    # Convert to a dict in pycountry's representation
    language_dict = vars(language_object)['_fields']

    return {
        "alpha3": language_dict.get('bibliographic', language_dict.get('alpha_3', '')),
        "alt3": language_dict.get('alpha_3', ''),
        "alpha2": language_dict.get('alpha_2', ''),
        "name": language_dict.get('name', ''),
        "fr": ''
    }


def get_doaj_3char_lang_by_lang(lang: 'pycountry.db.Language') -> Optional[str]:
    return lang and getattr(lang,
                            'bibliographic',
                            getattr(lang, 'alpha_3', None))
