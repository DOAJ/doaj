""" Check whether the DOAJ contains records with invalid country, currency or language datasets """
import json

from portality import constants
from portality.models import Suggestion, Journal
from portality.datasets import language_for, get_country_name, get_currency_name


def check_invalid_datasets(journalobj, report):
    """ Find failed lookups for country / currency / language in a journal-like object """
    bj = journalobj.bibjson()

    # Check whether lookup fails on country code in bibjson
    country = bj.country
    if get_country_name(country) == country:
        report['country'].append((journalobj.id, country))

    # Check whether lookup fails on currency in bibjson
    apc = bj.apc
    if apc and get_currency_name(apc['currency']) == apc['currency']:
        report['currency'].append((journalobj.id, apc))

    # Check whether lookup fails on languages in bibjson
    for l in bj.language:
        if language_for(l) == l:
            report['language'].append((journalobj.id, str(bj.language)))
        break


def traverse_applications():
    a_report = {'country': [], 'currency': [], 'language': []}

    statuses_incomplete = list(set(constants.APPLICATION_STATUSES_ALL).difference({constants.APPLICATION_STATUS_REJECTED, constants.APPLICATION_STATUS_ACCEPTED}))
    for a in Suggestion.list_by_status(statuses_incomplete):
        check_invalid_datasets(a, a_report)

    return a_report


def traverse_journals():
    """ Check dataset lookups in all journals in DOAJ """
    j_report = {'country': [], 'currency': [], 'language': []}

    for j in Journal.all_in_doaj():
        check_invalid_datasets(j, j_report)

    return j_report


if __name__ == '__main__':

    print('Reporting invalid datasets for journals and applications...')
    full_report = {
        'applications': traverse_applications(),
        'journals': traverse_journals()
    }
    print((json.dumps(full_report, indent=2)))
