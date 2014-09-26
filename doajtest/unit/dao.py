from portality import dao
from doajtest.helpers import DoajTestCase

class TestWorkflow(DoajTestCase):

    def test_generic_csv(self):
        data = {'col1': 2, 'col2': 'string', 'keywords': ['hoppity', 'hop', 'hop 2']}
        o = dao.DomainObject(**data)
        # expect alphabetic order of keys
        expected = ['2', 'string', 'hoppity,hop,hop 2']
        result = o.csv()
        assert result == expected  # You can compare lists: [1,2,3] != [1,3,2] but [1,2,3] == [1,2,3]
