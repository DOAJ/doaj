class SludgePump(object):
    def __init__(self, size, format="bytes"):
        self._size = size
        self._cursor = 0

    def read(self, n):
        nc = self._cursor + n
        if nc > self._size:
            nc = self._size
        total = nc - self._cursor
        self._cursor = nc
        if format == "bytes":
            if total > 0:
                return b"x" * total
            return b""
        else:
            if total > 0:
                return "x" * total
            return ""