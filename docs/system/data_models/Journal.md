# Journal

The JSON structure of the model is as follows:

```json
{
    "admin": {
        "bulk_upload": "string",
        "contact": {
            "email": "string",
            "name": "string"
        },
        "current_application": "string",
        "editor": "string",
        "editor_group": "string",
        "in_doaj": true,
        "notes": [
            {
                "date": "2021-04-16T12:49:43Z",
                "id": "string",
                "note": "string"
            }
        ],
        "owner": "string",
        "related_applications": [
            {
                "application_id": "string",
                "date_accepted": "2021-04-16T12:49:43Z",
                "status": "string"
            }
        ],
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
        "discontinued_date": "2021-04-16",
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
    "created_date": "2021-04-16T12:49:43Z",
    "es_type": "string",
    "id": "string",
    "index": {
        "asciiunpunctitle": "string",
        "classification": [
            "string"
        ],
        "classification_paths": [
            "string"
        ],
        "continued": "string",
        "country": "string",
        "has_apc": "string",
        "has_editor": "string",
        "has_editor_group": "string",
        "has_seal": "string",
        "institution_ac": "string",
        "issn": [
            "string"
        ],
        "language": [
            "string"
        ],
        "license": [
            "string"
        ],
        "publisher_ac": "string",
        "schema_code": [
            "string"
        ],
        "schema_codes_tree": [
            "string"
        ],
        "schema_subject": [
            "string"
        ],
        "subject": [
            "string"
        ],
        "title": [
            "string"
        ],
        "unpunctitle": "string"
    },
    "last_manual_update": "2021-04-16T12:49:43Z",
    "last_reapplication": "2021-04-16T12:49:43Z",
    "last_updated": "2021-04-16T12:49:43Z"
}
```

Each of the fields is defined as laid out in the table below.  All fields are optional unless otherwise specified:

| Field | Description | Datatype | Format | Allowed Values |
| ----- | ----------- | -------- | ------ | -------------- |
| admin.bulk_upload |  | str |  |  |
| admin.contact.email |  | str |  |  |
| admin.contact.name |  | str |  |  |
| admin.current_application |  | str |  |  |
| admin.editor |  | str |  |  |
| admin.editor_group |  | str |  |  |
| admin.in_doaj |  | bool |  |  |
| admin.notes.date |  | str | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| admin.notes.id |  | str |  |  |
| admin.notes.note |  | str |  |  |
| admin.owner |  | str |  |  |
| admin.related_applications.application_id |  | str |  |  |
| admin.related_applications.date_accepted |  | str | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| admin.related_applications.status |  | str |  |  |
| admin.seal |  | bool |  |  |
| admin.ticked |  | bool |  |  |
| bibjson.alternative_title |  | str |  |  |
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
| bibjson.keywords |  | str |  |  |
| bibjson.language |  | str | 2 letter ISO language code |  |
| bibjson.license.BY |  | bool |  |  |
| bibjson.license.NC |  | bool |  |  |
| bibjson.license.ND |  | bool |  |  |
| bibjson.license.SA |  | bool |  |  |
| bibjson.license.type |  | str |  |  |
| bibjson.license.url |  | str | URL |  |
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
| bibjson.preservation.url |  | str | URL |  |
| bibjson.publication_time_weeks |  | int |  |  |
| bibjson.publisher.country |  | str |  |  |
| bibjson.publisher.name |  | str |  |  |
| bibjson.ref.aims_scope |  | str | URL |  |
| bibjson.ref.author_instructions |  | str | URL |  |
| bibjson.ref.journal |  | str | URL |  |
| bibjson.ref.license_terms |  | str | URL |  |
| bibjson.ref.oa_statement |  | str | URL |  |
| bibjson.replaces |  | str |  |  |
| bibjson.subject.code |  | str |  |  |
| bibjson.subject.scheme |  | str |  |  |
| bibjson.subject.term |  | str |  |  |
| bibjson.title |  | str |  |  |
| bibjson.waiver.has_waiver |  | bool |  |  |
| bibjson.waiver.url |  | str | URL |  |
| created_date |  | str | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| es_type |  | str |  |  |
| id |  | str |  |  |
| index.asciiunpunctitle |  | str |  |  |
| index.classification |  | str |  |  |
| index.classification_paths |  | str |  |  |
| index.continued |  | str |  |  |
| index.country |  | str |  |  |
| index.has_apc |  | str |  |  |
| index.has_editor |  | str |  |  |
| index.has_editor_group |  | str |  |  |
| index.has_seal |  | str |  |  |
| index.institution_ac |  | str |  |  |
| index.issn |  | str |  |  |
| index.language |  | str |  |  |
| index.license |  | str |  |  |
| index.publisher_ac |  | str |  |  |
| index.schema_code |  | str |  |  |
| index.schema_codes_tree |  | str |  |  |
| index.schema_subject |  | str |  |  |
| index.subject |  | str |  |  |
| index.title |  | str |  |  |
| index.unpunctitle |  | str |  |  |
| last_manual_update |  | str | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| last_reapplication |  | str | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| last_updated |  | str | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
