# ~~Constants:Config~~
APPLICATION_STATUS_ACCEPTED = "accepted"
APPLICATION_STATUS_REJECTED = "rejected"
APPLICATION_STATUS_UPDATE_REQUEST = "update_request"
APPLICATION_STATUS_REVISIONS_REQUIRED = "revisions_required"
APPLICATION_STATUS_PENDING = "pending"
APPLICATION_STATUS_IN_PROGRESS = "in progress"
APPLICATION_STATUS_COMPLETED = "completed"
APPLICATION_STATUS_ON_HOLD = "on hold"
APPLICATION_STATUS_READY = "ready"

APPLICATION_STATUSES_ALL = [
    APPLICATION_STATUS_ACCEPTED,
    APPLICATION_STATUS_REJECTED,
    APPLICATION_STATUS_UPDATE_REQUEST,
    APPLICATION_STATUS_REVISIONS_REQUIRED,
    APPLICATION_STATUS_PENDING,
    APPLICATION_STATUS_IN_PROGRESS,
    APPLICATION_STATUS_COMPLETED,
    APPLICATION_STATUS_ON_HOLD,
    APPLICATION_STATUS_READY
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

EVENT_ACCOUNT_CREATED = "account:created"
EVENT_ACCOUNT_PASSWORD_RESET = "account:password_reset"
EVENT_APPLICATION_STATUS = "application:status"
EVENT_APPLICATION_ASSED_ASSIGNED = "application:assed:assigned"
EVENT_APPLICATION_CREATED = "application:created"
EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED = "application:editor_group:assigned"
EVENT_JOURNAL_ASSED_ASSIGNED = "journal:assed:assigned"
EVENT_JOURNAL_EDITOR_GROUP_ASSIGNED = "journal:editor_group:assigned"

NOTIFICATION_CLASSIFICATION_STATUS_CHANGE = "status_change"
NOTIFICATION_CLASSIFICATION_ASSIGN = "assign"
NOTIFICATION_CLASSIFICATION_CREATE = "create"
NOTIFICATION_CLASSIFICATION_FINISHED = "finished"

BACKGROUND_JOB_FINISHED = "bg:job_finished"

PROCESS__QUICK_REJECT = "quick_reject"

# Role
ROLE_ASSOCIATE_EDITOR = 'associate_editor'
ROLE_PUBLIC_DATA_DUMP = "public_data_dump"

CRON_NEVER = {"month": "2", "day": "31", "day_of_week": "*", "hour": "*", "minute": "*"}

# ~~-> BackgroundTask:Monitoring~~
# BackgroundJob.status
BGJOB_STATUS_QUEUED = 'queued'
BGJOB_STATUS_ERROR = 'error'
BGJOB_STATUS_COMPLETE = 'complete'

# BackgroundJob.queue_id
# ~~->BackgroundTasks:Feature~~
BGJOB_QUEUE_ID_LONG = 'long_running'
BGJOB_QUEUE_ID_MAIN = 'main_queue'
BGJOB_QUEUE_ID_UNKNOWN = 'unknown'

# Background monitor status
BG_STATUS_STABLE = 'stable'
BG_STATUS_UNSTABLE = 'unstable'

# Storage scopes
STORE__SCOPE__PUBLIC_DATA_DUMP = "public_data_dump"

# OAI
SUBJECTS_SCHEMA = "LCC:"
