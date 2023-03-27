from portality.models import JournalLikeObject, Annotation
from portality.annotation.resource_bundle import ResourceBundle

from typing import Callable


class Annotator(object):
    __identity__ = "base_annotator"

    def name(self):
        return self.__identity__

    def annotate(self, form: dict,
                        jla: JournalLikeObject,
                        annotations: Annotation,
                        resources: ResourceBundle,
                        logger: Callable):
        raise NotImplementedError()
