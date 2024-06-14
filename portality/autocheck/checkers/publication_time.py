from portality.models import JournalLikeObject, Autocheck
from portality.autocheck.checker import Checker
from portality.autocheck.resource_bundle import ResourceBundle
from typing import Callable

class PublicationTime(Checker):
    __identity__ = "publication_time"

    BELOW_2_WEEKS = "below_2_weeks"
    OVER_2_WEEKS = "over_2_weeks"

    def check(self, form: dict,
              jla: JournalLikeObject,
              autochecks: Autocheck,
              resources: ResourceBundle,
              logger: Callable):

        publication_time = form.get("publication_time_weeks")

        print(publication_time)

        if int(publication_time) <= 2:
            autochecks.add_check(
                field="publication_time_weeks",
                advice=self.BELOW_2_WEEKS,
                checked_by=self.__identity__
            )
        else:
            autochecks.add_check(
                field="publication_time_weeks",
                advice=self.OVER_2_WEEKS,
                checked_by=self.__identity__
            )
