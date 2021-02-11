from portality.dao import DomainObject


class LCC(DomainObject):
    __type__ = "lcc"

    def pathify(self, term, path_separator=": "):
        """
        Convert the given term into a string containing the path from the root via the parents to the term
        :param term:
        :param path_separator:
        :return:
        """

        def dive(node, path):
            if node.get("name") == term:
                path.append(term)
                return True

            if "children" not in node:
                return False

            path.append(node.get("name"))

            for n in node.get("children", []):
                found = dive(n, path)
                if found:
                    return True

            path.pop()
            return False

        roots = self.data.get("children", [])
        for r in roots:
            path = []
            found = dive(r, path)
            if found:
                return path_separator.join(path)

        return None

    def expand_codes(self, code):
        def dive(node, path):
            if node.get("code") == code:
                path.append(code)
                return True

            if "children" not in node:
                return False

            path.append(node.get("code"))

            for n in node.get("children", []):
                found = dive(n, path)
                if found:
                    return True

            path.pop()
            return False

        roots = self.data.get("children", [])
        for r in roots:
            path = []
            found = dive(r, path)
            if found:
                return path

        return []

    def longest(self, paths):
        """
        Returns only the longest paths from the provided classification paths (created with pathify)
        :param paths:
        :return:
        """
        keep = []
        for candidate in paths:
            trip = False
            for other in paths:
                # if the candidate is a substring of another, longer, string, hit the tripwire
                if candidate in other and len(candidate) != len(other):
                    trip = True
                    break

            if not trip:
                if candidate not in keep:
                    keep.append(candidate)

        return keep

    def save(self, **kwargs):
        self.set_id("lcc")
        return super(LCC, self).save(**kwargs)
