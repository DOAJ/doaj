from portality.models import Application, Annotation
from portality.annotation.annotator import Annotator
from portality.annotation.resource_bundle import ResourceBundle, ResourceUnavailable
from portality.annotation.resources.issn_org import ISSNOrg
from portality.annotation.annotators.issn_status import ISSNAnnotator
from typing import List


class ISSNMatch(ISSNAnnotator):
    __identity__ = "issn_match"

    def annotate(self, application_form: dict,
                        application: Application,
                        annotations: Annotation,
                        resources: ResourceBundle,
                        existing: Annotation=None) -> List[str]:

        logs = []
        eissn, eissn_url, eissn_data, eissn_fail, pissn, pissn_url, pissn_data, pissn_fail = self.retrieve_from_source(application_form, resources, annotations, logs)

        #####################################################
        # EISSN check: get the PISSN from the ISSN.org record
        # and compare to the application's PISSN.
        # * If they match, annotate as successful
        # * If they differ, annotate as error

        if eissn is not None:
            if eissn_data is None:
                if not eissn_fail:
                    logs.append("eissn not registered at {x}".format(x=eissn_url))
            else:
                logs.append("eissn successfully resolved at {x}".format(x=eissn_url))
                issns = [(ident.get("name"), ident.get("value")) for ident in eissn_data.get("identifier", []) if ident.get("value") != eissn]

                # no issn in form, no issn in issn.org
                if pissn is None and len(issns) == 0:
                    annotations.add_annotation(
                        field="pissn",
                        original_value="",
                        advice="There is no print issn registered on issn.org",
                        reference_url=eissn_url
                    )

                # ISSN in form, no ISSN in issn.org
                if pissn is not None and len(issns) == 0:
                    annotations.add_annotation(
                        field="pissn",
                        original_value=pissn,
                        advice="There is no print issn registered on issn.org",
                        suggested_value=[""],
                        reference_url=eissn_url
                    )

                # no ISSN in form, ISSN in issn.org
                if pissn is None and len(issns) > 0:
                    annotations.add_annotation(
                        field="pissn",
                        original_value="",
                        advice="There is one or more potential value for this field in issn.org",
                        suggested_value=issns,
                        reference_url=eissn_url
                    )

                # issn in form, issn in issn.org
                if pissn is not None and len(issns) > 0:
                    # they match
                    if pissn in issns:
                        annotations.add_annotation(
                            field="pissn",
                            original_value=pissn,
                            advice="This issn is registered at issn.org",
                            reference_url=eissn_url
                        )

                    # they don't match
                    if pissn not in issns:
                        annotations.add_annotation(
                            field="pissn",
                            original_value=pissn,
                            advice="This issn is not registered at issn.org",
                            suggested_value=issns,
                            reference_url=eissn_url
                        )

        if pissn is not None:
            if pissn_data is None:
                if not pissn_fail:
                    logs.append("pissn not registered at {x}".format(x=eissn_url))
                    annotations.add_annotation(
                        field="pissn",
                        original_value=pissn,
                        advice="The supplied Print ISSN was not found at ISSN.org",
                        reference_url=pissn_url
                    )
            else:
                logs.append("pissn successfully resolved at {x}".format(x=eissn_url))
                annotations.add_annotation(
                    field="pissn",
                    original_value=pissn,
                    advice="The supplied Print ISSN was found at ISSN.org",
                    reference_url=pissn_url
                )

        return logs
