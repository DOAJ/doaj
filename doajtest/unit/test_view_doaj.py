import time

from doajtest.fixtures.editor_groups import create_editor_group_en, create_editor_group_cn, create_editor_group_jp
from doajtest.helpers import DoajTestCase
from portality import models
from portality.view.doaj import id_text_mapping


class TestViewDoaj(DoajTestCase):

    def test_autocomplete_pair(self):
        eg = create_editor_group_en()
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

    def test_autocomplete_text(self):
        eg = create_editor_group_en()
        eg.save(blocking=True)
        with self.app_test.test_client() as client:
            doc_type = 'editor_group'
            field_name = 'name'
            id_field = 'id'
            response = client.get(f'/autocomplete-text/{doc_type}/{field_name}/{id_field}?id={eg.id}', )

            assert response.status_code == 200
            assert response.json == {eg.id: eg.name}

    def test_autocomplete_text__not_found(self):
        eg = create_editor_group_en()
        eg.save(blocking=True)
        with self.app_test.test_client() as client:
            doc_type = 'editor_group'
            field_name = 'name'
            id_field = 'id'
            id_val = 'qwjeqkwjeq'
            response = client.get(f'/autocomplete-text/{doc_type}/{field_name}/{id_field}?id={id_val}', )

            assert response.status_code == 200
            assert response.json == {}

    def test_autocomplete_text__ids(self):
        eg = create_editor_group_en()
        eg2 = create_editor_group_cn()
        eg3 = create_editor_group_jp()

        models.EditorGroup.save_all_block_last([eg, eg2, eg3])

        with self.app_test.test_client() as client:
            doc_type = 'editor_group'
            field_name = 'name'
            id_field = 'id'
            response = client.get(f'/autocomplete-text/{doc_type}/{field_name}/{id_field}',
                                  json={'ids': [eg.id, eg2.id]})

            assert response.status_code == 200
            assert response.json == {eg.id: eg.name, eg2.id: eg2.name, }

    def test_autocomplete_text__ids_empty(self):
        with self.app_test.test_client() as client:
            doc_type = 'editor_group'
            field_name = 'name'
            id_field = 'id'
            response = client.get(f'/autocomplete-text/{doc_type}/{field_name}/{id_field}',
                                  json={'ids': []})

            assert response.status_code == 200
            assert response.json == {}

    def test_id_text_mapping(self):
        models.EditorGroup.save_all_block_last([create_editor_group_en(), create_editor_group_cn(),
                                                create_editor_group_jp()])

        time.sleep(5)
        assert id_text_mapping('editor_group', 'name', 'id', 'egid') == {'egid': 'English'}
        assert id_text_mapping('editor_group', 'name', 'id', 'egid2') == {'egid2': 'Chinese'}
