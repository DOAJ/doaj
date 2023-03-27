from doajtest.fixtures.resources import ResourcesFixtureFactory

from portality.annotation.resource_bundle import ResourceUnavailable


class ResourceBundleResourceMockFactory(object):
    @classmethod
    def no_contact_resource_fetch(cls, version=None):
        def mock(self, *args, **kwargs):
            if self.__identity__ == "issn_org":
                issn = None
                if "issn" in kwargs:
                    issn = kwargs["issn"]
                if len(args) > 0:
                    issn = args[0]
                return ResourcesFixtureFactory.issn_org(issn=issn, version=version)

            return None

        return mock

    @classmethod
    def fail_fetch(cls):
        def mock(self, *args, **kwargs):
            raise ResourceUnavailable()

        return mock

    @classmethod
    def not_found_fetch(cls):
        def mock(self, *args, **kwargs):
            return None

        return mock