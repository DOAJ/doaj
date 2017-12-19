from doajtest.helpers import DoajTestCase
from parameterized import parameterized, param
from doajtest.fixtures import JournalFixtureFactory, ApplicationFixtureFactory
import uuid

from copy import deepcopy

from portality.models import Journal, Suggestion

from portality.bll import DOAJ
from portality.bll import exceptions


def load_journal_cases():
    journal = Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
    journal.makeid()

    wrong_id = uuid.uuid4()

    return [
        param("no_journal_no_id", None, None, raises=exceptions.ArgumentException),
        param("no_journal", None, journal.id),
        param("journal_wrong_id", journal, wrong_id),
        param("journal_right_id", journal, journal.id)
    ]

def load_application_cases():
    application = Suggestion(**ApplicationFixtureFactory.make_application_source())
    application.makeid()

    wrong_id = uuid.uuid4()

    return [
        param("no_app_no_id", None, None, raises=exceptions.ArgumentException),
        param("no_app", None, application.id),
        param("app_wrong_id", application, wrong_id),
        param("app_right_id", application, application.id)
    ]

class TestBLLGetters(DoajTestCase):

    @parameterized.expand(load_journal_cases)
    def test_01_get_journal(self, name, journal, journal_id, raises=None):
        doaj = DOAJ()

        if journal is not None:
            journal.save(blocking=True)

        if raises is not None:
            with self.assertRaises(raises):
                retrieved = doaj.journal(journal_id)
        else:
            retrieved = doaj.journal(journal_id)
            if retrieved is not None:
                assert retrieved.data == journal.data
            else:
                assert retrieved is None

    @parameterized.expand(load_application_cases)
    def test_02_get_application(self, name, application, application_id, raises=None):
        doaj = DOAJ()

        if application is not None:
            application.save(blocking=True)

        if raises is not None:
            with self.assertRaises(raises):
                retrieved = doaj.application(application_id)
        else:
            retrieved = doaj.application(application_id)
            if retrieved is not None:
                assert retrieved.data == application.data
            else:
                assert retrieved is None
