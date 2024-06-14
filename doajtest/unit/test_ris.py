from unittest import TestCase

from portality.lib.ris import RisEntry


class TestRisEntry(TestCase):

    def test_get_set_item(self):
        test_value = 'value_a'
        entry = RisEntry()
        entry['A1'] = test_value
        assert entry['A1'] == [test_value]

    def test_append(self):
        entry = RisEntry()
        entry.append('A1', '1')
        entry['A1'].append('2')
        assert entry['A1'] == ['1', '2']

        entry['A1'] = '9'
        assert entry['A1'] == ['9']

    def test_getitem__valid_undefined(self):
        entry = RisEntry()
        assert entry['A1'] == []

    def test_setitem__raise_field_not_found(self):
        entry = RisEntry()
        with self.assertRaises(ValueError):
            entry['qoidjqowijdkncoiqw'] = 'value_a'

    def test_getitem__raise_field_not_found(self):
        entry = RisEntry()
        with self.assertRaises(ValueError):
            print(entry['qoidjqowijdkncoiqw'])

    def test_to_text(self):
        entry = RisEntry()
        entry['A1'] = 'value_a'
        entry['A2'] = 'value_b'
        entry['TY'] = 'JOUR'

        expected = """
TY  - JOUR
A1  - value_a
A2  - value_b
ER  -
        """.strip() + ' \n'

        assert entry.to_text() == expected

    def test_from_text(self):
        expected = """
        TY  - JOUR
        A1  - value_a
        A2  - value_b
        ER  -
                """.strip() + ' \n'

        entry = RisEntry.from_text(expected)
        assert entry.type == 'JOUR'
        assert dict(entry.data) == {
            'TY': ['JOUR'],
            'A1': ['value_a'],
            'A2': ['value_b'],
        }
