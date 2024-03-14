from portality.models import JournalLikeObject, Autocheck
from portality.autocheck.resource_bundle import ResourceBundle

from typing import Callable


class Checker(object):
    __identity__ = "base_checker"

    def name(self):
        return self.__identity__

    def check(self, form: dict,
              jla: JournalLikeObject,
              autochecks: Autocheck,
              resources: ResourceBundle,
              logger: Callable):
        raise NotImplementedError()
