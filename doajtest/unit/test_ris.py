from unittest import TestCase

from portality.lib.ris import RisEntry


class TestRisEntry(TestCase):

    def test_get_set_item__basic(self):
        test_value = 'value_a'
        entry = RisEntry()
        entry['primary_author'] = test_value
        assert entry['primary_author'] == test_value

    def test_get_set_item__alias(self):
        test_value = 'value_a'
        entry = RisEntry()
        entry['primary_author'] = test_value
        assert entry['A1'] == test_value

    def test_getitem__valid_undefined(self):
        entry = RisEntry()
        assert entry['primary_author'] is None

    def test_setitem__raise_field_not_found(self):
        entry = RisEntry()
        with self.assertRaises(ValueError):
            entry['qoidjqowijdkncoiqw'] = 'value_a'

    def test_getitem__raise_field_not_found(self):
        entry = RisEntry()
        with self.assertRaises(ValueError):
            print(entry['qoidjqowijdkncoiqw'])

    def test_to_dict(self):
        entry = RisEntry()
        entry['primary_author'] = 'value_a'
        entry['secondary_author'] = 'value_b'
        entry['tertiary_author'] = 'value_c'
        assert entry.to_dict() == {
            'A1': 'value_a',
            'A2': 'value_b',
            'A3': 'value_c'
        }

    def test_to_text(self):
        entry = RisEntry()
        entry['primary_author'] = 'value_a'
        entry['secondary_author'] = 'value_b'
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
        assert entry['TY'] == 'JOUR'
        assert dict(entry.to_dict()) == {
            'TY': 'JOUR',
            'A1': 'value_a',
            'A2': 'value_b'
        }
