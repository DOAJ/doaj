from typing import Callable

from portality.autocheck.checker import Checker
from portality.autocheck.resource_bundle import ResourceBundle
from portality.models import JournalLikeObject, Autocheck

ADVICE_NONE_VALUE_FOUND = 'none_value_found'


class NoNoneValue(Checker):
    __identity__ = "no_none_value"

    def check(self, form: dict, jla: JournalLikeObject, autochecks: Autocheck,
              resources: ResourceBundle, logger: Callable):
        fields = [
            'preservation_service_library',
            'preservation_service_other',
            'deposit_policy_other',
            'persistent_identifiers_other',
        ]

        for field in fields:
            if field not in form:
                logger(f'Field {field} not found in form')
                continue

            value = form.get(field)

            if (
                    (isinstance(value, str) and value.strip() == 'None') or
                    (isinstance(value, list) and any([v.strip() == 'None' for v in value]))
            ):
                autochecks.add_check(
                    field=field,
                    original_value=value,
                    advice=ADVICE_NONE_VALUE_FOUND,
                    checked_by=self.__identity__,
                )
