from doajtest.testdrive.factory import TestDrive
from portality import models
from doajtest.fixtures.application_validate_csv import ApplicationValidateCSVFixtureFactory

class PublisherCsvUpload(TestDrive):

    def setup(self) -> dict:
        un = self.create_random_str()
        pw = self.create_random_str()

        artefacts = ApplicationValidateCSVFixtureFactory.create_test_artefacts(un, pw)

        artefacts["account"].save()

        def eliminate_existing(issns):
            for issn in issns:
                existing = models.Journal.find_by_issn(issn)
                for e in existing:
                    e.delete()

        eliminate_existing([
            "0000-0001",
            "0000-0002",
            "0000-0003",
            "0000-0004",
            "0000-0005",
            "0000-0006",
            "0000-0007",
            "0000-0008",
            "0000-0009",
            "0000-0010",
            "0000-0011",
            "0000-0012",
            "0000-0013",
            "0000-0014",
            "0000-0015",
            "0000-0016"
        ])

        for k, v in artefacts["journals"].items():
            v.save()

        return {
            "account": {
                "username": artefacts["account"].id,
                "password": pw
            },
            "journals": {
                "valid1": artefacts["journals"]["valid1"].id,
                "valid2": artefacts["journals"]["valid2"].id,
                "not_owner": artefacts["journals"]["not_owner"].id,
                "no_updates": artefacts["journals"]["no_updates"].id,
                "changed_title": artefacts["journals"]["changed_title"].id,
                "withdrawn": artefacts["journals"]["withdrawn"].id,
                "validation_fail": artefacts["journals"]["validation_fail"].id
            }
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for k, v in params["journals"].items():
            models.Journal.remove_by_id(v)
        return {"status": "success"}
