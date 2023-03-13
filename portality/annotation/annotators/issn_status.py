from portality.models import Application, Annotation
from portality.annotation.annotator import Annotator
from portality.annotation.resource_bundle import ResourceBundle, ResourceUnavailable
from portality.annotation.resources.issn_org import ISSNOrg
from typing import List


class ISSNStatus(Annotator):
    __identity__ = "issn_status"

    def annotate(self, application_form: dict,
                        application: Application,
                        annotations: Annotation,
                        resources: ResourceBundle,
                        existing: Annotation=None) -> List[str]:

        logs = []
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

        if eissn is not None:
            if eissn_data is None:
                if not eissn_fail:
                    logs.append("eissn not registered at {x}".format(x=eissn_url))
                    annotations.add_annotation(
                        field="eissn",
                        original_value=eissn,
                        advice="The supplied Electronic ISSN was not found at ISSN.org",
                        reference_url=eissn_url
                    )
            else:
                logs.append("eissn successfully resolved at {x}".format(x=eissn_url))
                annotations.add_annotation(
                    field="eissn",
                    original_value=eissn,
                    advice="The supplied Electronic ISSN was found at ISSN.org",
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
