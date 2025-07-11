# ~~Constants:Config~~

# ~~-> ApplicationStatuses:Config~~
APPLICATION_STATUS_ACCEPTED = "accepted"
APPLICATION_STATUS_REJECTED = "rejected"
APPLICATION_STATUS_UPDATE_REQUEST = "update_request"
APPLICATION_STATUS_REVISIONS_REQUIRED = "revisions_required"
APPLICATION_STATUS_PENDING = "pending"
APPLICATION_STATUS_IN_PROGRESS = "in progress"
APPLICATION_STATUS_COMPLETED = "completed"
APPLICATION_STATUS_ON_HOLD = "on hold"
APPLICATION_STATUS_READY = "ready"
APPLICATION_STATUS_POST_SUBMISSION_REVIEW = "post_submission_review"

APPLICATION_STATUSES_ALL = [
    APPLICATION_STATUS_ACCEPTED,
    APPLICATION_STATUS_REJECTED,
    APPLICATION_STATUS_UPDATE_REQUEST,
    APPLICATION_STATUS_REVISIONS_REQUIRED,
    APPLICATION_STATUS_PENDING,
    APPLICATION_STATUS_IN_PROGRESS,
    APPLICATION_STATUS_COMPLETED,
    APPLICATION_STATUS_ON_HOLD,
    APPLICATION_STATUS_READY,
    APPLICATION_STATUS_POST_SUBMISSION_REVIEW
]

APPLICATION_TYPE_UPDATE_REQUEST = "update_request"
APPLICATION_TYPE_NEW_APPLICATION = "new_application"

INDEX_RECORD_TYPE_UPDATE_REQUEST_UNFINISHED = "Update Request (in progress)"
INDEX_RECORD_TYPE_UPDATE_REQUEST_FINISHED = "Update Request (finished)"
INDEX_RECORD_TYPE_NEW_APPLICATION_UNFINISHED = "Application (in progress)"
INDEX_RECORD_TYPE_NEW_APPLICATION_FINISHED = "Application (finished)"

PROVENANCE_STATUS_REJECTED = "status:rejected"
PROVENANCE_STATUS_ACCEPTED = "status:accepted"

LOCK_APPLICATION = "suggestion"
LOCK_JOURNAL = "journal"

IDENT_TYPE_DOI = "doi"
LINK_TYPE_FULLTEXT = "fulltext"

# ~~-> Todo:Service~~
TODO_MANED_STALLED = "todo_maned_stalled"
TODO_MANED_FOLLOW_UP_OLD = "todo_maned_follow_up_old"
TODO_MANED_READY = "todo_maned_ready"
TODO_MANED_COMPLETED = "todo_maned_completed"
TODO_MANED_ASSIGN_PENDING = "todo_maned_assign_pending"
TODO_MANED_LAST_MONTH_UPDATE_REQUEST = "todo_maned_last_month_update_request"
TODO_MANED_NEW_UPDATE_REQUEST = "todo_maned_new_update_request"
TODO_MANED_ON_HOLD = "todo_maned_on_hold"
TODO_EDITOR_STALLED = "todo_editor_stalled"
TODO_EDITOR_FOLLOW_UP_OLD = "todo_editor_follow_up_old"
TODO_EDITOR_COMPLETED = "todo_editor_completed"
TODO_EDITOR_ASSIGN_PENDING = "todo_editor_assign_pending"
TODO_EDITOR_ASSIGN_PENDING_LOW_PRIORITY = "todo_editor_assign_pending_low_priority"
TODO_ASSOCIATE_PROGRESS_STALLED = "todo_associate_progress_stalled"
TODO_ASSOCIATE_FOLLOW_UP_OLD = "todo_associate_follow_up_old"
TODO_ASSOCIATE_START_PENDING = "todo_associate_start_pending"
TODO_ASSOCIATE_ALL_APPLICATIONS = "todo_associate_all_applications"

