from portality.models import Application, Annotation
from portality.annotation.annotator import Annotator
from portality.annotation.resource_bundle import ResourceBundle, ResourceUnavailable
from portality.annotation.resources.issn_org import ISSNOrg
from typing import List


class ISSNAnnotator(Annotator):
    def retrieve_from_source(self, application_form, resources, annotations, logs):
        source = ISSNOrg(resources)

        eissn = application_form.get("eissn")
        pissn = application_form.get("pissn")

        eissn_data = None
        pissn_data = None
        eissn_url = None
        pissn_url = None
        eissn_fail = False
        pissn_fail = False

        if eissn is not None:
            eissn_url = source.reference_url(issn=eissn)
            logs.append("Looking up eissn at {x}".format(x=eissn_url))
            try:
                eissn_data = source.fetch(issn=eissn)
                logs.append("Data received for eissn from {x}".format(x=eissn_url))
            except ResourceUnavailable:
                logs.append("Unable to resolve eissn at {x}".format(x=eissn_url))
                annotations.add_annotation(
                    field="eissn",
                    original_value=eissn,
                    advice="We were unable to access ISSN.org to check this value",
                    reference_url=eissn_url
                )
                eissn_fail = True

        if pissn is not None:
            pissn_url = source.reference_url(issn=pissn)
            logs.append("Looking up pissn at {x}".format(x=pissn_url))
            try:
                pissn_data = source.fetch(issn=pissn)
                logs.append("Data received for pissn from {x}".format(x=pissn_url))
            except ResourceUnavailable:
                logs.append("Unable to resolve pissn at {x}".format(x=pissn_url))
                annotations.add_annotation(
                    field="pissn",
                    original_value=pissn,
                    advice="We were unable to access ISSN.org to check this value",
                    reference_url=pissn_url
                )
                pissn_fail = True

        return eissn, eissn_url, eissn_data, eissn_fail, pissn, pissn_url, pissn_data, pissn_fail


class ISSNStatus(ISSNAnnotator):
    __identity__ = "issn_status"

    def _apply_rule(self, field, value, data, fail, url, logs, annotations):
        if value is not None:
            if data is None:
                if not fail:
                    logs.append("{y} not registered at {x}".format(y=field, x=url))
                    annotations.add_annotation(
                        field=field,
                        original_value=value,
                        advice="The supplied ISSN was not found at ISSN.org",
                        reference_url=url
                    )
            else:
                logs.append("{y} successfully resolved at {x}".format(y=field, x=url))
                annotations.add_annotation(
                    field=field,
                    original_value=value,
                    advice="The supplied ISSN was found at ISSN.org",
                    reference_url=url
                )

    def annotate(self, application_form: dict,
                        application: Application,
                        annotations: Annotation,
                        resources: ResourceBundle,
                        existing: Annotation=None) -> List[str]:

        logs = []
        eissn, eissn_url, eissn_data, eissn_fail, pissn, pissn_url, pissn_data, pissn_fail = self.retrieve_from_source(application_form, resources, annotations, logs)

        self._apply_rule("eissn", eissn, eissn_data, eissn_fail, eissn_url, logs, annotations)
        self._apply_rule("pissn", pissn, pissn_data, pissn_fail, pissn_url, logs, annotations)

        return logs
