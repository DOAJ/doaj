from portality.models import JournalLikeObject, Annotation
from portality.annotation.annotator import Annotator
from portality.annotation.resource_bundle import ResourceBundle, ResourceUnavailable
from portality.annotation.resources.issn_org import ISSNOrg
from typing import Callable
from portality.annotation.annotators.issn_active import ISSNAnnotator


class KeepersRegistry(ISSNAnnotator):
    __identity__ = "keepers_registry"

    NOT_FOUND = "not_found"
    FULLY_VALIDATED = "fully_validated"
    NOT_VALIDATED = "not_validated"

    def _apply_rule(self, field, value, data, fail, url, logger, annotations):
        if value is not None:
            if data is None:
                if not fail:
                    logger("{y} not registered at {x}".format(y=field, x=url))
                    annotations.add_annotation(
                        field=field,
                        original_value=value,
                        advice=self.NOT_FOUND,
                        reference_url=url,
                        annotator=self.__identity__
                    )
            else:
                if data.is_registered():
                    logger("{y} confirmed as fully validated at {x}".format(y=value, x=url))
                    annotations.add_annotation(
                        field=field,
                        original_value=value,
                        advice=self.FULLY_VALIDATED,
                        reference_url=url,
                        annotator=self.__identity__
                    )
                else:
                    logger("{y} is not fully validated at {x}".format(y=value, x=url))
                    annotations.add_annotation(
                        field=field,
                        original_value=value,
                        advice=self.NOT_VALIDATED,
                        reference_url=url,
                        annotator=self.__identity__
                    )

    def annotate(self, form: dict,
                        jla: JournalLikeObject,
                        annotations: Annotation,
                        resources: ResourceBundle,
                        logger: Callable):

        eissn, eissn_url, eissn_data, eissn_fail, pissn, pissn_url, pissn_data, pissn_fail = self.retrieve_from_source(form, resources, annotations, logger)

        self._apply_rule("eissn", eissn, eissn_data, eissn_fail, eissn_url, logger, annotations)
        self._apply_rule("pissn", pissn, pissn_data, pissn_fail, pissn_url, logger, annotations)