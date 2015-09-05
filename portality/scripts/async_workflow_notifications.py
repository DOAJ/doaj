""" Building emails to send asynchronously, via cron job or scheduler """

from portality import models
from portality.core import app
from datetime import datetime, timedelta


def managing_editor_notifications():
    """
    Notify managing editors about two things:
        * Summary of records not touched for X weeks
        * Records marked as ready
    """
    MAN_ED_EMAIL = app.config.get('MANAGING_EDITOR_EMAIL', 'managing-editors@doaj.org')

    # First note - records not touched for so long
    X_WEEKS = app.config.get('MAN_ED_IDLE_CUTOFF', 2)
    newest_date = datetime.now() - timedelta(weeks=X_WEEKS)
    newest_date_stamp = newest_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    age_query = {
        "query": {
            "filtered": {
                "filter": {
                    "bool": {
                        "must": {
                            "range": {
                                "last_manual_update": {
                                    #"gte": "1970-01-01T00:00:00Z",          # Newer than 'Never' (implicit)
                                    "lte": newest_date_stamp                 # Older than X_WEEKS
                                }
                            }
                        },
                        "should": [
                            {
                                "term": {"admin.application_status.exact": "submitted"}
                            },
                            {
                                "term": {"admin.application_status.exact": "pending"}
                            },
                            {
                                "term": {"admin.application_status.exact": "in progress"}
                            },
                            {
                                "term": {"admin.application_status.exact": "completed"}
                            },
                            {
                                "term": {"admin.application_status.exact": "on hold"}
                            }
                        ]
                    }
                },
                "query": {
                    "match_all": {}
                }
            }
        },
        "size": 0,
        "aggregations": {
            "never_updated": {
                "range": {
                    "field": "last_manual_update",
                    "ranges": [
                        {"to": "1970-01-01T00:00:01Z"}                      # Bucket including anything < 1s after Never
                    ]
                }
            }
        }
    }

    MAN_ED_AGE_TEMPLATE = '{num_idle} applications in the pipeline have not been updated for {x_weeks} weeks or more, ' \
                          'of which {num_never} have never been updated by an editor.' \
                          ' These can be viewed at the following url: \n{url}'

    idle_res = models.Suggestion.query(q=age_query)
    num_idle = idle_res.get('hits').get('total')
    num_never = idle_res.get('aggregations').get('never_updated').get('buckets')[0].get('doc_count')
    url = app.config.get('BASE_URL') + "/admin/applications?source={%22query%22%3A{%22match_all%22%3A{}}%2C%22sort%22%3A[{%22last_updated%22%3A{%22order%22%3A%22asc%22}}]%2C%22from%22%3A0%2C%22size%22%3A10}"

    text = MAN_ED_AGE_TEMPLATE.format(num_idle=num_idle, num_never=num_never, x_weeks=X_WEEKS, url=url)
    _add_email_paragraph(MAN_ED_EMAIL, text)

    # The second notification - the number of ready records
    ready_query = {
        "query": {
            "filtered": {
                "filter": {
                    "term": {"admin.application_status.exact": "ready"}
                },
                "query": {
                    "match_all": {}
                }
            }
        }
    }

    READY_TEMPLATE = 'There are {num} records in status \'Ready\' which are awaiting the attention of a Managing Editor.'

    ready_res = models.Suggestion.query(q=ready_query)
    num_ready = ready_res.get('hits').get('total')

    text = READY_TEMPLATE.format(num=num_ready)
    _add_email_paragraph(MAN_ED_EMAIL, text)


def editor_notifications():
    """ Notify editors how many records are assigned to their group. """

    ed_app_query = {
        "query": {
            "filtered": {
                "filter": {
                    "bool": {
                        "must": {
                            "exists": {"field": "admin.editor_group"}
                        },
                        "should": [
                            {
                                "term": {"admin.application_status.exact": "submitted"}
                            },
                            {
                                "term": {"admin.application_status.exact": "pending"}
                            },
                            {
                                "term": {"admin.application_status.exact": "in progress"}
                            },
                            {
                                "term": {"admin.application_status.exact": "completed"}
                            },
                            {
                                "term": {"admin.application_status.exact": "on hold"}
                            }
                        ]
                    }
                },
                "query": {
                    "match_all": {}
                }
            }
        },
        "size": 0,
        "aggregations": {
            "ed_group_counts": {
                "terms": {
                    "field": "admin.editor_group",
                    "size": 0
                }
            }
        }
    }

    ED_TEMPLATE = "There are {num} applications currently assigned to your Editor Group, \"{ed_group}\". " \
                  "View these in the Editor area: {url}"
    ED_URL = app.config.get("BASE_URL") + "/editor/group_applications"

    # Query for editor groups which have items in the required statuses, count their numbers
    es = models.Suggestion.query(q=ed_app_query)
    group_stats = [(bucket.get("key"), bucket.get("doc_count")) for bucket in es.get("aggregations", {}).get("ed_group_counts", {}).get("buckets", [])]

    # Get the email addresses for the editor in charge of each group, Add the template to their email
    for g in group_stats:
        print g
        # get editor group object by name
        eg = models.EditorGroup.pull_by_key("name", g[0])
        if eg is None:
            continue

        # Get the email address to the editor account
        editor = models.Account.pull(eg.editor)
        ed_email = editor.email

        text = ED_TEMPLATE.format(num=g[1], ed_group=g[0], url=ED_URL)
        _add_email_paragraph(ed_email, text)



def associate_editor_notifications():
    """
    Notify associates about two things:
        * Records assigned that haven't been updated for X days
        * Record(s) that haven't been updated for Y weeks
    """
    pass


def _add_email_paragraph(addr, para_string):
    print (addr, para_string)