EVENT_ACCOUNT_CREATED = "account:created"
EVENT_ACCOUNT_PASSWORD_RESET = "account:password_reset"
EVENT_APPLICATION_STATUS = "application:status"
EVENT_APPLICATION_ASSED_ASSIGNED = "application:assed:assigned"
EVENT_APPLICATION_CREATED = "application:created"
EVENT_APPLICATION_UR_SUBMITTED = "application:ur_submitted"
EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED = "application:editor_group:assigned"
EVENT_JOURNAL_ASSED_ASSIGNED = "journal:assed:assigned"
EVENT_JOURNAL_EDITOR_GROUP_ASSIGNED = "journal:editor_group:assigned"
EVENT_JOURNAL_DISCONTINUING_SOON = "journal:discontinuing_soon"

NOTIFICATION_CLASSIFICATION_STATUS = "alert"
NOTIFICATION_CLASSIFICATION_STATUS_CHANGE = "status_change"
NOTIFICATION_CLASSIFICATION_ASSIGN = "assign"
NOTIFICATION_CLASSIFICATION_CREATE = "create"
NOTIFICATION_CLASSIFICATION_FINISHED = "finished"

BACKGROUND_JOB_FINISHED = "bg:job_finished"

PROCESS__QUICK_REJECT = "quick_reject"

# Roles
ROLE_ADMIN = "admin"
ROLE_PUBLISHER = "publisher"
ROLE_EDITOR = "editor"
ROLE_ASSOCIATE_EDITOR = 'associate_editor'
ROLE_PUBLIC_DATA_DUMP = "public_data_dump"
ROLE_PUBLISHER_JOURNAL_CSV = "journal_csv"
ROLE_PUBLISHER_PRESERVATION = "preservation"
ROLE_API = "api"
# TODO add ultra_bulk_delete and refactor view to use constants
ROLE_ADMIN_REPORT_WITH_NOTES = "ultra_admin_reports_with_notes"  # MUST start with ultra_ so that superusers don't gain

CRON_NEVER = {"month": "2", "day": "31", "day_of_week": "*", "hour": "*", "minute": "*"}

# ~~-> BackgroundTask:Monitoring~~
# BackgroundJob.status
BGJOB_STATUS_QUEUED = 'queued'
BGJOB_STATUS_PROCESSING = 'processing'
BGJOB_STATUS_ERROR = 'error'
BGJOB_STATUS_COMPLETE = 'complete'

# BackgroundJob.queue_id
# ~~->BackgroundTasks:Feature~~
BGJOB_QUEUE_ID_LONG = 'long_running'
BGJOB_QUEUE_ID_MAIN = 'main_queue'
BGJOB_QUEUE_ID_UNKNOWN = 'unknown'
BGJOB_QUEUE_ID_EVENTS = "events"
BGJOB_QUEUE_ID_SCHEDULED_SHORT = "scheduled_short"
BGJOB_QUEUE_ID_SCHEDULED_LONG = "scheduled_long"

# Background monitor status
BG_STATUS_STABLE = 'stable'
BG_STATUS_UNSTABLE = 'unstable'


class ConstantList:
    @classmethod
    def all_constants(cls):
        att_names = cls.__dict__
        att_names = (i for i in att_names if not (i.startswith('__') and i.endswith('__')))
        return (getattr(cls, n) for n in att_names)


class FileUploadStatus(ConstantList):
    Processed = 'processed'
    Failed = 'failed'
    Incoming = 'incoming'
    Validated = 'validated'


class BgjobOutcomeStatus(ConstantList):
    Pending = 'pending'
    Success = 'success'
    Fail = 'fail'


class BaseArticlesUploadStatus(ConstantList):
    Processed = 'processed'


# Storage scopes
STORE__SCOPE__PUBLIC_DATA_DUMP = "public_data_dump"

# OAI
SUBJECTS_SCHEMA = "LCC:"

# Extra params
EXPARAM_EDITING_USER = 'editing_user'
