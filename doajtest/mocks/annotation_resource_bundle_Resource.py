from doajtest.fixtures.resources import ResourcesFixtureFactory


class ResourceBundleResourceMockFactory(object):
    @classmethod
    def no_contact_resource_fetch(cls):
        def mock(self, *args, **kwargs):
            if self.__identity__ == "issn_org":
                issn = None
                if "issn" in kwargs:
                    issn = kwargs["issn"]
                if len(args) > 0:
                    issn = args[0]
                return ResourcesFixtureFactory.issn_org(issn=issn)

            return None

        return mock