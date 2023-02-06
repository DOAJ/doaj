from datetime import datetime, timedelta

from flask import render_template

from portality import constants
from portality import models, app_email
from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.core import app
from portality.dao import Facetview2
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import main_queue, schedule


class AgeQuery(object):
    def __init__(self, newest_date, status_filters):
        self._newest_date = newest_date
        self._status_filters = status_filters

    def query(self):
        return {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "last_manual_update": {
                                    #"gte": "1970-01-01T00:00:00Z",          # Newer than 'Never' (implicit)
                                    "lte": self._newest_date                 # Older than X_WEEKS
                                }
                            }
                        },
                        {
                            "exists": {
                                "field": "admin.editor"
                            }
                        }
                    ],
                    "should": self._status_filters,
                    "minimum_should_match": 1
                }
            },
            "size": 0,
        }


class ReadyQuery(object):
    def __init__(self, ready_filter):
        self._ready_filter = ready_filter

    def query(self):
        return {
            "query": {
                "bool": {
                    "filter": self._ready_filter
                }
            },
            "size": 0
        }


class EdAppQuery(object):
    def __init__(self, status_filters):
        self._status_filters = status_filters

    def query(self):
        return {
            "query": {
                "bool": {
                    "filter": {
                        "bool": {
                            "must": {
                                "exists": {"field": "admin.editor_group"}
                            },
                            "must_not": {
                                "exists": {
                                    "field": "admin.editor"
                                }
                            },
                            "should": self._status_filters,
                            "minimum_should_match": 1
                        }
                    }
                }
            },
            "size": 0,
            "aggregations": {
                "ed_group_counts": {
                    "terms": {
                        "field": "admin.editor_group.exact",
                        "size" : 9999
                    }
                }
            }
        }


class EdAgeQuery(object):
    def __init__(self, newest_date, status_filters):
        self._newest_date = newest_date
        self._status_filters = status_filters

    def query(self):
        return {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "last_manual_update": {
                                    # "gte": "1970-01-01T00:00:00Z",          # Newer than 'Never' (implicit)
                                    "lte": self._newest_date  # Older than X_WEEKS
                                }
                            }
                        },
                        {
                            "exists": {
                                "field": "admin.editor"
                            }
                        }
                    ],
                    "should": self._status_filters,
                    "minimum_should_match": 1
                }
            },
            "size": 0,
            "aggregations": {
                "ed_group_counts": {
                    "terms": {
                        "field": "admin.editor_group.exact",
                        "size": 9999
                    }
                }
            }
        }

class AssEdAgeQuery(object):
    def __init__(self, idle_date, very_idle_date, status_filters):
        self._idle_date = idle_date
        self._very_idle_date = very_idle_date
        self._status_filters = status_filters

    def query(self):
        return {
            "query": {
                "bool": {
                    "must": {
                        "range": {
                            "last_manual_update": {
                                # "gte": "1970-01-01T00:00:00Z",          # Newer than 'Never' (implicit)
                                "lte": self._idle_date  # Older than X_DAYS
                            }
                        }
                    },
                    "should": self._status_filters,
                    "minimum_should_match" : 1
                }
            },
            "size": 0,
            "aggregations": {
                "assoc_ed": {
                    "terms": {
                        "field": "admin.editor.exact",
                        "size": 9999
                    },
                    "aggregations": {
                        "older_weeks": {
                            "range": {
                                "field": "last_manual_update",
                                "ranges": [
                                    {"to": self._very_idle_date},  # count those which are idle for weeks
                                ]
                            }
                        }
                    }
                }
            }
        }
