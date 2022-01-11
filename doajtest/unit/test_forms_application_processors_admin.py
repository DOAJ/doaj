from doajtest.helpers import DoajTestCase


class TestPublicApplicationProcessor(DoajTestCase):

    def setUp(self):
        super(TestPublicApplicationProcessor, self).setUp()

    def tearDown(self):
        super(TestPublicApplicationProcessor, self).tearDown()

    def test_01_do_not_accept_nonexistant(self):
        pass

    def test_02_do_not_accept_withdrawn(self):
        pass

    def test_03_do_not_accept_deleted(self):
        pass

    def test_03_do_not_edit_accepted(self):
        pass