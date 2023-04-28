from portality.models import JournalLikeObject, Annotation
from portality.annotation.annotator import Annotator
from portality.annotation.resource_bundle import ResourceBundle, ResourceUnavailable
from portality.annotation.resources.issn_org import ISSNOrg
from typing import Callable
from portality.annotation.annotators.issn_active import ISSNAnnotator
from datetime import datetime


class KeepersRegistry(ISSNAnnotator):
    __identity__ = "keepers_registry"

    ID_MAP = {
        "CLOCKSS": "http://issn.org/organization/keepers#clockss",
        "LOCKSS": "",
        "Internet Archive": "",
        "PKP PN": "",
        "Portico": ""
    }

    MISSING = "missing"
    PRESENT = "present"
    OUTDATED = "outdated"

    def _get_archive_components(self, eissn_data, pissn_data):
        acs = []
        if eissn_data is not None:
            acs += eissn_data.archive_components
        if pissn_data is not None:
            acs += pissn_data.archive_components
        return acs

    def _extract_archive_data(self, acs):
        ad = {}
        for ac in acs:
            id = ac.get("holdingArchive", {}).get("@id")
            tc = ac.get("temporalCoverage")
            bits = tc.split("/")
            if len(bits) != 2:
                continue
            end_year = int(bits[1].strip())
            if id in ad:
                if end_year > ad[id]:
                    ad[id] = end_year
            else:
                ad[id] = end_year

        return ad

    def annotate(self, form: dict,
                        jla: JournalLikeObject,
                        annotations: Annotation,
                        resources: ResourceBundle,
                        logger: Callable):

        eissn, eissn_url, eissn_data, eissn_fail, pissn, pissn_url, pissn_data, pissn_fail = self.retrieve_from_source(form, resources, annotations, logger)

        url = eissn_url if eissn_url else pissn_url

        acs = self._get_archive_components(eissn_data, pissn_data)
        ad = self._extract_archive_data(acs)
        services = form.get("preservation_service", [])
        logger("There are {x} preservation services on the record: {y}".format(x=len(services), y=",".join(services)))
        for service in services:
            id = self.ID_MAP.get(service)
            if not id:
                continue

            coverage = ad.get(id)
            if not coverage:
                # the archive is not mentioned in issn.org
                logger("Service {x} is not registered at issn.org for this record".format(x=service))
                annotations.add_annotation(
                    field="preservation_service",
                    advice=self.MISSING,
                    reference_url=url,
                    context={"service": service},
                    annotator=self.__identity__
                )
                continue

            if coverage < datetime.utcnow().year - 1:
                # the temporal coverage is too old
                logger("Service {x} is registerd as issn.org for this record, but the archive is not recent enough".format(x=service))
                annotations.add_annotation(
                    field="preservation_service",
                    advice=self.OUTDATED,
                    reference_url=url,
                    context={"service": service},
                    annotator=self.__identity__
                )
            else:
                # the coverage is within a reasonable period
                logger("Service {x} is registerd as issn.org for this record".format(x=service))
                annotations.add_annotation(
                    field="preservation_service",
                    advice=self.PRESENT,
                    reference_url=url,
                    context={"service": service},
                    annotator=self.__identity__
                )