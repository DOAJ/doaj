class ResourceUnavailable(Exception):
    pass


class ResourceBundle(object):
    def __init__(self):
        self._resource_data = {}

    def register(self, resource_id, data):
        self._resource_data[resource_id] = data

    def get(self, resource_id):
        return self._resource_data.get(resource_id)


class Resource(object):
    __identity__ = "base_resource"

    def __init__(self, resource_bundle):
        self._resource_bundle = resource_bundle

    def name(self):
        return self.__identity__

    def make_resource_id(self, *args, **kwargs):
        return self.name()

    def reference_url(self, *args, **kwargs):
        raise NotImplementedError()

    def fetch_fresh(self, *args, **kwargs):
        raise NotImplementedError()

    def fetch(self, *args, **kwargs):
        resource_id = self.make_resource_id(*args, **kwargs)
        data = self._resource_bundle.get(resource_id)
        if data is not None:
            return data

        try:
            data = self.fetch_fresh(*args, **kwargs)
        except:
            raise ResourceUnavailable()

        self._resource_bundle.register(resource_id, data)
        return data