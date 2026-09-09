import gzip
import json
import tempfile
from pathlib import Path

from doajtest.fixtures.accounts import AccountFixtureFactory
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.helpers import DoajTestCase, StoreLocalPatcher
from doajtest.unit_tester import bgtask_tester
from portality.models import BackgroundJob, Account, Note
from portality.store import StoreLocal
from portality.tasks import anon_export
from portality.tasks.anon_export import AnonExportBackgroundTask
from portality.tasks.helpers import background_helper


class TestAnonExport(DoajTestCase):

    def setUp(self):
        super().setUp()
        self.store_local_patcher = StoreLocalPatcher()
        self.store_local_patcher.setUp(self.app_test)

    def tearDown(self):
        super().tearDown()
        self.store_local_patcher.tearDown(self.app_test)

    def test_execute(self):

        # prepare test data
        BackgroundJob.destroy_index()
        Account.destroy_index()
        BackgroundJob.save_all((BackgroundJob() for _ in range(3)), blocking=True)
        Account.save_all((Account() for _ in range(2)), blocking=True)
        BackgroundJob.refresh()
        Account.refresh()

        new_background_jobs = list(BackgroundJob.scroll())
        new_accounts = list(Account.scroll())

        # run execute
        background_task = background_helper.execute_by_bg_task_type(AnonExportBackgroundTask)

        # assert audit messages
        self.assertIn('audit', background_task.background_job.data)
        msgs = {l.get('message') for l in background_task.background_job.data['audit']}
        self.assertTrue(any('Compressing temporary file' in m for m in msgs))
        self.assertTrue(any('account.bulk.1' in m for m in msgs))

        main_store = StoreLocal(None)
        container_id = self.app_test.config.get("STORE_ANON_DATA_CONTAINER")
        target_names = main_store.list(container_id)

        # must have some file in main store
        self.assertGreater(len(target_names), 0)

        for target_name in target_names:

            # load data from store
            _target_path = Path(main_store.get(container_id, target_name).name)
            data_str = gzip.decompress(_target_path.read_bytes()).decode(errors='ignore')
            if data_str:
                rows = data_str.strip().split('\n')

                # Filter out the index: directives, leaving the actual record data
                json_rows = (json.loads(j) for j in rows)
                json_rows = filter(lambda j: len(j.keys()) > 1, json_rows)
                # drop additional background job record for AnonExportBackgroundTask execute
                json_rows = (j for j in json_rows if (
                        j.get('action') != 'anon_export' and
                        j.get('status') != 'processing'
                ))
                json_rows = list(json_rows)

                if target_name.startswith('background_job'):
                    test_data_list = new_background_jobs
                elif target_name.startswith('account'):
                    test_data_list = new_accounts
                else:
                    print(f'unexpected data dump for target_name[{target_name}]')
                    continue

                print(f'number of rows have been saved to store: [{target_name}] {len(json_rows)}')
                self.assertEqual(len(json_rows), len(test_data_list))
                self.assertIn(test_data_list[0].id, [j['id'] for j in json_rows])
            else:
                print(f'empty archive {target_name}')

    def test_prepare__queue_id(self):
        bgtask_tester.test_queue_id_assigned(AnonExportBackgroundTask)


class TestAnonymisationTransforms(DoajTestCase):
    """ Regression tests for the individual transform functions used by anon_export.

    These cover bugs found after the notes-separation migration:

    1. `anonymise_note` used to operate on the raw dict yielded by the dump iterator as if it
       were already a `Note` instance, which raised `AttributeError` on every note record.
    2. `anonymise_application`/`anonymise_journal` only caught the legacy `DataStructureException`,
       not the `SeamlessException` that `JournalLikeObject` actually raises when
       `SEAMLESS_JOURNAL_LIKE_OTHER_FIELDS` is False and a record carries a field outside the
       current struct (e.g. a leftover pre-migration `admin.notes`) - so such records crashed the
       whole export instead of being handled.
    3. Any record that can't be safely anonymised must be dropped from the export (return None),
       not returned raw/unmodified - an "anon" export that can silently contain un-anonymised
       records (real note text, real names) isn't anonymous.
    """

    def test_anonymise_note(self):
        note = Note(id="n1", note="secret note text", author_id="real_author",
                    resource_type="application", resource_id="app1")
        raw = note.data

        result = anon_export.anonymise_note(raw)

        self.assertEqual(result["note"], "---note removed for data security---")
        self.assertNotEqual(result["author_id"], "real_author")
        self.assertEqual(result["id"], "n1")

    def test_anonymise_note_with_disallowed_field_is_dropped(self):
        raw = {"id": "n2", "note": "secret note text", "author_id": "real_author",
               "not_a_real_field": "leftover from an old schema"}

        # must not raise, and must not return the un-anonymised record - drop it instead
        result = anon_export.anonymise_note(raw)

        self.assertIsNone(result)

    def test_anonymise_application_with_legacy_notes_field_is_dropped(self):
        source = ApplicationFixtureFactory.make_application_source()
        source["admin"]["notes"] = [{"id": "x", "note": "secret note text", "author_id": "real_author"}]

        # must not raise, and must not return the un-anonymised record - drop it instead
        result = anon_export.anonymise_application(source)

        self.assertIsNone(result)

    def test_anonymise_journal_with_legacy_notes_field_is_dropped(self):
        source = JournalFixtureFactory.make_journal_source()
        source["admin"]["notes"] = [{"id": "x", "note": "secret note text", "author_id": "real_author"}]

        # must not raise, and must not return the un-anonymised record - drop it instead
        result = anon_export.anonymise_journal(source)

        self.assertIsNone(result)

    def test_anonymise_account_name(self):
        source = AccountFixtureFactory.make_publisher_source()
        source["id"] = "steve"
        source["name"] = "Steve Real Name"

        result = anon_export.anonymise_account(source)

        # id/username is left alone, but the real name must not survive the export
        self.assertEqual(result["id"], "steve")
        self.assertNotEqual(result["name"], "Steve Real Name")
        self.assertNotEqual(result["email"], source["email"])


class TestDumpDropsUnanonymisableRecords(DoajTestCase):
    """ dao.DomainObject.dump() is only ever used by anon_export - confirm it actually drops
    records for which the transform returns None, rather than writing them out regardless. """

    def test_dump_skips_records_the_transform_drops(self):
        BackgroundJob.destroy_index()
        BackgroundJob.save_all(
            [BackgroundJob(id="job0"), BackgroundJob(id="job1"), BackgroundJob(id="job2")], blocking=True)
        BackgroundJob.refresh()

        def transform(record):
            return None if record.get("id") == "job1" else record

        with tempfile.TemporaryDirectory() as d:
            out_template = str(Path(d) / "bgjob.bulk")
            filenames = BackgroundJob.dump(transform=transform, out_template=out_template,
                                           es_bulk_fields=["_id"])

            ids_seen = []
            for fn in filenames:
                with open(fn) as f:
                    lines = [json.loads(l) for l in f if l.strip()]
                # bulk format alternates an index directive line with a document line
                for doc in lines[1::2]:
                    ids_seen.append(doc.get("id"))

        self.assertEqual(sorted(ids_seen), ["job0", "job2"])
