# Account management
GLOBAL_LOGIN = "public/account/login.html"
LOGIN_TO_APPLY = "public/account/login_to_apply.html"
FORGOT_PASSWORD = "public/account/forgot.html"
REGISTER = "public/account/register.html"
CREATE_USER = "management/admin/account/create.html"
RESET_PASSWORD = "public/account/reset.html"
USER_LIST = "management/admin/account/users.html"
ADMIN_EDIT_USER = "management/admin/account/edit.html"
EDITOR_EDIT_USER = "management/editor/account/edit.html"
PUBLIC_EDIT_USER = "public/account/edit.html"

# Public pages
PUBLIC_INDEX = "public/index.html"
PUBLIC_ARTICLE = "public/article.html"
PUBLIC_ARTICLE_SEARCH = "public/articles_search.html"
PUBLIC_JOURNAL_SEARCH = "public/journals_search.html"
PUBLIC_READ_ONLY_MODE = "public/readonly_mode.html"
PUBLIC_TOC_MAIN = "public/toc_main.html"
PUBLIC_TOC_ARTICLES = "public/toc_articles.html"
OPENURL_404 = "public/openurl/404.html"
OPENURL_HELP = "public/openurl/help.html"

# Static content
STATIC_PAGE = "public/layouts/static-page.html"
STATIC_PAGE_LAYOUT = "public/layouts/_static-page_{layout}.html"

# Error pages
ERROR_400 = "public/400.html"
ERROR_401 = "public/401.html"
ERROR_404 = "public/404.html"
ERROR_410 = "public/410.html"
ERROR_500 = "public/500.html"

# API
API_V3_DOCS = "public/api/v3/api_docs.html"
API_V4_DOCS = "public/api/v4/api_docs.html"

# Admin area
ADMIN_SITE_SEARCH = "management/admin/admin_site_search.html"
APPLICATION_LOCKED = "management/admin/application_locked.html"
APPLICATIONS_SEARCH = "management/admin/applications.html"
ADMIN_ARTICLE_FORM = "management/admin/article_metadata.html"
ADMIN_REPORTS_SEARCH = "management/admin/reports_search.html"
BACKGROUND_JOBS_SEARCH = "management/admin/background_jobs_search.html"
CONTINUATION = "management/admin/continuation.html"
EDITOR_GROUP = "management/admin/editor_group.html"
EDITOR_GROUP_SEARCH = "management/admin/editor_group_search.html"
GLOBAL_NOTIFICATIONS_SEARCH = "management/admin/global_notifications_search.html"
ADMIN_JOURNALS_SEARCH = "management/admin/journals_search.html"
JOURNAL_LOCKED = "management/admin/journal_locked.html"
UPDATE_REQUESTS_SEARCH = "management/admin/update_requests.html"
DASHBOARD = "management/admin/dashboard.html"
NOTIFICATIONS = "management/admin/notifications.html"
ADMIN_UNLOCKED = "management/admin/unlocked.html"

# Application Form
MANED_APPLICATION_FORM = "management/admin/maned_application.html"
MANED_JOURNAL_FORM = "management/admin/maned_journal.html"
EDITOR_APPLICATION_FORM = "management/editor/editor_application.html"
EDITOR_JOURNAL_FORM = "management/editor/editor_journal.html"
ASSED_APPLICATION_FORM = "management/editor/assed_application.html"
ASSED_JOURNAL_FORM = "management/editor/assed_journal.html"
PUBLIC_APPLICATION_FORM = "public/public_application.html"
PUBLISHER_UPDATE_REQUEST_FORM = "public/publisher/publisher_update_request.html"
PUBLISHER_READ_ONLY_APPLICATION = "public/publisher/readonly_application.html"
MANED_READ_ONLY_JOURNAL = "management/admin/readonly_journal.html"
EDITOR_READ_ONLY_JOURNAL = "management/editor/readonly_journal.html"
MANED_JOURNAL_BULK_EDIT = "management/admin/_application-form/layouts/maned_journal_bulk_edit.html"

# Reusable application form components
AF_ENTRY_GOUP = "_application-form/includes/_entry_group.html"
AF_ENTRY_GROUP_HORIZONTAL = "_application-form/includes/_entry_group_horizontal.html"
AF_FIELD = "_application-form/includes/_field.html"
AF_GROUP = "_application-form/includes/_group.html"
AF_LIST = "_application-form/includes/_list.html"

# Publisher area
PUBLISHER_DRAFTS = "public/publisher/drafts.html"
PUBLISHER_APPLICATION_ALREADY_SUBMITTED = "public/publisher/application_already_submitted.html"
PUBLISHER_APPLICATION_DELETED = "public/publisher/application_deleted.html"
PUBLISHER_XML_HELP = "public/publisher/xml_help.html"
PUBLISHER_CSV_UPLOAD = "public/publisher/journal_csv.html"
PUBLISHER_JOURNAL_SEARCH = "public/publisher/journals.html"
PUBLISHER_LOCKED = "public/publisher/locked.html"
PUBLISHER_ARTICLE_METADATA = "public/publisher/article_metadata.html"
PUBLISHER_PRESERVATION = "public/publisher/preservation.html"
PUBLISHER_PRESERVATION_READONLY = "public/publisher/readonly_preservation.html"
PUBLISHER_UPDATE_REQUESTS = "public/publisher/update_requests.html"
PUBLISHER_XML_UPLOAD = "public/publisher/xml_upload.html"

# Editor Area
EDITOR_APPLICATION_LOCKED = "management/editor/application_locked.html"
EDITOR_YOUR_APPLICATIONS_SEARCH = "management/editor/your_applications.html"
EDITOR_DASHBOARD = "management/editor/dashboard.html"
EDITOR_GROUP_APPLICATIONS_SEARCH = "management/editor/group_applications.html"
EDITOR_UNLOCKED = "management/editor/unlocked.html"

# Utilities
SITE_NOTE = "includes/_site_note.html"

# Email templates
EMAIL_ACCOUNT_CREATED = "email/account_created.jinja2"
EMAIL_PASSWORD_RESET = "email/account_password_reset.jinja2"
EMAIL_NOTIFICATION = "email/notification_email.jinja2"
EMAIL_SCRIPT_TAG_DETECTED = "email/script_tag_detected.jinja2"
EMAIL_EDITOR_APPLICATION_COMPLETED = "email/editor_application_completed.jinja2"
EMAIL_WF_ADMIN_AGE = "email/workflow_reminder_fragments/admin_age_frag.jinja2"
EMAIL_WF_ADMIN_READY = "email/workflow_reminder_fragments/admin_ready_frag.jinja2"
EMAIL_WF_ASSED_AGE = "email/workflow_reminder_fragments/assoc_ed_age_frag.jinja2"
EMAIL_WF_EDITOR_AGE = "email/workflow_reminder_fragments/editor_age_frag.jinja2"
EMAIL_WF_EDITOR_GROUPCOUNT = "email/workflow_reminder_fragments/editor_groupcount_frag.jinja2"