# Functions for each notification recipient - ManEd, Editor, Assoc_editor
def managing_editor_notifications(emails_dict):
    """
    Notify managing editors about two things:
        * Summary of records assigned to associate editors but not touched for X weeks
        * Records marked as ready
    Note: requires request context to render the email text from templates
    """
    MAN_ED_EMAIL = app.config.get('MANAGING_EDITOR_EMAIL', 'managing-editors@doaj.org')

    relevant_statuses = app.config.get("MAN_ED_NOTIFICATION_STATUSES")
    term = "admin.application_status.exact"
    status_filters = [Facetview2.make_term_filter(term, status) for status in relevant_statuses]

    # First note - records not touched for so long
    X_WEEKS = app.config.get('MAN_ED_IDLE_WEEKS', 2)
    newest_date = datetime.now() - timedelta(weeks=X_WEEKS)
    newest_date_stamp = newest_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    age_query = AgeQuery(newest_date_stamp, status_filters)
    idle_res = models.Suggestion.query(q=age_query.query())
    num_idle = idle_res.get('hits', {}).get('total', {}).get('value', 0)

    text = render_template('email/workflow_reminder_fragments/admin_age_frag', num_idle=num_idle, x_weeks=X_WEEKS)
    _add_email_paragraph(emails_dict, MAN_ED_EMAIL, 'Managing Editors', text)

    # The second notification - the number of ready records
    ready_filter = Facetview2.make_term_filter('admin.application_status.exact', constants.APPLICATION_STATUS_READY)
    ready_query = ReadyQuery(ready_filter)

    admin_fv_prefix = app.config.get('BASE_URL') + "/admin/applications?source="
    fv_ready = Facetview2.make_query(filters=ready_filter, sort_parameter="last_manual_update")
    ready_url = admin_fv_prefix + Facetview2.url_encode_query(fv_ready)

    ready_res = models.Suggestion.query(q=ready_query.query())
    num_ready = ready_res.get('hits').get('total', {}).get('value', 0)

    text = render_template('email/workflow_reminder_fragments/admin_ready_frag', num=num_ready, url=ready_url)
    _add_email_paragraph(emails_dict, MAN_ED_EMAIL, 'Managing Editors', text)


def editor_notifications(emails_dict, limit=None):
    """
    Notify editors about two things:
        * how many records are assigned to their group which have no associate assigned.
        * how many records assigned to an associate in their group but have been idle for X_WEEKS
    Note: requires request context to render the email text from templates
    
    :param: limit: for the purposes of demonstration, limit the number of emails this function generates.
    """

    relevant_statuses = app.config.get("ED_NOTIFICATION_STATUSES")
    term = "admin.application_status.exact"
    status_filters = [Facetview2.make_term_filter(term, status) for status in relevant_statuses]

    # First note - how many applications in editor's group have no associate editor assigned.
    ed_app_query = EdAppQuery(status_filters)

    ed_url = app.config.get("BASE_URL") + "/editor/group_applications"

    # Query for editor groups which have items in the required statuses, count their numbers
    es = models.Suggestion.query(q=ed_app_query.query())
    group_stats = [(bucket.get("key"), bucket.get("doc_count")) for bucket in es.get("aggregations", {}).get("ed_group_counts", {}).get("buckets", [])]

    if limit is not None and isinstance(limit, int):
        group_stats = group_stats[:limit]

    # Get the email addresses for the editor in charge of each group, Add the template to their email
    for (group_name, group_count) in group_stats:
        # get editor group object by name
        eg = models.EditorGroup.pull_by_key("name", group_name)
        if eg is None:
            continue

        # Get the email address to the editor account
        editor = eg.get_editor_account()
        ed_email = editor.email

        text = render_template('email/workflow_reminder_fragments/editor_groupcount_frag', num=group_count, ed_group=group_name, url=ed_url)
        _add_email_paragraph(emails_dict, ed_email, eg.editor, text)

    # Second note - records within editor group not touched for so long
    X_WEEKS = app.config.get('ED_IDLE_WEEKS', 2)
    newest_date = datetime.now() - timedelta(weeks=X_WEEKS)
    newest_date_stamp = newest_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    ed_age_query = EdAgeQuery(newest_date_stamp, status_filters)

    ed_fv_prefix = app.config.get('BASE_URL') + "/editor/group_applications?source="
    fv_age = Facetview2.make_query(sort_parameter="last_manual_update")
    ed_age_url = ed_fv_prefix + Facetview2.url_encode_query(fv_age)

    es = models.Suggestion.query(q=ed_age_query.query())
    group_stats = [(bucket.get("key"), bucket.get("doc_count")) for bucket in es.get("aggregations", {}).get("ed_group_counts", {}).get("buckets", [])]

    if limit is not None and isinstance(limit, int):
        group_stats = group_stats[:limit]

    # Get the email addresses for the editor in charge of each group, Add the template to their email
    for (group_name, group_count) in group_stats:
        # get editor group object by name
        eg = models.EditorGroup.pull_by_key("name", group_name)
        if eg is None:
            continue

        # Get the email address to the editor account
        editor = eg.get_editor_account()
        ed_email = editor.email

        text = render_template('email/workflow_reminder_fragments/editor_age_frag', num=group_count, ed_group=group_name, url=ed_age_url, x_weeks=X_WEEKS)
        _add_email_paragraph(emails_dict, ed_email, eg.editor, text)


