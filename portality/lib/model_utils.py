from enum import Enum
from typing import Type


def create_allowed_values_by_enum(enum_class: Type[Enum]):
    return {
        'allowed_values': [x.value for x in enum_class]
    }