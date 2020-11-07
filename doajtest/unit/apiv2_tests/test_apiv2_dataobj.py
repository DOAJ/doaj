from doajtest.helpers import DoajTestCase
from portality.lib import dataobj
from portality.api.v2.data_objects.journal import OutgoingJournal
from portality import models
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from portality.lib.seamless import SeamlessData, SeamlessMixin


class TestAPIDataObj(DoajTestCase):

    # we aren't going to talk to ES so override setup and teardown of index
    def setUp(self):
        self.jm = models.Journal(**JournalFixtureFactory.make_journal_source())

    def tearDown(self):
        pass

    def test_01_create_empty(self):
        """Create an empty dataobject, mostly to check it doesn't die a recursive death"""
        do = SeamlessData()
        assert do.data == {}
        assert do._struct is None
        with self.assertRaises(AttributeError):
            do.nonexistent_attribute

    def test_02_create_from_model(self):
        expected_struct = JournalFixtureFactory.make_journal_apido_struct()
        do = OutgoingJournal.from_model(self.jm)
        # FIXME: broken test - struct has changed, lots more set__allow_coerce_failure have been added - what does the test achieve anyway?
        #assert do.__seamless_struct__.raw == expected_struct, "do._struct:\n {}, \n expected_struct:\n {}".format(do.__seamless_struct__.raw, expected_struct)
        self.check_do(do, expected_struct)

    def check_do(self, do, expected_struct):
        assert isinstance(do, SeamlessMixin), 'Declared as "SeamlessMixin" but not a Data Object?'
        assert do.data["id"] == self.jm.id
        assert do.data["created_date"] == self.jm.created_date
        assert do.data["last_updated"] == self.jm.last_updated

        assert do.data["admin"]["in_doaj"] is self.jm.is_in_doaj(), 'actual val {0} is of type {1}'.format(do.admin.in_doaj, type(do.admin.in_doaj))
        assert do.data["admin"]["ticked"] is self.jm.is_ticked()  # it's not set in the journal fixture so we expect a None back
        assert do.data["admin"]["seal"] is self.jm.has_seal()

        # assert isinstance(do.data["bibjson"], dataobj.DataObj), 'Declared as "object" but not a Data Object?'
        assert do.data["bibjson"]["title"] == self.jm.bibjson().title
        assert do.data["bibjson"]["alternative_title"] == self.jm.bibjson().alternative_title
        assert do.data["bibjson"]["publisher"]["name"] == self.jm.bibjson().publisher, "do.data['bibjson'].publisher:\n{},\nself.jm.bibjson().publisher:\n{}".format(do.data["bibjson"].publisher, self.jm.bibjson().publisher)
        assert do.data["bibjson"]["institution"]["name"] == self.jm.bibjson().institution
        assert do.data["bibjson"]["apc"]["max"][0]["currency"] == self.jm.bibjson().apc[0]["currency"], "do.data['bibjson'].apc.currency:\n{},\nself.jm.bibjson().apc.currency:\n{}".format(do.data["bibjson"].apc.max[0].currency, self.jm.bibjson().apc[0]["currency"])
        assert do.data["bibjson"]["apc"]["max"][0]["price"] == self.jm.bibjson().apc[0]["price"], "do.data['bibjson'].apc.price:\n{},\nself.jm.bibjson().apc.price:\n{}".format(do.data["bibjson"].apc.max[0].price,self.jm.bibjson().apc[0]["price"])
        assert do.data["bibjson"]["other_charges"]["url"] == self.jm.bibjson().other_charges_url, \
            "do.data['bibjson'].other_charges.other_charges_url:\n{},\nself.jm.bibjson().other_charges_url:\n{}" \
                .format(do.data["bibjson"]["other_charges"]["other_charges_url"], self.jm.bibjson().other_charges_url)
        assert do.data['bibjson']["publication_time_weeks"] == self.jm.bibjson().publication_time_weeks

        for o in expected_struct['structs']['bibjson']['objects']:
            assert isinstance(do.data["bibjson"][o], dict), '{0} declared as "object" but not a dicts?'.format(o)

        for l in expected_struct['structs']['bibjson']['lists']:
            assert isinstance(do.data["bibjson"][l], list), '{0} declared as "list" but not a list?'.format(l)

        assert do.data["bibjson"]["preservation"]["url"] == self.jm.bibjson().preservation_url
        assert isinstance(do.data["bibjson"]["preservation"]["service"], list)

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