def associate_editor_notifications(emails_dict, limit=None):
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
    status_filters = [Facetview2.make_term_filter(term, status) for status in relevant_statuses]

    assoc_age_query = AssEdAgeQuery(idle_date_stamp, very_idle_date_stamp, status_filters)
    url = app.config.get("BASE_URL") + "/editor/your_applications"

    es = models.Suggestion.query(q=assoc_age_query.query())
    buckets = es.get("aggregations", {}).get("assoc_ed", {}).get("buckets", [])

    if limit is not None and isinstance(limit, int):
        buckets = buckets[:limit]

    for bucket in buckets:    # loop through assoc_ed buckets
        assoc_id = bucket.get("key")
        idle = bucket.get("doc_count")

        # Get the 'older than y weeks' count from nested aggregation
        very_idle = bucket.get("older_weeks").get("buckets")[0].get('doc_count')        # only one bucket, so take first

        # Pull the email address for our associate editor from their account
        assoc = models.Account.pull(assoc_id)
        try:
            assoc_email = assoc.email
        except AttributeError:
            # There isn't an account for that id
            app.logger.warn("No account found for ID {0}".format(assoc_id))
            continue

        text = render_template('email/workflow_reminder_fragments/assoc_ed_age_frag', num_idle=idle, x_days=X_DAYS, num_very_idle=very_idle, y_weeks=Y_WEEKS, url=url)
        _add_email_paragraph(emails_dict, assoc_email, assoc_id, text)


def send_emails(emails_dict):

    for (email, (to_name, paragraphs)) in emails_dict.items():
        pre = 'Dear ' + to_name + ',\n\n'
        post = '\n\nThe DOAJ Team\n\n***\nThis is an automated message. Please do not reply to this email.'
        full_body = pre + '\n\n'.join(paragraphs) + post

        app_email.send_mail(to=[email],
                            fro=app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org'),
                            subject="DOAJ editorial reminders",
                            msg_body=full_body)


def _add_email_paragraph(emails_dict, addr, to_name, para_string):
    """
    Add a new email to the global dict which stores the email fragments, or extend an existing one.
    :param emails_dict: target object to store the emails
    :param addr: email address for recipient
    :param to_name: name of recipient
    :param para_string: paragraph to add to the email
    """

    try:
        (name, paras) = emails_dict[addr]
        paras.append(para_string)
    except KeyError:
        emails_dict[addr] = (to_name, [para_string])


class AsyncWorkflowBackgroundTask(BackgroundTask):

    __action__ = "async_workflow_notifications"

    def run(self):
        """
        Execute the task as specified by the background_job
        """
        job = self.background_job

        """ Run through each notification type, then send emails """
        # Create a request context to render templates
        ctx = app.test_request_context()
        ctx.push()

        # Store all of the emails: { email_addr : (name, [paragraphs]) }
        emails_dict = {}

        # Gather info and build the notifications
        managing_editor_notifications(emails_dict)
        editor_notifications(emails_dict)
        associate_editor_notifications(emails_dict)

        # Discard the context (the send mail function makes its own)
        ctx.pop()

        send_emails(emails_dict)

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        """
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception
        :param username: user who called this job
        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        if not app.config.get("ENABLE_EMAIL", False):
            raise BackgroundException("Email has been disabled in config. Set ENABLE_EMAIL to True to run this task.")

        # first prepare a job record
        return background_helper.create_job(username, cls.__action__, queue_id=huey_helper.queue_id)

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue
        :param background_job: the BackgroundJob instance
        """
        background_job.save()
        async_workflow_notifications.schedule(args=(background_job.id,), delay=10)


huey_helper = AsyncWorkflowBackgroundTask.create_huey_helper(main_queue)


@huey_helper.task_queue.periodic_task(schedule("async_workflow_notifications"))
def scheduled_async_workflow_notifications():
    user = app.config.get("SYSTEM_USERNAME")
    job = AsyncWorkflowBackgroundTask.prepare(user)
    AsyncWorkflowBackgroundTask.submit(job)


@huey_helper.task_queue.task()
def async_workflow_notifications(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = AsyncWorkflowBackgroundTask(job)
    BackgroundApi.execute(task)
