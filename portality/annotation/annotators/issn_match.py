from portality.models import JournalLikeObject, Annotation
from portality.annotation.annotator import Annotator
from portality.annotation.resource_bundle import ResourceBundle, ResourceUnavailable
from portality.annotation.resources.issn_org import ISSNOrg
from portality.annotation.annotators.issn_active import ISSNAnnotator
from typing import Callable


class ISSNMatch(ISSNAnnotator):
    __identity__ = "issn_match"

    def _apply_rule(self, field, value, data, fail, url, logger, other_field, other_field_value, annotations):
        if value is not None:
            if data is None:
                if not fail:
                    logger("{y} not registered at {x}".format(y=field, x=url))
            else:
                logger("{y} successfully resolved at {x}".format(y=field, x=url))
                issns = [(ident.get("name"), ident.get("value")) for ident in data.get("identifier", []) if
                         ident.get("value") != value]

                # no issn in form, no issn in issn.org
                if other_field_value is None and len(issns) == 0:
                    annotations.add_annotation(
                        field=other_field,
                        original_value="",
                        advice="There is no {y} registered on issn.org".format(y=other_field),
                        reference_url=url
                    )

                # ISSN in form, no ISSN in issn.org
                if other_field_value is not None and len(issns) == 0:
                    annotations.add_annotation(
                        field=other_field,
                        original_value=other_field_value,
                        advice="There is no {y} registered on issn.org".format(y=other_field),
                        suggested_value=[""],
                        reference_url=url
                    )

                # no ISSN in form, ISSN in issn.org
                if other_field_value is None and len(issns) > 0:
                    annotations.add_annotation(
                        field=other_field,
                        original_value="",
                        advice="There is one or more potential value for this field in issn.org",
                        suggested_value=issns,
                        reference_url=url
                    )

                # issn in form, issn in issn.org
                if other_field_value is not None and len(issns) > 0:
                    # they match
                    if other_field_value in issns:
                        annotations.add_annotation(
                            field=other_field,
                            original_value=other_field_value,
                            advice="This issn is registered at issn.org",
                            reference_url=url
                        )

                    # they don't match
                    if other_field_value not in issns:
                        annotations.add_annotation(
                            field="pissn",
                            original_value=other_field_value,
                            advice="This issn is not registered at issn.org",
                            suggested_value=issns,
                            reference_url=url
                        )

    def annotate(self, form: dict,
                        jla: JournalLikeObject,
                        annotations: Annotation,
                        resources: ResourceBundle,
                        logger: Callable):

        eissn, eissn_url, eissn_data, eissn_fail, pissn, pissn_url, pissn_data, pissn_fail = self.retrieve_from_source(form, resources, annotations, logs)

        self._apply_rule("eissn", eissn, eissn_data, eissn_fail, eissn_url, logger, "pissn", pissn, annotations)
        self._apply_rule("pissn", pissn, eissn_data, eissn_fail, eissn_url, logger, "eissn", eissn, annotations)
