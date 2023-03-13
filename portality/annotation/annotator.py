from portality.models import Application, Annotation
from portality.annotation.resource_bundle import ResourceBundle

from typing import List


class Annotator(object):
    __identity__ = "base_annotator"

    def name(self):
        return self.__identity__

    def annotate(self, application_form: dict,
                        application: Application,
                        annotations: Annotation,
                        resources: ResourceBundle,
                        existing: Annotation=None) -> List[str]:
        raise NotImplementedError()
