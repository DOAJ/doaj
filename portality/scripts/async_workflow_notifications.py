""" Building emails to send asynchronously, via cron job or scheduler """
# FIXME: Sort out status filters in all queries.

from portality import models, app_email
from portality.core import app

from flask import render_template
from datetime import datetime, timedelta
import time

# Store all of the emails: { email_addr : (name, [paragraphs]) }
emails_dict = {}


# Functions for each notification recipient - ManEd, Editor, Assoc_editor
def managing_editor_notifications():
    """
    Notify managing editors about two things:
        * Summary of records not touched for X weeks
        * Records marked as ready
    Note: requires request context to render the email text from templates
    """
    MAN_ED_EMAIL = app.config.get('MANAGING_EDITOR_EMAIL', 'managing-editors@doaj.org')

    relevant_statuses = app.config.get("MAN_ED_NOTIFICATION_STATUSES")
    term = "admin.application_status.exact"
    status_filters = [{"term": {term: status}} for status in relevant_statuses]

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
                        "should": status_filters
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

    # todo: build URLS nicely
    age_url = app.config.get('BASE_URL') + "/admin/applications?source={%22query%22%3A{%22match_all%22%3A{}}%2C%22sort%22%3A[{%22last_manual_update%22%3A{%22order%22%3A%22asc%22}}]%2C%22from%22%3A0%2C%22size%22%3A10}"

    idle_res = models.Suggestion.query(q=age_query)
    num_idle = idle_res.get('hits').get('total')
    num_never = idle_res.get('aggregations').get('never_updated').get('buckets')[0].get('doc_count')

    text = render_template('email/workflow_reminder_fragments/admin_age_frag', num_idle=num_idle, num_never=num_never, x_weeks=X_WEEKS, url=age_url)
    _add_email_paragraph(MAN_ED_EMAIL, 'Managing Editors', text)

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

    ready_url = app.config.get("BASE_URL") + '/admin/applications?source={%22query%22%3A{%22filtered%22%3A{%22filter%22%3A{%22bool%22%3A{%22must%22%3A[{%22term%22%3A{%22admin.application_status.exact%22%3A%22ready%22}}]}}%2C%22query%22%3A{%22match_all%22%3A{}}}}%2C%22sort%22%3A[{%22last_updated%22%3A{%22order%22%3A%22asc%22}}]%2C%22from%22%3A0%2C%22size%22%3A10}'

    ready_res = models.Suggestion.query(q=ready_query)
    num_ready = ready_res.get('hits').get('total')

    text = render_template('email/workflow_reminder_fragments/admin_ready_frag', num=num_ready, url=ready_url)
    _add_email_paragraph(MAN_ED_EMAIL, 'Managing Editors', text)


