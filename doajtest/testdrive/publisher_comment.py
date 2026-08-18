from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory
from portality import constants
from doajtest.testdrive.factory import TestDrive
from portality import models
from portality.lib import dates
from portality.core import app

DATA = {
    "publisher_name": "Institute for Moonlit Ecology",
    "admin": {
        "username": "DrVesperCeleste",
        "email": "c.vesper@moonlightecology.example.org",
        "role": constants.ROLE_PUBLISHER,
    },
    "publisher": {
        "username": "QuillMartin",
        "email": "martin.quill@scholarlyindex.example.org",
        "role": [constants.ROLE_ADMIN],
    },
    "draft": {
        "title": "Journal of Nocturnal Pollination Studies",
        "alternative_title": "Nocturnal Pollination Research",
        "comment": (
            "This journal was established to address a persistent gap in "
            "pollination research: a considerable proportion of fieldwork "
            "concludes shortly before the moths arrive. The first issue is "
            "scheduled for October 2026."
        ),
    },
    "update_request": {
        "title": "International Review of Applied Hibernation",
        "alternative_title": "Review of Torpor and Seasonal Dormancy",
        "issn": "2048-7316",
        "url": (
            "https://moonlightecology.example.org/journals/seasonal-unavailability"
        ),
        "comment": (
            "We have added 'torpor economics' to reflect the journal’s growing coverage "
            "of energy conservation, seasonal resource allocation, and the measurable "
            "benefits of remaining unavailable until spring."
        ),
        "keywords": [
                "comparative hibernation",
                "seasonal torpor",
        ],
        "new_keyword": "torpor economics",
    }
}

class PublisherComment(TestDrive):
    admin: models.Account
    publisher: models.Account
    draft: models.Application
    journal: models.Journal

    def __init__(self):
        super(PublisherComment, self).__init__()
        self.users = ["admin", "publisher"]

    def setup(self) -> dict:
        s = self.seeded
        # admin
        admin_username = s(DATA["admin"]["username"])
        admin_password = self.create_random_str()
        self.admin = models.Account.make_account(DATA["admin"]["email"], admin_username, f"{admin_username}(Admin)", [DATA["admin"]["role"]])
        self.admin.set_password(admin_password)
        self.admin.save()

        # publisher
        publisher_username = s(DATA["publisher"]["username"])
        publisher_password = self.create_random_str()
        self.publisher = models.Account.make_account(DATA["publisher"]["email"], publisher_username, f"{publisher_username}(Publisher)", [DATA["publisher"]["role"]])
        self.publisher.set_password(publisher_password)
        self.publisher.save()

        # new draft application
        source = ApplicationFixtureFactory.make_application_source()
        self.draft = models.DraftApplication(**source)
        self.draft.set_id(self.draft.makeid())
        self.draft.set_application_status("draft")
        self.draft.set_owner(self.publisher.id)
        self.draft.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
        self.draft.remove_related_journal()
        self.draft.date_applied = dates.now_str()
        bj = self.draft.bibjson()
        bj.title = s(DATA["draft"]["title"])
        bj.alternative_title = DATA["draft"]["alternative_title"]
        bj.pissn = self.generate_unique_issn()
        bj.eissn = self.generate_unique_issn()
        bj.publisher_name = DATA["publisher_name"]
        self.draft.save()

        # journal
        source = JournalFixtureFactory.make_journal_source()
        self.journal = models.Journal(**source)
        self.journal.set_id(self.journal.makeid())
        self.journal.set_owner(self.publisher.id)
        bj = self.journal.bibjson()
        bj.title = s(DATA["update_request"]["title"])
        bj.alternative_title = DATA["update_request"]["alternative_title"]
        bj.pissn = self.generate_unique_issn()
        bj.eissn = self.generate_unique_issn()
        bj.publisher_name = DATA["publisher_name"]
        bj.set_keywords(DATA["update_request"]["keywords"])
        self.journal.save()

        # update_request

        # new draft application
        source = ApplicationFixtureFactory.make_update_request_source()
        self.ur = models.Application(**source)
        self.ur.set_id(self.draft.makeid())
        self.ur.set_current_journal(self.journal.id)
        self.ur.set_owner(self.journal.owner)
        self.ur.application_type = constants.APPLICATION_TYPE_UPDATE_REQUEST
        self.ur.date_applied = dates.now_str()
        bj = self.ur.bibjson()
        jbj = self.journal.bibjson()
        bj.title = jbj.title
        bj.alternative_title = jbj.alternative_title
        bj.pissn = jbj.pissn
        bj.eissn = jbj.eissn
        bj.publisher_name = jbj.publisher_name
        bj.set_keywords([*DATA["update_request"]["keywords"], [DATA["update_request"]["new_keyword"]]])
        self.ur.save()

        return {
            "id": self.run_seed,
            "accounts": {
                "admin": {
                    "username": self.admin.id,
                    "password": admin_password
                },
                "publisher": {
                    "username": self.publisher.id,
                    "password": publisher_password
                }
            },
            "new_application":  {
                "id": self.draft.id,
                "title": self.draft.bibjson().title,
                "url": f"{app.config.get('BASE_URL', '')}/apply/{self.draft.id}",
                "comment": DATA["draft"]["comment"],
            },
            "update_request": {
                "id": self.ur.id,
                 "title": self.ur.bibjson().title,
                 "url": f"{app.config.get('BASE_URL', '')}/publisher/update_request/{self.ur.id}",
                "comment": DATA["update_request"]["comment"],
            },
            "non_renderable": {
                "journal": self.journal.id
            }
        }

    def teardown(self, params):
        models.Account.remove_by_id(params["accounts"]["admin"]["username"])
        models.Account.remove_by_id(params["accounts"]["publisher"]["username"])
        models.Journal.remove_by_id(params["non_renderable"]["journal"])
        models.Application.remove_by_id(params["new_application"]["id"])
        models.Application.remove_by_id(params["update_request"]["id"])
        return {"status": "success"}
