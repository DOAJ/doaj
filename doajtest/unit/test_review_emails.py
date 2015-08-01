from doajtest.helpers import DoajTestCase

from portality import models
from portality.formcontext import formcontext
from portality.core import app
from portality import lcc

from werkzeug.routing import BuildError

from doajtest.fixtures import EditorGroupFixtureFactory, AccountFixtureFactory, ApplicationFixtureFactory

APPLICATION_SOURCE = ApplicationFixtureFactory.make_application_source()
APPLICATION_FORM = ApplicationFixtureFactory.make_application_form()

EDITOR_GROUP_SOURCE = EditorGroupFixtureFactory.make_editor_group_source()
EDITOR_SOURCE = AccountFixtureFactory.make_editor_source()
ASSED_SOURCE = AccountFixtureFactory.make_assed3_source()

#####################################################################
# Mocks required to make some of the lookups work
#####################################################################

@classmethod
def editor_group_pull(cls, field, value):
    eg = models.EditorGroup(**EDITOR_GROUP_SOURCE)
    return eg

@classmethod
def editor_account_pull(self, _id):
    if _id == 'eddie':
        return models.Account(**EDITOR_SOURCE)
    if _id == 'associate_3':
        return models.Account(**ASSED_SOURCE)


class TestApplicationReviewEmails(DoajTestCase):

    def setUp(self):
        super(TestApplicationReviewEmails, self).setUp()

        self.editor_group_pull = models.EditorGroup.pull_by_key
        models.EditorGroup.pull_by_key = editor_group_pull

        self.editor_account_pull = models.Account.pull
        models.Account.pull = editor_account_pull

    def tearDown(self):
        super(TestApplicationReviewEmails, self).tearDown()

        models.EditorGroup.pull_by_key = self.editor_group_pull
        models.Account.pull = self.editor_account_pull

    def test_01_maned_review_emails(self):
        """ Ensure the Managing Editor's application review form sends the right emails"""

        # If an application has been set to 'ready' but is returned to 'in progress', an email is sent to the editor
        ready_application = models.Suggestion(**APPLICATION_SOURCE)
        ready_application.set_application_status("ready")

        # Construct an application form
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role="admin",
            source=ready_application
        )
        assert isinstance(fc, formcontext.ManEdApplicationReview)

        # Make changes to the application status via the form
        fc.form.application_status.data = "in progress"

        # Emails are sent during the finalise stage, and requires the app context to build URLs
        with app.test_request_context():
            try:                # fixme: this might be bad. I expect it to error, but the error shows my code works so I've incorporated it into my test.
                fc.finalise()
            except BuildError as e:
                assert str(e) == "('editor.group_suggestions', {'source': '{\"query\":{\"query_string\":{\"query\":\"abcdefghijk\",\"default_operator\":\"OR\"}}}'}, None)"

        # Prove we went from to and from the right statuses
        assert fc.source.application_status == "ready"
        assert fc.target.application_status == "in progress"

        # Next, if we change the editor group or assigned editor, emails should be sent to editors and the publisher.
        # Construct a new application form
        fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=models.Suggestion(**APPLICATION_SOURCE))
        assert isinstance(fc, formcontext.ManEdApplicationReview)

        fc.form.editor_group.data = "Test Editor Group"
        fc.form.editor.data = "associate_3"

        # Finalise again to send emails, no url building this time so no request context required.
        fc.finalise()

        assert fc.target.editor == "associate_3"
        assert True # gives us a place to drop a break point later if we need it
