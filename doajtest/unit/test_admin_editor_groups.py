import time
from doajtest.helpers import DoajTestCase, login
from portality.models import Account, EditorGroup
from doajtest.fixtures import AccountFixtureFactory


class TestAdminEditorGroups(DoajTestCase):

    def setUp(self):
        super(TestAdminEditorGroups, self).setUp()
        admin_account = Account.make_account(email="admin@test.com", username="admin", name="Admin", roles=["admin"])
        admin_account.set_password('password123')
        admin_account.save()

        asource = AccountFixtureFactory.make_editor_source()
        self.editor = Account(**asource)
        self.editor.save()

    def test_editor_group_creation_and_update(self):
        with self.app_test.test_client() as t_client:
            # Test creating an EditorGroup

            login(t_client, "admin", "password123")
            data = {"name": "Test Group", "editor": "eddie"}
            response = t_client.post('/admin/editor_group', data=data)
            assert response.status_code == 302

            # give some time for the new record to be indexed
            time.sleep(1)
            editor_group_id = EditorGroup.group_exists_by_name("Test Group")
            self.assertIsNotNone(editor_group_id)

            # Test EditorGroup name is not editable (silent failure if supplied)
            data = {"name": "New Test Group", "editor": "eddie"}
            response = t_client.post('/admin/editor_group/' + editor_group_id, data=data)
            assert response.status_code == 302

            # give some time for the new record to be indexed
            time.sleep(1)
            updated_group = EditorGroup.pull(editor_group_id)
            self.assertEquals(updated_group.name, "New Test Group")
            self.assertNotEquals(updated_group.name, "Test Group")
