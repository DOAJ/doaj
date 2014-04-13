from copy import deepcopy

from portality.models import Journal


def suggestion2journal(suggestion):
    journal_data = deepcopy(suggestion.data)
    del journal_data['suggestion']
    del journal_data['index']
    del journal_data['admin']['application_status']
    del journal_data['admin']['contact']
    del journal_data['id']
    del journal_data['created_date']
    del journal_data['last_updated']
    journal_data['bibjson']['active'] = True
    new_j = Journal(**journal_data)
    return new_j

def journal_form(form, request, redirect_url_on_success, template_name, existing_suggestion=None, **kwargs):
    pass

def JournalFormXWalk(object):
    pass