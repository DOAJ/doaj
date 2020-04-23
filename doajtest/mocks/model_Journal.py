from doajtest.fixtures import JournalFixtureFactory
from portality.models import Journal

class ModelJournalMockFactory(object):

    @classmethod
    def find_by_issn(cls, issns, owners):
        journals = []
        seen_issns = []

        for owner in owners:
            for eissn, pissn in issns:
                if eissn not in seen_issns and eissn is not None:
                    seen_issns.append(eissn)
                if pissn not in seen_issns and pissn is not None:
                    seen_issns.append(pissn)

                source = JournalFixtureFactory.make_journal_source(in_doaj=True)
                journal = Journal(**source)
                journal.set_owner(owner)

                jbj = journal.bibjson()
                del jbj.eissn
                del jbj.pissn
                if eissn is not None:
                    journal.bibjson().add_identifier("eissn", eissn)
                if pissn is not None:
                    journal.bibjson().add_identifier("pissn", pissn)
                journals.append(journal)

        @classmethod
        def mock(cls, issns, in_doaj=None, max=10):
            if not isinstance(issns, list):
                issns = [issns]

            for issn in issns:
                if issn in seen_issns:
                    return journals

            return []

        return mock
