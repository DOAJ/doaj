from doajtest.fixtures import JournalFixtureFactory
from portality.models import Journal, Account
from portality import constants

class ApplicationValidateCSVFixtureFactory(object):
    @classmethod
    def create_test_artefacts(cls, username, password):

        def make_journal(title, pissn, eissn, owner=None, in_doaj=True):
            source = JournalFixtureFactory.make_journal_source(in_doaj=in_doaj)
            journal = Journal(**source)
            journal.set_id(journal.makeid())
            journal.set_owner(owner)
            bj = journal.bibjson()
            bj.title = title
            bj.pissn = pissn
            bj.eissn = eissn
            return journal

        acc = Account.make_account(username + "@example.com", username, "Publisher " + username,
                                          [constants.ROLE_PUBLISHER, constants.ROLE_PUBLISHER_JOURNAL_CSV])
        acc.set_password(password)

        valid1 = make_journal("Electronics Letters", "0000-0001", "0000-0002", owner=acc.id)
        valid2 = make_journal("Journal of Veterinary Internal Medicine", "0000-0003", "0000-0004", owner=acc.id)

        # note that we don't make 0000-0005, as this journal will come back as not found

        # Not the owner
        not_owner = make_journal("Not Owner", "0000-0007", "0000-0008", owner="someone_else")

        # No updates
        no_updates = make_journal("No Updates", "0000-0009", "0000-0010", owner=acc.id)

        # Changed the title
        changed_title = make_journal("Original Title", "0000-0011", "0000-0012", owner=acc.id)

        # Withdrawn Journal
        withdrawn = make_journal("Withdrawn Journal", "0000-0013", "0000-0014", owner=acc.id, in_doaj=False)

        # validation failure
        validation_fail = make_journal("Validation Failure", "0000-0015", "0000-0016", owner=acc.id)

        # invalid data failure
        invalid_fail = make_journal("Malformed Field", "0000-0017", "0000-0018", owner=acc.id)

        return {
            "account": acc,
            "journals": {
                "valid1": valid1,
                "valid2": valid2,
                "not_owner": not_owner,
                "no_updates": no_updates,
                "changed_title": changed_title,
                "withdrawn": withdrawn,
                "validation_fail": validation_fail,
                "invalid_fail": invalid_fail
            }
        }