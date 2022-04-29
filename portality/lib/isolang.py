import pycountry


def find(lang, as_dict=True):
    """" Look up a language preferably by alpha2 code, or any of its attributes """
    language = pycountry.languages.get(alpha_2=lang)
    if language is None:
        try:
            language = pycountry.languages.lookup(lang)
        except LookupError:
            language = None
    return _as_dict(language) if as_dict else language


def _as_dict(language_object):
    """ Get a dict representing a language """
    # Previously we had a list of ISO_639_2b (bibliographic) languages in datasets.py represented e.g.
    # [u"wel", u"cym", u"cy", u"Welsh", u"gallois"] - now we have pycountry, so we favour the bibliographic name when
    # available. French is no longer present.

    # Convert to a dict in pycountry's representation
    language_dict = vars(language_object)['_fields']

    return {
        "alpha3": language_dict.get('bibliographic', language_dict.get('alpha_3', '')),
        "alt3": language_dict.get('alpha_3', ''),
        "alpha2": language_dict.get('alpha_2', ''),
        "name": language_dict.get('name', ''),
        "fr": ''
    }
