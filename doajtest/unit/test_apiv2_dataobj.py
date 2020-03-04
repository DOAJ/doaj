from doajtest.helpers import DoajTestCase
from portality.lib import dataobj
from portality.api.v2.data_objects.journal import OutgoingJournal
from portality import models
from doajtest.fixtures.v2.journals import JournalFixtureFactory

class TestAPIDataObj(DoajTestCase):

    # we aren't going to talk to ES so override setup and teardown of index
    def setUp(self):
        self.jm = models.Journal(**JournalFixtureFactory.make_journal_source())

    def tearDown(self):
        pass

    def test_01_create_empty(self):
        """Create an empty dataobject, mostly to check it doesn't die a recursive death"""
        do = dataobj.DataObj()
        assert do.data == {}
        assert do._struct is None
        with self.assertRaises(AttributeError):
            do.nonexistent_attribute

    def test_02_create_from_model(self):
        expected_struct = JournalFixtureFactory.make_journal_apido_struct()
        do = OutgoingJournal.from_model(self.jm)
        assert do._struct == expected_struct, "do._struct:\n {}, \n expected_struct:\n {}".format(do._struct, expected_struct)
        self.check_do(do, expected_struct)

    def check_do(self, do, expected_struct):
        assert isinstance(do.admin, dataobj.DataObj), 'Declared as "object" but not a Data Object?'
        assert do.id == self.jm.id
        assert do.created_date == self.jm.created_date
        assert do.last_updated == self.jm.last_updated

        assert do.admin.in_doaj is self.jm.is_in_doaj(), 'actual val {0} is of type {1}'.format(do.admin.in_doaj, type(do.admin.in_doaj))
        assert do.admin.ticked is self.jm.is_ticked()  # it's not set in the journal fixture so we expect a None back
        assert do.admin.seal is self.jm.has_seal()
        assert do.admin.owner == self.jm.owner

        assert isinstance(do.bibjson, dataobj.DataObj), 'Declared as "object" but not a Data Object?'
        assert do.bibjson.title == self.jm.bibjson().title
        assert do.bibjson.alternative_title == self.jm.bibjson().alternative_title
        assert do.bibjson.publisher.name == self.jm.bibjson().publisher, "do.bibjson.publisher:\n{},\nself.jm.bibjson().publisher:\n{}".format(do.bibjson.publisher, self.jm.bibjson().publisher)
        assert do.bibjson.institution.name == self.jm.bibjson().institution
        assert do.bibjson.apc == self.jm.bibjson().apc
        assert do.bibjson.other_charges == self.jm.bibjson().other_charges
        assert do.bibjson.publication_time_weeks == self.jm.bibjson().publication_time_weeks

        for o in expected_struct['structs']['bibjson']['objects']:
            assert isinstance(getattr(do.bibjson, o), dataobj.DataObj), '{0} declared as "object" but not a Data Object?'.format(o)

        for l in expected_struct['structs']['bibjson']['lists']:
            assert isinstance(getattr(do.bibjson, l), list), '{0} declared as "list" but not a list?'.format(l)

        assert do.bibjson.apc.max[0].currency == self.jm.bibjson().apc.max[0]['currency']
        assert do.bibjson.apc.max[0].price == self.jm.bibjson().apc.max[0]['price']

        assert do.bibjson.preservation.url == self.jm.bibjson().preservation_url
        assert isinstance(do.bibjson.preservation_services, list)
        # TODO the below line passes but journal struct needs enhancing here
        # assert do.bibjson.archiving_policy.policy == [u"['LOCKSS', 'CLOCKSS', ['A national library', 'Trinity'], ['Other', 'A safe place']]", u"['LOCKSS', 'CLOCKSS', ['A national library', 'Trinity'], ['Other', 'A safe place']]", u"['LOCKSS', 'CLOCKSS', ['A national library', 'Trinity'], ['Other', 'A safe place']]", u"['LOCKSS', 'CLOCKSS', ['A national library', 'Trinity'], ['Other', 'A safe place']]"], do.bibjson.archiving_policy.policy

    def test_03_merge_outside_construct(self):
        struct = {
            "fields" : {
                "one" : {"coerce" : "unicode"}
            },
            "lists" : {
                "two" : {"contains" : "field", "coerce" : "unicode"}
            },
            "objects" : ["three"],

            "structs" : {
                "three" : {
                    "fields" : {
                        "alpha" : {"coerce" : "unicode"}
                    },
                    "lists" : {
                        "beta" : {"contains" : "field", "coerce" : "unicode"}
                    },
                    "objects" : ["gamma"]
                }
            }
        }

        target = {
            "one" : "first",
            "two" : ["second1", "second2"],
            "three" : {
                "alpha" : "a",
                "beta" : ["b1", "b2"],
                "gamma" : {"letter" : "c"}
            }
        }

        source = {
            "one" : "not first",
            "two" : ["not second1", "not second2"],
            "three" : {
                "alpha" : "not a",
                "beta" : ["not b1", "not b2"],
                "gamma" : {"letter" : "not c"},
                "delta" : "d",
                "epsilon" : ["e1", "e2"],
                "zeta" : {"another" : "object"}
            },
            "four" : "fourth",
            "five" : ["fifth1", "fifth2"],
            "six" : {"an" : "object"}
        }

        merged = dataobj.merge_outside_construct(struct, target, source)

        do = dataobj.DataObj(raw=merged, expose_data=True)
        assert do.one == "first"
        assert do.two == ["second1", "second2"]
        assert do.three.alpha == "a"
        assert do.three.beta == ["b1", "b2"]
        assert do.three.gamma.letter == "c"
        assert do.three.delta == "d"
        assert do.three.epsilon == ["e1", "e2"]
        assert do.three.zeta.another == "object"
        assert do.four == "fourth"
        assert do.five == ["fifth1", "fifth2"]
        assert do.six.an == "object"
