from typing import Iterable

import jsonpath_ng.ext


def find_values(query: str, data: dict) -> Iterable:
    return (m.value for m in jsonpath_ng.ext.parse(query).find(data))
