from portality.models import Application, Annotation
from portality.annotation.annotator import Annotator
from portality.annotation.resource_bundle import ResourceBundle, ResourceUnavailable
from portality.annotation.resources.issn_org import ISSNOrg
from typing import List


class ISSNOrgAnnotator(Annotator):

    def _get_issns_and_data(self, application_form):
        eissn = application_form.get("eissn")
        pissn = application_form.get("pissn")

        eissn_data = None
        pissn_data = None
        eissn_url = None
        pissn_url = None
        eissn_fail = False
        pissn_fail = False

class ISSNMatch(Annotator):
    __identity__ = "issn_match"

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

        #################################################
        # Data retrieval, get the print and electronic issn records from ISSN.org
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
