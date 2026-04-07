from doajtest import helpers
from doajtest.helpers import DoajTestCase
from portality.store import StoreFactory
from io import StringIO, BytesIO
from doajtest.fixtures.store import SludgePump

class TestStore(DoajTestCase):

    def setUp(self):
        super(TestStore, self).setUp()

        self.store_local_patcher = helpers.StoreLocalPatcher()
        self.store_local_patcher.setUp(self.app_test)

    def tearDown(self):
        self.store_local_patcher.tearDown(self.app_test)

        super(TestStore, self).tearDown()


    def test_01_local(self):
        local = StoreFactory.get(None)

        stringin = StringIO("test")
        local.store("string", "string.txt", source_stream=stringin)

        stringout_bin = local.get("string", "string.txt")
        assert stringout_bin.read().decode("utf-8") == "test"

        stringout_utf8 = local.get("string", "string.txt", encoding="utf-8")
        assert stringout_utf8.read() == "test"

        bytesin = BytesIO(b"here are some bytes")
        local.store("bytes", "bytes.bin", source_stream=bytesin)

        bytesout_bin = local.get("bytes", "bytes.bin")
        assert bytesout_bin.read() == b"here are some bytes"

    def test_02_local_large(self):
        local = StoreFactory.get(None)

        local.store("sludge", "sludge.txt", source_stream=SludgePump(100000000, format="text"))
        local.store("sludge", "sludge.bin", source_stream=SludgePump(90000000, format="bytes"))

        assert local.size("sludge", "sludge.txt") == 100000000
        assert local.size("sludge", "sludge.bin") == 90000000