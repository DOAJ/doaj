""" Check whether the DOAJ contains records with invalid country, currency or language datasets """

from portality.models import Article, Suggestion, Journal
from portality.datasets import language_for, get_country_name, get_currency_name


def traverse_journals(report):
    j_report = {'country': [], 'currency': [], 'language': []}

    for j in Journal.all_in_doaj():
        bj = j.bibjson()

        # Check whether lookup fails on country code in bibjson
        country = bj.country
        if get_country_name(country) == country:
            j_report['country'].append((j.id, country))

        # Check whether lookup fails on currency in bibjson
        apc = bj.apc
        if apc and get_currency_name(apc['currency']) == apc['currency']:
            j_report['currency'].append((j.id, apc))

        # Check whether lookup fails on languages in bibjson
        for l in bj.language:
            if language_for(l) == l:
                j_report['language'].append((j.id, str(bj.language)))
            break

    report['journals'] = j_report


def traverse_articles(report):
    pass


def traverse_suggestions(report):
    pass


if __name__ == '__main__':
    import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-j', '--journals', action='store_true')
parser.add_argument('-a', '--articles', action='store_true')
parser.add_argument('-s', '--suggestions', action='store_true')

args = parser.parse_args()

full_report = {}
if args.journals is True:
    traverse_journals(full_report)

print(full_report)
