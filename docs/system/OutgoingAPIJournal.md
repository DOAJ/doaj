# OutgoingJournal

The JSON structure of the model is as follows:

```json
{
    "admin": {
        "in_doaj": true,
        "seal": true,
        "ticked": true
    },
    "bibjson": {
        "alternative_title": "string",
        "apc": {
            "has_apc": true,
            "max": [
                {
                    "currency": "string",
                    "price": 0
                }
            ],
            "url": "string"
        },
        "article": {
            "i4oc_open_citations": true,
            "license_display": [
                "string"
            ],
            "license_display_example_url": "string",
            "orcid": true
        },
        "boai": true,
        "copyright": {
            "author_retains": true,
            "url": "string"
        },
        "deposit_policy": {
            "has_policy": true,
            "is_registered": true,
            "service": [
                "string"
            ],
            "url": "string"
        },
        "discontinued_date": "2020-07-01",
        "editorial": {
            "board_url": "string",
            "review_process": [
                "string"
            ],
            "review_url": "string"
        },
        "eissn": "string",
        "institution": {
            "country": "string",
            "name": "string"
        },
        "is_replaced_by": [
            "string"
        ],
        "keywords": [
            "string"
        ],
        "language": [
            "string"
        ],
        "license": [
            {
                "BY": true,
                "NC": true,
                "ND": true,
                "SA": true,
                "type": "string",
                "url": "string"
            }
        ],
        "other_charges": {
            "has_other_charges": true,
            "url": "string"
        },
        "pid_scheme": {
            "has_pid_scheme": true,
            "scheme": [
                "string"
            ]
        },
        "pissn": "string",
        "plagiarism": {
            "detection": true,
            "url": "string"
        },
        "preservation": {
            "has_preservation": true,
            "national_library": [
                "string"
            ],
            "service": [
                "string"
            ],
            "url": "string"
        },
        "publication_time_weeks": 0,
        "publisher": {
            "country": "string",
            "name": "string"
        },
        "ref": {
            "aims_scope": "string",
            "author_instructions": "string",
            "journal": "string",
            "license_terms": "string",
            "oa_statement": "string"
        },
        "replaces": [
            "string"
        ],
        "subject": [
            {
                "code": "string",
                "scheme": "string",
                "term": "string"
            }
        ],
        "title": "string",
        "waiver": {
            "has_waiver": true,
            "url": "string"
        }
    },
    "created_date": "2020-07-01T15:44:16Z",
    "id": "string",
    "last_manual_update": "2020-07-01T15:44:16Z",
    "last_updated": "2020-07-01T15:44:16Z"
}
```

Each of the fields is defined as laid out in the table below.  All fields are optional unless otherwise specified:

| Field | Description | Datatype | Format | Allowed Values |
| ----- | ----------- | -------- | ------ | -------------- |
| admin.in_doaj | Whether the journal appears in the public corpus of DOAJ | bool |  |  |
| admin.seal | Does the journal qualify for the DOAJ Seal | bool |  |  |
| admin.ticked | Is the journal ticked?  This means that it has successfully re-applied for continued presence in DOAJ | bool |  |  |
| bibjson.alternative_title | See application form Q3 - https://doaj.org/application/new#alternative_title-container | str |  |  |
| bibjson.apc.has_apc |  | bool |  |  |
| bibjson.apc.max.currency |  | str |  |  |
| bibjson.apc.max.price |  | int |  |  |
| bibjson.apc.url |  | str | URL |  |
| bibjson.article.i4oc_open_citations |  | bool |  |  |
| bibjson.article.license_display |  | str |  | Embed, Display, No |
| bibjson.article.license_display_example_url |  | str | URL |  |
| bibjson.article.orcid |  | bool |  |  |
| bibjson.boai |  | bool |  |  |
| bibjson.copyright.author_retains |  | bool |  |  |
| bibjson.copyright.url |  | str | URL |  |
| bibjson.deposit_policy.has_policy |  | bool |  |  |
| bibjson.deposit_policy.is_registered |  | bool |  |  |
| bibjson.deposit_policy.service |  | str |  |  |
| bibjson.deposit_policy.url |  | str | URL |  |
| bibjson.discontinued_date |  | str | Date, year first: YYYY-MM-DD |  |
| bibjson.editorial.board_url |  | str | URL |  |
| bibjson.editorial.review_process |  | str |  |  |
| bibjson.editorial.review_url |  | str | URL |  |
| bibjson.eissn |  | str |  |  |
| bibjson.institution.country |  | str |  |  |
| bibjson.institution.name |  | str |  |  |
| bibjson.is_replaced_by |  | str |  |  |
| bibjson.keywords | as per application form Q34 - https://doaj.org/application/new#keywords-container | str |  |  |
| bibjson.language | as per application form Q35 - https://doaj.org/application/new#languages-container | str | 2 letter ISO language code |  |
| bibjson.license.BY | Does the licence have an attribution clause. | bool |  |  |
| bibjson.license.NC | Does the licence have a non-commercial clause. | bool |  |  |
| bibjson.license.ND | Does the licence have a no-derivatives clause. | bool |  |  |
| bibjson.license.SA | Does the licence have a share-alike clause. | bool |  |  |
| bibjson.license.type | The licence type from application form Q47 - https://doaj.org/application/new#license-container | str |  |  |
| bibjson.license.url | see application form Q49 - https://doaj.org/application/new#license_url-container | str | URL |  |
| bibjson.other_charges.has_other_charges |  | bool |  |  |
| bibjson.other_charges.url |  | str | URL |  |
| bibjson.pid_scheme.has_pid_scheme |  | bool |  |  |
| bibjson.pid_scheme.scheme |  | str |  |  |
| bibjson.pissn |  | str |  |  |
| bibjson.plagiarism.detection |  | bool |  |  |
| bibjson.plagiarism.url |  | str | URL |  |
| bibjson.preservation.has_preservation |  | bool |  |  |
| bibjson.preservation.national_library |  | str |  |  |
| bibjson.preservation.service |  | str |  |  |
| bibjson.preservation.url |  | str |  |  |
| bibjson.publication_time_weeks |  | int |  |  |
| bibjson.publisher.country |  | str |  |  |
| bibjson.publisher.name |  | str |  |  |
| bibjson.ref.aims_scope |  | str | URL |  |
| bibjson.ref.author_instructions |  | str | URL |  |
| bibjson.ref.journal |  | str | URL |  |
| bibjson.ref.license_terms |  | str | URL |  |
| bibjson.ref.oa_statement |  | str | URL |  |
| bibjson.replaces |  | str |  |  |
| bibjson.subject.code | assigned subject code | str |  |  |
| bibjson.subject.scheme | assigned subject scheme | str |  |  |
| bibjson.subject.term | assigned subject term | str |  |  |
| bibjson.title | see application form Q1 - https://doaj.org/application/new#title-container | str |  |  |
| bibjson.waiver.has_waiver |  | bool |  |  |
| bibjson.waiver.url |  | str | URL |  |
| created_date | Date the record was created in DOAJ. | str | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| id | ID assigned by DOAJ for the record. | str |  |  |
| last_manual_update |  | str | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| last_updated | Date the record was last updated in DOAJ. | str | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
