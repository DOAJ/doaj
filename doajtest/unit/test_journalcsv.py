# -*- coding: UTF-8 -*-
import csv, os, codecs
from doajtest.helpers import DoajTestCase
from doajtest.fixtures import JournalFixtureFactory
from portality import models, journalcsv
from StringIO import StringIO

from portality.core import app
from portality.tasks import journal_csv

# wee function to check for differences between lists
diff = lambda l1, l2: filter(lambda x: x not in l2, l1)


class TestJournalCSV(DoajTestCase):
    def setUp(self):
        super(TestJournalCSV, self).setUp()

    def tearDown(self):
        super(TestJournalCSV, self).tearDown()
        cdir = app.config.get("CACHE_DIR")
        csvdir = os.path.join(cdir, "csv")
        csvs = [c for c in os.listdir(csvdir) if c.endswith(".csv")]
        for c in csvs:
            os.remove(os.path.join(csvdir, c))

    def test_01_single_row(self):
        """ Writing a CSV for a single-journal index """
        expected_titles = [
            'Journal title',
            'Journal URL',
            'Alternative title',
            'Journal ISSN (print version)',
            'Journal EISSN (online version)',
            'Publisher',
            'Society or institution',
            'Platform, host or aggregator',
            'Country of publisher',
            'Journal article processing charges (APCs)',
            'APC information URL',
            'APC amount',
            'Currency',
            'Journal article submission fee',
            'Submission fee URL',
            'Submission fee amount',
            'Submission fee currency',
            'Number of articles publish in the last calendar year',
            'Number of articles information URL',
            'Journal waiver policy (for developing country authors etc)',
            'Waiver policy information URL',
            'Digital archiving policy or program(s)',
            'Archiving: national library',
            'Archiving: other',
            'Archiving infomation URL',
            'Journal full-text crawl permission',
            'Permanent article identifiers',
            'Journal provides download statistics',
            'Download statistics information URL',
            'First calendar year journal provided online Open Access content',
            'Full text formats',
            'Keywords',
            'Full text language',
            'URL for the Editorial Board page',
            'Review process',
            'Review process information URL',
            "URL for journal's aims & scope",
            "URL for journal's instructions for authors",
            'Journal plagiarism screening policy',
            'Plagiarism information URL',
            'Average number of weeks between submission and publication',
            "URL for journal's Open Access statement",
            'Machine-readable CC licensing information embedded or displayed in articles',
            'URL to an example page with embedded licensing information',
            'Journal license',
            'License attributes',
            'URL for license terms',
            'Does this journal allow unrestricted reuse in compliance with BOAI?',
            'Deposit policy directory',
            'Author holds copyright without restrictions',
            'Copyright information URL',
            'Author holds publishing rights without restrictions',
            'Publishing rights information URL',
            'DOAJ Seal',
            'Tick: Accepted after March 2014',
            'Added on Date',
            'Subjects']

        csv_source_journal1 = models.Journal(**JournalFixtureFactory.make_journal_source())
        # Journal must be in_doaj to be included
        csv_source_journal1.set_in_doaj(True)
        csv_source_journal1.save(blocking=True)

        expected_journalrow = [
            'The Title',
            'http://journal.url',
            'Alternative Title',
            '1234-5678',
            '9876-5432',
            'The Publisher',
            'Society Institution',
            'Platform Host Aggregator',
            'United States',
            'Yes',
            'http://apc.com',
            '2',
            'GBP - Pound Sterling',
            'Yes',
            'http://submission.com',
            '4',
            'USD - US Dollar',
            '',
            '',
            'Yes',
            'http://waiver.policy',
            'LOCKSS, CLOCKSS',
            'Trinity',
            'A safe place',
            'http://digital.archiving.policy',
            'Yes',
            'DOI, ARK, PURL',
            'Yes',
            'http://download.stats',
            '1980',
            'HTML, XML, Wordperfect',
            'word, key',
            'English, French',
            'http://editorial.board',
            'Open peer review',
            'http://review.process',
            'http://aims.scope',
            'http://author.instructions.com',
            'Yes',
            'http://plagiarism.screening',
            '8',
            'http://oa.statement',
            'Yes',
            'http://licence.embedded',
            'CC MY',
            'Attribution, No Commercial Usage',
            'http://licence.url',
            'Yes',
            'Sherpa/Romeo, Store it',
            'True',
            'http://copyright.com',
            'True',
            'http://publishing.rights',
            'Yes',
            'Yes',
            '2000-01-01T00:00:00Z',
            'Social Sciences: Economic theory. Demography']

        # make the single-journal csv file
        csvstream = StringIO()
        journalcsv.make_journals_csv(csvstream)

        # read back the csv and check the rows are as expected.
        csvstream.seek(0)
        csvreader = csv.reader(csvstream)
        csv_rows = []
        for row in csvreader:
            csv_rows.append(row)

        assert len(csv_rows) == 2                      # 2 rows: titles and single journal
        assert csv_rows[0] == expected_titles
        assert csv_rows[1] == expected_journalrow

    def test_02_multi_row(self):
        """ Test adding two items to index and writing a CSV """
        csv_source_journal1 = models.Journal(**JournalFixtureFactory.make_journal_source())
        csv_source_journal1.set_in_doaj(True)
        csv_source_journal1.save()

        # add a second journal by editing the id and issn from source of the first
        j2_source = JournalFixtureFactory.make_journal_source()
        j2_source['id'] = 'lmnopqrstuvxyz_journal'
        j2_source['bibjson']['identifier'][0] = {"type": "pissn", "id": "8765-4321"}
        csv_source_journal2 = models.Journal(**j2_source)
        csv_source_journal2.set_in_doaj(True)
        csv_source_journal2.save(blocking=True)

        # make the multi-journal csv file
        csvstream = StringIO()
        journalcsv.make_journals_csv(csvstream)

        # read back the csv and check the rows are as expected.
        csvstream.seek(0)
        csvreader = csv.reader(csvstream)
        csv_rows = []
        for row in csvreader:
            csv_rows.append(row)

        assert len(csv_rows) == 3                     # we expect 3 rows this time
        assert csv_rows[1] != csv_rows[2]             # ID was changed, rows should differ

        # check that the difference between rows is the ISSN

        assert diff(csv_rows[2], csv_rows[1]) == ["8765-4321"]

    def test_03_overwrite_by_issn(self):
        """ Testing overwrite -  The CSV rows are unique by ISSN; the second entry with the same ISSN should replace the first """
        csv_source_journal1 = models.Journal(**JournalFixtureFactory.make_journal_source())
        csv_source_journal1.set_in_doaj(True)
        csv_source_journal1.save()

        # add a second journal by editing the id and the title from source of the first
        j2_source = JournalFixtureFactory.make_journal_source()
        j2_source['id'] = 'lmnopqrstuvxyz_journal'
        j2_source['bibjson']['title'] = 'The New Title'
        csv_source_journal2 = models.Journal(**j2_source)
        csv_source_journal2.set_in_doaj(True)
        csv_source_journal2.save(blocking=True)

        # make the multi-journal csv file
        csvstream = StringIO()
        journalcsv.make_journals_csv(csvstream)

        # read back the csv and check the rows are as expected.
        csvstream.seek(0)
        csvreader = csv.reader(csvstream)
        csv_rows = []
        for row in csvreader:
            csv_rows.append(row)

        assert len(csv_rows) == 2                     # We only expect one journal here - the second should overwrite the first
        assert csv_rows[1].pop(0) == 'The New Title'  # The title should be the second one we added

    def test_04_background_task(self):
        csv_source_journal1 = models.Journal(**JournalFixtureFactory.make_journal_source())
        csv_source_journal1.set_in_doaj(True)
        csv_source_journal1.save()

        # add a second journal by editing the id and issn from source of the first
        j2_source = JournalFixtureFactory.make_journal_source()
        j2_source['id'] = 'lmnopqrstuvxyz_journal'
        j2_source['bibjson']['identifier'][0] = {"type": "pissn", "id": "8765-4321"}
        csv_source_journal2 = models.Journal(**j2_source)
        csv_source_journal2.set_in_doaj(True)
        csv_source_journal2.save(blocking=True)

        user = app.config.get("SYSTEM_USERNAME")
        job = journal_csv.JournalCSVBackgroundTask.prepare(user)
        journal_csv.JournalCSVBackgroundTask.submit(job)

        filename = models.Cache.get_latest_csv().get("filename")
        cdir = app.config.get("CACHE_DIR")
        jcsv = os.path.join(cdir, "csv", filename)

        with codecs.open(jcsv, "r", "utf-8") as f:
            csvreader = csv.reader(f)
            csv_rows = []
            for row in csvreader:
                csv_rows.append(row)

            assert len(csv_rows) == 3                     # we expect 3 rows this time
            assert csv_rows[1] != csv_rows[2]             # ID was changed, rows should differ

            # check that the difference between rows is the ISSN
            assert diff(csv_rows[2], csv_rows[1]) == ["8765-4321"]

    def test_05_mixed_unicode(self):
        """ Writing a CSV for a mixed unicode single-journal index """
        expected_titles = [
            'Journal title',
            'Journal URL',
            'Alternative title',
            'Journal ISSN (print version)',
            'Journal EISSN (online version)',
            'Publisher',
            'Society or institution',
            'Platform, host or aggregator',
            'Country of publisher',
            'Journal article processing charges (APCs)',
            'APC information URL',
            'APC amount',
            'Currency',
            'Journal article submission fee',
            'Submission fee URL',
            'Submission fee amount',
            'Submission fee currency',
            'Number of articles publish in the last calendar year',
            'Number of articles information URL',
            'Journal waiver policy (for developing country authors etc)',
            'Waiver policy information URL',
            'Digital archiving policy or program(s)',
            'Archiving: national library',
            'Archiving: other',
            'Archiving infomation URL',
            'Journal full-text crawl permission',
            'Permanent article identifiers',
            'Journal provides download statistics',
            'Download statistics information URL',
            'First calendar year journal provided online Open Access content',
            'Full text formats',
            'Keywords',
            'Full text language',
            'URL for the Editorial Board page',
            'Review process',
            'Review process information URL',
            "URL for journal's aims & scope",
            "URL for journal's instructions for authors",
            'Journal plagiarism screening policy',
            'Plagiarism information URL',
            'Average number of weeks between submission and publication',
            "URL for journal's Open Access statement",
            'Machine-readable CC licensing information embedded or displayed in articles',
            'URL to an example page with embedded licensing information',
            'Journal license',
            'License attributes',
            'URL for license terms',
            'Does this journal allow unrestricted reuse in compliance with BOAI?',
            'Deposit policy directory',
            'Author holds copyright without restrictions',
            'Copyright information URL',
            'Author holds publishing rights without restrictions',
            'Publishing rights information URL',
            'DOAJ Seal',
            'Tick: Accepted after March 2014',
            'Added on Date',
            'Subjects']

        journal1_source = JournalFixtureFactory.make_journal_source()
        journal1_source['bibjson']['title'] = u'The Title'
        journal1_source['bibjson']['alternative_title'] = u"Заглавие на журнала"
        journal1_source['bibjson']['institution'] = u'Society Institution'
        journal1_source['bibjson']['publisher'] = u'The Publisher'
        csv_source_journal1 = models.Journal(**journal1_source)
        # Journal must be in_doaj to be included
        csv_source_journal1.set_in_doaj(True)
        csv_source_journal1.save(blocking=True)

        expected_journalrow = [
            'The Title',
            'http://journal.url',
            'Заглавие на журнала',
            '1234-5678',
            '9876-5432',
            'The Publisher',
            'Society Institution',
            'Platform Host Aggregator',
            'United States',
            'Yes',
            'http://apc.com',
            '2',
            'GBP - Pound Sterling',
            'Yes',
            'http://submission.com',
            '4',
            'USD - US Dollar',
            '',
            '',
            'Yes',
            'http://waiver.policy',
            'LOCKSS, CLOCKSS',
            'Trinity',
            'A safe place',
            'http://digital.archiving.policy',
            'Yes',
            'DOI, ARK, PURL',
            'Yes',
            'http://download.stats',
            '1980',
            'HTML, XML, Wordperfect',
            'word, key',
            'English, French',
            'http://editorial.board',
            'Open peer review',
            'http://review.process',
            'http://aims.scope',
            'http://author.instructions.com',
            'Yes',
            'http://plagiarism.screening',
            '8',
            'http://oa.statement',
            'Yes',
            'http://licence.embedded',
            'CC MY',
            'Attribution, No Commercial Usage',
            'http://licence.url',
            'Yes',
            'Sherpa/Romeo, Store it',
            'True',
            'http://copyright.com',
            'True',
            'http://publishing.rights',
            'Yes',
            'Yes',
            '2000-01-01T00:00:00Z',
            'Social Sciences: Economic theory. Demography']

        # make the single-journal csv file
        csvstream = StringIO()
        journalcsv.make_journals_csv(csvstream)

        def utf_8_encoder(unicode_csv_data):
            for line in unicode_csv_data:
                yield line.encode('utf-8')

        # read back the csv and check the rows are as expected.
        csvstream.seek(0)
        csvreader = csv.reader(utf_8_encoder(csvstream))
        csv_rows = []
        for row in csvreader:
            csv_rows.append(row)

        assert len(csv_rows) == 2                      # 2 rows: titles and single journal
        assert csv_rows[0] == expected_titles
        assert csv_rows[1] == expected_journalrow
