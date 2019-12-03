from doajtest.helpers import DoajTestCase
from portality.store import StoreFactory
from io import StringIO, BytesIO

class SludgePump(object):
    def __init__(self, size, format="bytes"):
        self._size = size
        self._cursor = 0

    def read(self, n):
        nc = self._cursor + n
        if nc > self._size:
            nc = self._size
        total = nc - n
        if format == "bytes":
            return b"x" * total
        else:
            return "x" * total

class TestStore(DoajTestCase):

    def setUp(self):
        super(TestStore, self).setUp()

    def tearDown(self):
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