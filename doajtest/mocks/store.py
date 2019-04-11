from portality import store

class NoWriteStore(store.Store):

    def __init__(self, scope=None):
        pass

    def store(self, container_id, target_name, source_path=None, source_stream=None):
        raise IOError("No writes")

    def exists(self, container_id):
        return False

    def list(self, container_id):
        return None

    def get(self, container_id, target_name, encoding=None):
        return None

    def url(self, container_id, target_name):
        return None

    def delete(self, container_id, target_name=None):
        raise IOError("No writes")

    def path(self, container_id, filename, create_container=False, must_exist=True):
        raise IOError("No writes")

    def list_container_ids(self):
        return []


class StoreMockFactory(object):

    @classmethod
    def no_writes_classpath(self):
        return "doajtest.mocks.store.NoWriteStore"