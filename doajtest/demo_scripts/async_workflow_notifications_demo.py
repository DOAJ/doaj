""" Building emails to send asynchronously, via cron job or scheduler """
# THIS IS A DEMO WHICH LIMITS THE NUMBER OF EMAILS SENT, and is rate limited for mailtrap

from portality import app_email
from portality.core import app
from portality.tasks import async_workflow_notifications

import time


# Replace the async workflow send function with this one to limit emails sent in this demo.
def send_emails(emails_dict):

    for (email, (to_name, paragraphs)) in emails_dict.iteritems():
        time.sleep(0.6)
        pre = 'Dear ' + to_name + ',\n\n'
        post = '\n\nThe DOAJ Team\n\n***\nThis is an automated message. Please do not reply to this email.'
        full_body = pre + '\n\n'.join(paragraphs) + post

        app_email.send_mail(to=[email],
                            fro=app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org'),
                            subject="DOAJ editorial reminders",
                            msg_body=full_body)


# Main function for running all notification types in sequence
def run_async_notifications():
    """ Run through each notification type, then send emails """
    # Create a request context to render templates
    ctx = app.test_request_context()
    ctx.push()

    # Store all of the emails: { email_addr : (name, [paragraphs]) }
    emails_dict = {}

    # Gather info and build the notifications
    async_workflow_notifications.managing_editor_notifications(emails_dict)
    async_workflow_notifications.editor_notifications(emails_dict, limit=5)
    async_workflow_notifications.associate_editor_notifications(emails_dict, limit=5)

    # Discard the context (the send mail function makes its own)
    ctx.pop()

    send_emails(emails_dict)

# Run all if the script is called.
if __name__ == '__main__':
    run_async_notifications()