def editor_notifications():
    """
    Notify editors how many records are assigned to their group.
    Note: requires request context to render the email text from templates
    """

    relevant_statuses = app.config.get("ED_NOTIFICATION_STATUSES")
    term = "admin.application_status.exact"
    status_filters = [{"term": {term: status}} for status in relevant_statuses]

    ed_app_query = {
        "query": {
            "filtered": {
                "filter": {
                    "bool": {
                        "must": {
                            "exists": {"field": "admin.editor_group"}
                        },
                        "should": status_filters
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

    ed_url = app.config.get("BASE_URL") + "/editor/group_applications"

    # Query for editor groups which have items in the required statuses, count their numbers
    es = models.Suggestion.query(q=ed_app_query)
    group_stats = [(bucket.get("key"), bucket.get("doc_count")) for bucket in es.get("aggregations", {}).get("ed_group_counts", {}).get("buckets", [])]

    # Get the email addresses for the editor in charge of each group, Add the template to their email
    for (group_name, group_count) in group_stats:
        # get editor group object by name
        eg = models.EditorGroup.pull_by_key("name", group_name)
        if eg is None:
            continue

        # Get the email address to the editor account
        editor = models.Account.pull(eg.editor)
        ed_email = editor.email

        text = render_template('email/workflow_reminder_fragments/editor_groupcount_frag', num=group_count, ed_group=group_name, url=ed_url)
        _add_email_paragraph(ed_email, eg.editor, text)


def associate_editor_notifications():
    """
    Notify associates about two things:
        * Records assigned that haven't been updated for X days
        * Record(s) that haven't been updated for Y weeks
    Note: requires request context to render the email text from templates
    """

    # Get our thresholds from settings
    X_DAYS = app.config.get('ASSOC_ED_IDLE_DAYS', 2)
    Y_WEEKS = app.config.get('ASSOC_ED_IDLE_WEEKS', 2)
    now = datetime.now()
    idle_date = now - timedelta(days=X_DAYS)
    very_idle_date = now - timedelta(weeks=Y_WEEKS)
    idle_date_stamp = idle_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    very_idle_date_stamp = very_idle_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    relevant_statuses = app.config.get("ASSOC_ED_NOTIFICATION_STATUSES")
    term = "admin.application_status.exact"
    status_filters = [{"term": {term: status}} for status in relevant_statuses]

    assoc_age_query = {
        "query": {
            "filtered": {
                "filter": {
                    "bool": {
                        "must": {
                            "range": {
                                "last_manual_update": {
                                    #"gte": "1970-01-01T00:00:00Z",          # Newer than 'Never' (implicit)
                                    "lte": idle_date_stamp                   # Older than X_DAYS
                                }
                            }
                        },
                        "should": status_filters
                    }
                },
                "query": {
                    "match_all": {}
                }
            }
        },
        "size": 0,
        "aggregations": {
            "assoc_ed": {
                "terms": {
                    "field": "editor",
                    "size": 0
                },
                "aggregations": {
                    "older_weeks": {
                        "range": {
                            "field": "last_manual_update",
                            "ranges": [
                                {"to": very_idle_date_stamp},                # count those which are idle for weeks
                            ]
                        }
                    }
                }
            }
        }
    }

    url = app.config.get("BASE_URL") + "/editor/your_applications"

    es = models.Suggestion.query(q=assoc_age_query)
    for bucket in es.get("aggregations", {}).get("assoc_ed", {}).get("buckets", []):    # loop through assoc_ed buckets
        assoc_id = bucket.get("key")
        idle = bucket.get("doc_count")

        # Get the 'older than y weeks' count from nested aggregation
        very_idle = bucket.get("older_weeks").get("buckets")[0].get('doc_count')         # only one bucket, so take first

        # Pull the email address for our associate editor from their account
        assoc = models.Account.pull(assoc_id)
        try:
            assoc_email = assoc.email
        except AttributeError:
            # There isn't an account for that id todo: should we tell someone about this?
            continue

        text = render_template('email/workflow_reminder_fragments/assoc_ed_age_frag', num_idle=idle, x_days=X_DAYS, num_very_idle=very_idle, y_weeks=Y_WEEKS, url=url)
        _add_email_paragraph(assoc_email, assoc_id, text)


# Helper functions
def send_emails():
    global emails_dict

    for (email, (to_name, paragraphs)) in emails_dict.iteritems():
        pre = 'Dear ' + to_name + ',\n\n'
        post = '\n\nThe DOAJ Team'
        full_body = pre + '\n\n'.join(paragraphs) + post

        app_email.send_mail(to=[email],
                            fro=app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org'),
                            subject="DOAJ editorial reminders",
                            msg_body=full_body
                            )


def _add_email_paragraph(addr, to_name, para_string):
    """
    Add a new email to the global dict which stores the email fragments, or extend an existing one.
    :param addr: email address for recipient
    :param to_name: name of recipient
    :param para_string: paragraph to add to the email
    """
    global emails_dict

    try:
        (name, paras) = emails_dict[addr]
        paras.append(para_string)
    except KeyError:
        emails_dict[addr] = (to_name, [para_string])


# Main function for running all notification types in sequence
def run_async_notifications():
    """ Run through each notification type, then send emails """
    # Create a request context to render templates
    ctx = app.test_request_context()
    ctx.push()

    # Gather info and build the notifications
    managing_editor_notifications()
    editor_notifications()
    associate_editor_notifications()

    # Discard the context (the send mail function makes its own)
    ctx.pop()

    send_emails()

# Run all if the script is called.
if __name__ == '__main__':
    run_async_notifications()
