class ResourceUnavailable(Exception):
    pass


class ResourceBundle(object):
    def __init__(self, resources=None, stack_size=100):
        self._resources = resources if resources is not None else []
        self._resource_data = {}
        self._resource_stack = []
        self._stack_size = stack_size

    def register(self, resource_id, data):
        self._resource_data[resource_id] = data
        self._resource_stack.append(resource_id)
        if len(self._resource_stack) > self._stack_size:
            remove = self._resource_stack.pop(0)
            if remove in self._resource_data:
                # I don't know why it ever wouldn't be, but I have occasionally got a key error here
                self._resource_data.pop(remove)

    def get(self, resource_id):
        return self._resource_data.get(resource_id)

    def resource(self, resource_class):
        for resource in self._resources:
            if isinstance(resource, resource_class):
                return resource
        inst = resource_class(self)
        self._resources.append(inst)
        return inst


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
        except Exception as e:
            raise ResourceUnavailable()

        self._resource_bundle.register(resource_id, data)
        return data