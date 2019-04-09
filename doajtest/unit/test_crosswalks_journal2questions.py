from doajtest.helpers import DoajTestCase
from portality import models

from doajtest.fixtures import JournalFixtureFactory

from portality.crosswalks.journal_questions import Journal2QuestionXwalk


class TestCrosswalksJournal2Questions(DoajTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_journal2questions(self):
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.prep()
        q_and_a = Journal2QuestionXwalk.journal2question(journal)
        answers = [unicode(x[1]) for x in q_and_a]
        expected = JournalFixtureFactory.question_answers()
        for i in range(len(answers)):
            a = answers[i]
            if a != expected[i]:
                print("{c} = {a} | {b}".format(a=a, b=expected[i], c=q_and_a[i]))

        assert answers == expected
