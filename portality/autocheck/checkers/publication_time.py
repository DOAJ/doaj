from portality.core import app
from portality.models import JournalLikeObject, Autocheck
from portality.autocheck.checker import Checker
from portality.autocheck.resource_bundle import ResourceBundle
from typing import Callable

class PublicationTime(Checker):
    __identity__ = "publication_time"

    BELOW_THRESHOLD = "below_threshold"
    OVER_THRESHOLD = "over_threshold"

    def check(self, form: dict,
              jla: JournalLikeObject,
              autochecks: Autocheck,
              resources: ResourceBundle,
              logger: Callable):

        publication_time = form.get("publication_time_weeks")
        publication_time_threshold = app.config.get("AUTOCHECK_PUBLICATION_THRESHOLD", 2)

        if int(publication_time) <= publication_time_threshold:
            autochecks.add_check(
                field="publication_time_weeks",
                advice=self.BELOW_THRESHOLD,
                checked_by=self.__identity__,
                context={"threshold": publication_time_threshold}
            )
        else:
            autochecks.add_check(
                field="publication_time_weeks",
                advice=self.OVER_THRESHOLD,
                checked_by=self.__identity__,
                context={"threshold": publication_time_threshold}
            )
