from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from portality.models import Article


def update_article_language(article: 'Article'):
    if len(article.bibjson().journal_language) and not all(article.bibjson().journal_language):
        print('invalid language {}'.format(article.bibjson().journal_language))
    else:
        article.bibjson().journal_language = [l for l in article.bibjson().journal_language]
    return article
