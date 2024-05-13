from doajtest.helpers import DoajTestCase
from portality import models


class TestViewDoaj(DoajTestCase):
    def test_autocomplete_pair(self):
        eg = models.EditorGroup()
        eg.set_name("English")
        eg.set_id('egid')
        eg.save(blocking=True)

        with self.app_test.test_client() as client:
            doc_type = 'editor_group'
            field_name = 'name'
            id_field = 'id'
            query = 'eng'
            response = client.get(f'/autocomplete/{doc_type}/{field_name}/{id_field}?q={query}', )
            resp_json = response.json
            assert response.status_code == 200
            assert len(resp_json['suggestions']) == 1
            assert resp_json['suggestions'][0]['id'] == eg.id
            assert resp_json['suggestions'][0]['text'] == eg.name

    def test_autocomplete_pair__not_found(self):
        with self.app_test.test_client() as client:
            doc_type = 'editor_group'
            field_name = 'name'
            id_field = 'id'
            query = 'alksjdlaksjdalksdjl'
            response = client.get(f'/autocomplete/{doc_type}/{field_name}/{id_field}?q={query}', )
            resp_json = response.json
            assert response.status_code == 200
            assert len(resp_json['suggestions']) == 0

    def test_autocomplete_pair__unknown_doc_type(self):
        with self.app_test.test_client() as client:
            doc_type = 'alskdjalskdjal'
            field_name = 'name'
            id_field = 'id'
            query = 'eng'
            response = client.get(f'/autocomplete/{doc_type}/{field_name}/{id_field}?q={query}', )
            resp_json = response.json
            assert response.status_code == 200
            assert len(resp_json['suggestions']) == 1
            assert resp_json['suggestions'][0]['id'] == ''


