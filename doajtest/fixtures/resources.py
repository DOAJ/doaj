from copy import deepcopy

from portality.annotation.resources.issn_org import ISSNOrgData

class ResourcesFixtureFactory(object):
    @classmethod
    def issn_org(cls, issn=None, version=None):
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

        return ISSNOrgData(record)


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