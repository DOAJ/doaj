from copy import deepcopy
from datetime import datetime

from portality.autocheck.resources.issn_org import ISSNOrgData


class ResourcesFixtureFactory(object):
    @classmethod
    def issn_org(cls, issn=None, version=None, archive_components=None):
        record = deepcopy(ISSN_ORG)

        if issn is not None:
            record["@id"] = "https://portal.issn.org/resource/ISSN/" + issn
            record["exampleOfWork"]["@id"] = record["@id"]
            record["exampleOfWork"]["workExample"][0]["@id"] = record["@id"]
            record["issn"] = issn
            record["identifier"][0]["value"] = issn
            record["identifier"][1]["value"] = issn
            record["mainEntityOfPage"]["@id"] = record["@id"] + "#Record"
            record["mainEntityOfPage"]["mainEntity"] = record["@id"]

        if version is not None:
            record["mainEntityOfPage"]["version"] = version

        if archive_components is not None:
            record["subjectOf"] = []
            for service, in_time in archive_components.items():
                ac_base = deepcopy(SUBJECT_OF)
                service_url = ID_MAP.get(service)
                ac_base["holdingArchive"]["@id"] = service_url
                ac_base["holdingArchive"]["name"] = service
                if in_time is True:
                    now = datetime.utcnow()
                    last = now.year - 1
                    first = now.year - 3
                    ac_base["temporalCoverage"] = "{x}/{y}".format(x=first, y=last)
                elif in_time is False:
                    now = datetime.utcnow()
                    last = now.year - 4
                    first = now.year - 6
                    ac_base["temporalCoverage"] = "{x}/{y}".format(x=first, y=last)
                else:
                    # time coverage missing the closing component
                    now = datetime.utcnow()
                    first = now.year - 3
                    ac_base["temporalCoverage"] = "{x}/".format(x=first)

                record["subjectOf"].append(ac_base)

        return ISSNOrgData(record)


ID_MAP = {
    "CLOCKSS": "http://issn.org/organization/keepers#clockss",
    "LOCKSS": "http://issn.org/organization/keepers#lockss",
    "Internet Archive": "http://issn.org/organization/keepers#internetarchive",
    "PKP PN": "http://issn.org/organization/keepers#pkppln",
    "Portico": "http://issn.org/organization/keepers#portico"
}

SUBJECT_OF = {
    "@type": "ArchiveComponent",
    "creativeWorkStatus": "Preserved",
    "description": "1 to 3",
    "holdingArchive": {
        "@type": "ArchiveOrganization",
        "@id": "http://issn.org/organization/keepers#clockss",
        "name": "CLOCKSS Archive"
    },
    "abstract": "1 to 3",
    "dateModified": "2023-06-19",
    "temporalCoverage": ""
}

ISSN_ORG = {
    "@context": "http://schema.org/",
    "@id": "https://portal.issn.org/resource/ISSN/1234-1231",
    "@type": "Periodical",
    "exampleOfWork": {
        "@id": "https://portal.issn.org/resource/ISSN-L/1234-1231",
        "@type": "CreativeWork",
        "workExample": [
            {
                "@id": "https://portal.issn.org/resource/ISSN/1234-1231",
                "name": "Wiadomości Unii Spółdzielców Mieszkaniowych"
            }
        ]
    },
    "issn": "1234-1231",
    "identifier": [
        {
            "@type": "PropertyValue",
            "name": "ISSN",
            "value": "1234-1231",
            "description": "Valid"
        },
        {
            "@type": "PropertyValue",
            "name": "ISSN-L",
            "value": "1234-1231",
            "description": "Valid"
        }
    ],
    "name": "Wiadomości Unii Spółdzielców Mieszkaniowych",
    "alternateName": "Wiadomości Unii Spółdzielców Mieszkaniowych.",
    "publication": {
        "@id": "https://portal.issn.org/resource/ISSN/1234-1231#ReferencePublicationEvent",
        "@type": "PublicationEvent",
        "location": {
            "@id": "https://www.iso.org/obp/ui/#iso:code:3166:PL",
            "@type": "Country",
            "name": "Poland"
        }
    },
    "mainEntityOfPage": {
        "@id": "https://portal.issn.org/resource/ISSN/1234-1231#Record",
        "@type": "CreativeWork",
        "dateModified": "05/01/2023",
        "mainEntity": "https://portal.issn.org/resource/ISSN/1234-1231",
        "sourceOrganization": {
            "@id": "https://www.issn.org/organization/ISSNCenter#57",
            "@type": "Organization",
            "name": "ISSN National Centre for Poland"
        },
        "version": "Register"
    },
    "material": "Print"
}