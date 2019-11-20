from doajtest.helpers import DoajTestCase
from doajtest.fixtures.accounts import AccountFixtureFactory
from portality import models
from portality.lib import paths
from portality.scripts.accounts_with_marketing_consent import publishers_with_consent
import os, shutil, csv

class TestScriptsAccountsWithMarketingConsent(DoajTestCase):

    def setUp(self):
        super(TestScriptsAccountsWithMarketingConsent, self).setUp()
        self.tmp_dir = paths.rel2abs(__file__, "tmp_data")
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
        os.mkdir(self.tmp_dir)

    def tearDown(self):
        super(TestScriptsAccountsWithMarketingConsent, self).tearDown()
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_01_publishers_with_consent(self):
        # output file to save csv
        output_file = os.path.join(self.tmp_dir, 'accounts.csv')
        # Create accounts with marketing consent not set
        for i in range(20):
            pubsource = AccountFixtureFactory.make_publisher_source()
            pubaccount = models.Account(**pubsource)
            pubaccount.set_id()
            pubaccount.save()
        # Create accounts with marketing consent set to False
        for i in range(20):
            pubsource = AccountFixtureFactory.make_publisher_source()
            pubaccount = models.Account(**pubsource)
            pubaccount.set_id()
            pubaccount.set_marketing_consent(False)
            pubaccount.save()
        # Create accounts with marketing consent set to True
        expected_data = [[
          'ID',
          'Name',
          'Email',
          'Created',
          'Last Updated',
          'Updated Since Create?'
        ]]
        for i in range(20):
            pubsource = AccountFixtureFactory.make_publisher_source()
            pubaccount = models.Account(**pubsource)
            pubaccount.set_id()
            pubaccount.set_marketing_consent(True)
            if i == 19:
                pubaccount.save(blocking=True)
            else:
                pubaccount.save()
            expected_data.append([
              str(pubaccount.id),
              str(pubaccount.name),
              str(pubaccount.email),
              str(pubaccount.created_date),
              str(pubaccount.last_updated),
              str('False')
            ])

        publishers_with_consent(output_file)

        assert os.path.exists(output_file)

        table = []
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                table.append(row)
        assert len(table) == 21
        self.assertCountEqual(table, expected_data)
