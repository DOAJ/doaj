import importlib

from doajtest.helpers import DoajTestCase

# module name starts with a digit, so it can't be imported with a plain import statement
operations = importlib.import_module("portality.migrate.2959_multiple_affiliations.operations")


class TestMigrate2959MultipleAffiliations(DoajTestCase):

    def test_01_old_format_duplicates_merged(self):
        authors = [
            {"name": "Ana", "affiliation": "Uni A", "orcid_id": "https://orcid.org/0000-0001-1234-1234"},
            {"name": "Ben", "affiliation": "Uni C"},
            {"name": "Ana", "affiliation": "Uni B"},
            {"name": "Ana", "affiliation": "Uni A"},
            {"name": "Cat", "affiliation": ""},
        ]
        merged, old_format, dupes = operations._transform_authors(authors)
        assert old_format is True
        assert dupes is True
        assert merged == [
            {"name": "Ana", "affiliations": ["Uni A", "Uni B"], "orcid_id": "https://orcid.org/0000-0001-1234-1234"},
            {"name": "Ben", "affiliations": ["Uni C"]},
            {"name": "Cat"},
        ]

    def test_02_orcid_taken_from_later_duplicate(self):
        authors = [{"name": "Ana", "affiliation": "Uni A"},
                   {"name": "Ana", "affiliation": "Uni B", "orcid_id": "https://orcid.org/0000-0001-1234-1234"}]
        merged, _, _ = operations._transform_authors(authors)
        assert merged == [{"name": "Ana", "affiliations": ["Uni A", "Uni B"],
                           "orcid_id": "https://orcid.org/0000-0001-1234-1234"}]

    def test_03_new_format_untouched(self):
        authors = [{"name": "Ana", "affiliations": ["Uni A", "Uni B"]}, {"name": "Ben"}]
        merged, old_format, dupes = operations._transform_authors([dict(a) for a in authors])
        assert (old_format, dupes) == (False, False)
        assert merged == authors

    def test_04_migrate_returns_article(self):
        source = {"id": "abc", "bibjson": {"title": "T", "author": [
            {"name": "Ana", "affiliation": "Uni A"}, {"name": "Ana", "affiliation": "Uni B"}]}}
        article = operations.migrate_affiliations(source)
        assert article.bibjson().author == [{"name": "Ana", "affiliations": ["Uni A", "Uni B"]}]
