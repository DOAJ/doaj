from copy import deepcopy
from doajtest.fixtures.journals import JOURNAL_SOURCE, JOURNAL_INFO
from doajtest.fixtures.common import EDITORIAL, SUBJECT, NOTES, OWNER

class ApplicationFixtureFactory(object):
    @staticmethod
    def make_application_source():
        return deepcopy(APPLICATION_SOURCE)

    @staticmethod
    def make_application_form():
        return deepcopy(APPLICATION_FORM)

    @staticmethod
    def make_application_form_info():
        return deepcopy(APPLICATION_FORMINFO)

APPLICATION_SOURCE = {
    "id" : "abcdefghijk",
    "created_date" : "2000-01-01T00:00:00Z",
    "bibjson": deepcopy(JOURNAL_SOURCE['bibjson']),
    "suggestion" : {
        "suggester" : {
            "name" : "Suggester",
            "email" : "suggester@email.com"
        },
        "articles_last_year" : {
            "count" : 16,
            "url" : "http://articles.last.year"
        },
        "article_metadata" : True
    },
    "admin" : {
        "application_status" : "pending",
        "notes" : [
            {"note" : "First Note", "date" : "2014-05-21T14:02:45Z"},
            {"note" : "Second Note", "date" : "2014-05-22T00:00:00Z"}
        ],
        "contact" : [
            {
                "email" : "contact@email.com",
                "name" : "Contact Name"
            }
        ],
        "owner" : "Owner",
        "editor_group" : "editorgroup",
        "editor" : "associate",
    }
}

SUGGESTION = {
    "articles_last_year" : 16,
    "articles_last_year_url" : "http://articles.last.year",
    "metadata_provision" : "True"
}

SUGGESTER = {
    "suggester_name" : "Suggester",
    "suggester_email" : "suggester@email.com",
    "suggester_email_confirm" : "suggester@email.com"
}

WORKFLOW = {
    "application_status" : "pending"
}

APPLICATION_FORMINFO = deepcopy(JOURNAL_INFO)
APPLICATION_FORMINFO.update(deepcopy(SUGGESTION))
APPLICATION_FORMINFO.update(deepcopy(SUGGESTER))
APPLICATION_FORMINFO.update(deepcopy(NOTES))
APPLICATION_FORMINFO.update(deepcopy(SUBJECT))
APPLICATION_FORMINFO.update(deepcopy(OWNER))
APPLICATION_FORMINFO.update(deepcopy(EDITORIAL))
APPLICATION_FORMINFO.update(deepcopy(WORKFLOW))

APPLICATION_FORM = deepcopy(APPLICATION_FORMINFO)
APPLICATION_FORM["keywords"] = ",".join(APPLICATION_FORM["keywords"])
notes = APPLICATION_FORM["notes"]
del APPLICATION_FORM["notes"]
i = 0
for n in notes:
    notekey = "notes-" + str(i) + "-note"
    datekey = "notes-" + str(i) + "-date"
    APPLICATION_FORM[notekey] = n.get("note")
    APPLICATION_FORM[datekey] = n.get("date")
    i += 1