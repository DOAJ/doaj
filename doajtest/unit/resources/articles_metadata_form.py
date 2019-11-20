from copy import deepcopy

from werkzeug.datastructures import ImmutableMultiDict


class ArticleMetadataFactory(object):
    def __init__(self, article_source):
        self.article = article_source

    def update_article_no_change_to_url_and_doi(self):
        form = deepcopy(ARTICLE_METADATA_VALID_FORM)
        form["doi"] = list(filter(lambda identifier: identifier['type'] == 'doi', self.article["bibjson"]["identifier"]))[0]["id"]
        form["fulltext"] = list(filter(lambda link: link['type'] == 'fulltext', self.article["bibjson"]["link"]))[0]["url"]
        form["pissn"] = list(filter(lambda identifier: identifier['type'] == 'pissn', self.article["bibjson"]["identifier"]))[0]["id"]
        form["eissn"] = list(filter(lambda identifier: identifier['type'] == 'eissn', self.article["bibjson"]["identifier"]))[0]["id"]

        return ImmutableMultiDict(form)

    def update_article_fulltext(self, valid):
        form = deepcopy(ARTICLE_METADATA_VALID_FORM)
        form["doi"] = list(filter(lambda identifier: identifier['type'] == 'doi', self.article["bibjson"]["identifier"]))[0]["id"]
        if valid:
            form["fulltext"] = 'https://www.newarticleurl.co.uk/fulltext'
        else:
            form["fulltext"] = 'https://www.urltorepeat.com'
        form["pissn"] = \
        list(filter(lambda identifier: identifier['type'] == 'pissn', self.article["bibjson"]["identifier"]))[0]["id"]
        form["eissn"] = \
        list(filter(lambda identifier: identifier['type'] == 'eissn', self.article["bibjson"]["identifier"]))[0]["id"]

        return ImmutableMultiDict(form)

    def update_article_doi(self, valid):
        form = deepcopy(ARTICLE_METADATA_VALID_FORM)
        if valid:
            form["doi"] = '10.1111/article-0'
        else:
            form["doi"] = '10.1234/article'
            form["doi"] = '10.1234/article'
        form['pissn'] = list(filter(lambda identifier: identifier['type'] == 'pissn', self.article["bibjson"]["identifier"]))[0]["id"]
        form["eissn"] = list(filter(lambda identifier: identifier['type'] == 'eissn', self.article["bibjson"]["identifier"]))[0]["id"]
        form["fulltext"] = list(filter(lambda link: link['type'] == 'fulltext', self.article["bibjson"]["link"]))[0][
            "url"]

        return ImmutableMultiDict(form)


ARTICLE_METADATA_VALID_FORM = {
    'title': 'New title',
    'authors-0-name': 'Agnieszka',
    'authors-0-affiliation': 'Cottage Labs',
    'authors-1-name': 'John Smith',
    'authors-1-affiliation': 'DOAJ',
    'abstract': 'This abstract has been edited',
    'keywords': 'edited-1,edited-2, edited-3',
    'publication_month': '10',
    'publication_year': '1987',
    #'pissn': '1234-5678',
    #'eissn': '9876-5432',
    'volume': '1',
    'number': '1',
    'start': '1',
    'end': '1'
}