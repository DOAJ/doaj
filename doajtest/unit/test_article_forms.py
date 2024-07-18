from doajtest.fixtures import AccountFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase, save_all_block_last
from portality import models
from portality.forms import article_forms


class TestArticleFormsFunction(DoajTestCase):
    def test_choices_for_article_issns(self):
        account = models.Account(**(AccountFixtureFactory.make_managing_editor_source()))

        journals = [models.Journal(**j) for j in JournalFixtureFactory.make_many_journal_sources()]
        for j in journals:
            j.set_owner(account.id)
            j.set_in_doaj(True)
        save_all_block_last(journals)

        pissns = article_forms.choices_for_article_issns(account, issn_type='pissn')
        eissns = article_forms.choices_for_article_issns(account, issn_type='eissn')
        issns = article_forms.choices_for_article_issns(account, issn_type='all')

        assert pissns != eissns
        assert len(issns)
        assert set(pissns) | set(eissns) == set(issns)
