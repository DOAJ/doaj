from portality.models import JournalLikeObject, Annotation
from portality.annotation.annotator import Annotator
from portality.annotation.resource_bundle import ResourceBundle, ResourceUnavailable
from portality.annotation.resources.issn_org import ISSNOrg
from typing import Callable


class ISSNAnnotator(Annotator):

    UNABLE_TO_ACCESS = "unable_to_access"

    def retrieve_from_source(self, form, resources, annotations, logger):
        source = ISSNOrg(resources)

        eissn = form.get("eissn")
        pissn = form.get("pissn")

        eissn_data = None
        pissn_data = None
        eissn_url = None
        pissn_url = None
        eissn_fail = False
        pissn_fail = False

        if eissn is not None:
            eissn_url = source.reference_url(issn=eissn)
            logger("Looking up eissn at {x}".format(x=eissn_url))
            try:
                eissn_data = source.fetch(issn=eissn)
                logger("Data received for eissn from {x}".format(x=eissn_url))
            except ResourceUnavailable:
                logger("Unable to resolve eissn at {x}".format(x=eissn_url))
                annotations.add_annotation(
                    field="eissn",
                    original_value=eissn,
                    advice=self.UNABLE_TO_ACCESS,
                    reference_url=eissn_url
                )
                eissn_fail = True

        if pissn is not None:
            pissn_url = source.reference_url(issn=pissn)
            logger("Looking up pissn at {x}".format(x=pissn_url))
            try:
                pissn_data = source.fetch(issn=pissn)
                logger("Data received for pissn from {x}".format(x=pissn_url))
            except ResourceUnavailable:
                logger("Unable to resolve pissn at {x}".format(x=pissn_url))
                annotations.add_annotation(
                    field="pissn",
                    original_value=pissn,
                    advice=self.UNABLE_TO_ACCESS,
                    reference_url=pissn_url
                )
                pissn_fail = True

        return eissn, eissn_url, eissn_data, eissn_fail, pissn, pissn_url, pissn_data, pissn_fail


class ISSNActive(ISSNAnnotator):
    __identity__ = "issn_status"

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
                        reference_url=url
                    )
            else:
                if data.is_registered():
                    logger("{y} confirmed as fully validated at {x}".format(y=value, x=url))
                    annotations.add_annotation(
                        field=field,
                        original_value=value,
                        advice=self.FULLY_VALIDATED,
                        reference_url=url
                    )
                else:
                    logger("{y} is not fully validated at {x}".format(y=value, x=url))
                    annotations.add_annotation(
                        field=field,
                        original_value=value,
                        advice=self.NOT_VALIDATED,
                        reference_url=url
                    )

    def annotate(self, form: dict,
                        jla: JournalLikeObject,
                        annotations: Annotation,
                        resources: ResourceBundle,
                        logger: Callable):

        eissn, eissn_url, eissn_data, eissn_fail, pissn, pissn_url, pissn_data, pissn_fail = self.retrieve_from_source(form, resources, annotations, logger)

        self._apply_rule("eissn", eissn, eissn_data, eissn_fail, eissn_url, logger, annotations)
        self._apply_rule("pissn", pissn, pissn_data, pissn_fail, pissn_url, logger, annotations)