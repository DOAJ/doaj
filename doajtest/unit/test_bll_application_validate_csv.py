import os

from doajtest.fixtures.application_validate_csv import ApplicationValidateCSVFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality import models
from portality.lib import paths
from portality.ui.messages import Messages
from portality.crosswalks.journal_questions import Journal2PublisherUploadQuestionsXwalk

EXAMPLE_FILES_DIR = paths.rel2abs(__file__, "..", "example_files")

class TestApplicationValidateCSV(DoajTestCase):

    def setUp(self):
        super(TestApplicationValidateCSV, self).setUp()

        self.artefacts = ApplicationValidateCSVFixtureFactory.create_test_artefacts("testuser", "testpass")

        awaiting = []
        for k, v in self.artefacts["journals"].items():
            v.save()
            awaiting.append((v.id, v.last_updated))
        models.Journal.blockall(awaiting)

    def tearDown(self):
        super(TestApplicationValidateCSV, self).tearDown()

    def test_01_invalid_headers(self):
        test_file = os.path.join(EXAMPLE_FILES_DIR, "publisher_csv_invalid_headers.csv")
        app_svc = DOAJ.applicationService()
        validation_response  = app_svc.validate_update_csv(test_file, self.artefacts["account"])
        assert validation_response.has_errors_or_warnings() is True

        pissn_name = Journal2PublisherUploadQuestionsXwalk.q("pissn")
        required_header = Messages.JOURNAL_CSV_VALIDATE__REQUIRED_HEADER_MISSING.format(h=pissn_name)
        assert len(validation_response.general_errors) == 1
        assert required_header in [e for t, e in validation_response.general_errors]

        journal_title = Journal2PublisherUploadQuestionsXwalk.q("title")
        mismatch_case = Messages.JOURNAL_CSV_VALIDATE__HEADER_CASE_MISMATCH.format(h="journal title", expected=journal_title)
        assert len(validation_response.header_errors.keys()) == 2
        assert validation_response.header_errors[0][1] == mismatch_case

        unexpected_header = Messages.JOURNAL_CSV_VALIDATE__INVALID_HEADER.format(h="Extra unexpected header")
        assert validation_response.header_errors[10][1] == unexpected_header

    def test_02_invalid_data(self):
        test_file = os.path.join(EXAMPLE_FILES_DIR, "publisher_csv_invalid_data.csv")
        app_svc = DOAJ.applicationService()
        validation_response = app_svc.validate_update_csv(test_file, self.artefacts["account"])
        assert validation_response.has_errors_or_warnings() is True

        not_found_1 = Messages.JOURNAL_CSV_VALIDATE__MISSING_JOURNAL.format(issns=", ".join(["0000-0005","0000-0006"]))
        assert validation_response.row_errors[2][1] == not_found_1

        not_found_2 = Messages.JOURNAL_CSV_VALIDATE__MISSING_JOURNAL.format(issns=", ".join(["0000-0013", "0000-0014"]))
        assert validation_response.row_errors[6][1] == not_found_2

        owner_mismatch = Messages.JOURNAL_CSV_VALIDATE__OWNER_MISMATCH.format(acc=self.artefacts["account"].id, issns=", ".join(["0000-0007","0000-0008"]))
        assert validation_response.row_errors[3][1] == owner_mismatch

        assert validation_response.row_errors[4][1] == Messages.JOURNAL_CSV_VALIDATE__NO_DATA_CHANGE

        journal_title = Journal2PublisherUploadQuestionsXwalk.q("title")
        disabled_change = Messages.JOURNAL_CSV_VALIDATE__QUESTION_CANNOT_CHANGE.format(question=journal_title)
        assert validation_response.value_errors[5][0][1] == disabled_change

        # validation errors are hard to check, we're just going to make sure they are there
        assert 4 in validation_response.value_errors[7]
        assert 5 in validation_response.value_errors[7]
        assert 6 not in validation_response.value_errors[7] # because it is a conditional field which will be excluded
        assert 7 in validation_response.value_errors[7]
        assert 8 not in validation_response.value_errors[7]  # because it is a conditional field which will be excluded
        assert 9 in validation_response.value_errors[7]
        assert 10 not in validation_response.value_errors[7]  # because it is a conditional field which will be excluded

        # invalid data check
        assert 6 in validation_response.value_errors[8]

    def test_03_upload_warnings(self):
        test_file = os.path.join(EXAMPLE_FILES_DIR, "publisher_csv_upload_warnings.csv")
        app_svc = DOAJ.applicationService()
        validation_response = app_svc.validate_update_csv(test_file, self.artefacts["account"])
        assert validation_response.has_errors_or_warnings() is True
        assert validation_response.has_errors() is False
        assert validation_response.has_warnings() is True

        journal_title = Journal2PublisherUploadQuestionsXwalk.q("title")
        mismatch_case = Messages.JOURNAL_CSV_VALIDATE__HEADER_CASE_MISMATCH.format(h="journal title",
                                                                                   expected=journal_title)
        assert len(validation_response.header_errors.keys()) == 1
        assert validation_response.header_errors[0][1] == mismatch_case

        assert validation_response.row_errors[5][1] == Messages.JOURNAL_CSV_VALIDATE__NO_DATA_CHANGE

    def test_04_upload_success(self):
        test_file = os.path.join(EXAMPLE_FILES_DIR, "publisher_csv_upload_success.csv")
        app_svc = DOAJ.applicationService()
        validation_response = app_svc.validate_update_csv(test_file, self.artefacts["account"])
        assert validation_response.has_errors_or_warnings() is False