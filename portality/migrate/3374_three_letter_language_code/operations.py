from typing import TYPE_CHECKING

from portality.lib import val_convert

if TYPE_CHECKING:
    from portality.models import Article

lang_code_fn = val_convert.create_fn_to_isolang(is_upper=False)

lang_map = {
    'engilish': 'English',
    'greek': 'gre',
    'malay': 'may',
}
# some can't found by lookup
country_name_map = {
    'iran': 'IRN',
    'south korea': 'KOR',
}


def update_article_code(article: 'Article'):
    lang_list = article.data['bibjson']['journal']['language']
    lang_list = (l for l in lang_list if l is not None and l != '')
    lang_list = (lang_map.get(l.lower(), l) for l in lang_list)
    lang_list = map(lang_code_fn, lang_list)
    try:
        article.data['bibjson']['journal']['language'] = list(lang_list)
    except ValueError as e:
        # ignore convert code fail
        print(str(e))

    org_country = article.data['bibjson']['journal']['country']
    new_val = country_name_map.get(org_country.lower())
    try:
        if not new_val:
            new_val = val_convert.to_country_code_3(org_country)
        article.data['bibjson']['journal']['country'] = new_val
    except ValueError as e:
        # ignore convert code fail
        print(str(e))

    return article
