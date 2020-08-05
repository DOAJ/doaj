# Journal

The JSON structure of the model is as follows:

```json
{
    "admin": {
        "bulk_upload": "string", 
        "contact": [
            {
                "email": "string", 
                "name": "string"
            }
        ], 
        "current_application": "string", 
        "editor": "string", 
        "editor_group": "string", 
        "in_doaj": true, 
        "notes": [
            {
                "date": "2018-01-25T09:45:44Z", 
                "note": "string"
            }
        ], 
        "owner": "string", 
        "related_applications": [
            {
                "application_id": "string", 
                "date_accepted": "2018-01-25T09:45:44Z", 
                "status": "string"
            }
        ], 
        "seal": true, 
        "ticked": true
    }, 
    "bibjson": {
        "active": true, 
        "allows_fulltext_indexing": true, 
        "alternative_title": "string", 
        "apc": {
            "average_price": 0, 
            "currency": "string"
        }, 
        "apc_url": "string", 
        "archiving_policy": {
            "known": [
                "string"
            ], 
            "nat_lib": "string", 
            "other": "string", 
            "url": "string"
        }, 
        "article_statistics": {
            "statistics": true, 
            "url": "string"
        }, 
        "author_copyright": {
            "copyright": "string", 
            "url": "string"
        }, 
        "author_pays": "string", 
        "author_pays_url": "string", 
        "author_publishing_rights": {
            "publishing_rights": "string", 
            "url": "string"
        }, 
        "country": "string", 
        "deposit_policy": [
            "string"
        ], 
        "discontinued_date": "2018-01-25", 
        "editorial_review": {
            "process": "string", 
            "url": "string"
        }, 
        "format": [
            "string"
        ], 
        "identifier": [
            {
                "id": "string", 
                "type": "string"
            }
        ], 
        "institution": "string", 
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
                "embedded": true, 
                "embedded_example_url": "string", 
                "open_access": true, 
                "title": "string", 
                "type": "string", 
                "url": "string", 
                "version": "string"
            }
        ], 
        "link": [
            {
                "content_type": "string", 
                "type": "string", 
                "url": "string"
            }
        ], 
        "oa_end": {
            "number": "string", 
            "volume": "string", 
            "year": 0
        }, 
        "oa_start": {
            "number": "string", 
            "volume": "string", 
            "year": 0
        }, 
        "persistent_identifier_scheme": [
            "string"
        ], 
        "plagiarism_detection": {
            "detection": true, 
            "url": "string"
        }, 
        "provider": "string", 
        "publication_time": 0, 
        "publisher": "string", 
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
        "submission_charges": {
            "average_price": 0, 
            "currency": "string"
        }, 
        "submission_charges_url": "string", 
        "title": "string"
    }, 
    "created_date": "2018-01-25T09:45:44Z", 
    "id": "string", 
    "index": {
        "aims_scope_url": "string", 
        "asciiunpunctitle": "string", 
        "author_instructions_url": "string", 
        "classification": [
            "string"
        ], 
        "classification_paths": [
            "string"
        ], 
        "continued": "string", 
        "country": "string", 
        "editorial_board_url": "string", 
        "has_apc": "string", 
        "has_editor": "string", 
        "has_editor_group": "string", 
        "has_seal": "string", 
        "homepage_url": "string", 
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
        "oa_statement_url": "string", 
        "provider_ac": "string", 
        "publisher": [
            "string"
        ], 
        "publisher_ac": "string", 
        "schema_code": [
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
        "unpunctitle": "string", 
        "waiver_policy_url": "string"
    }, 
    "last_manual_update": "2018-01-25T09:45:44Z", 
    "last_reapplication": "2018-01-25T09:45:44Z", 
    "last_updated": "2018-01-25T09:45:44Z"
}
```

Each of the fields is defined as laid out in the table below.  All fields are optional unless otherwise specified:

| Field | Description | Datatype | Format | Allowed Values |
| ----- | ----------- | -------- | ------ | -------------- |
| admin.bulk_upload |  | unicode |  |  |
| admin.contact.email |  | unicode |  |  |
| admin.contact.name |  | unicode |  |  |
| admin.current_application |  | unicode |  |  |
| admin.editor |  | unicode |  |  |
| admin.editor_group |  | unicode |  |  |
| admin.in_doaj |  | bool |  |  |
| admin.notes.date |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| admin.notes.note |  | unicode |  |  |
| admin.owner |  | unicode |  |  |
| admin.related_applications.application_id |  | unicode |  |  |
| admin.related_applications.date_accepted |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| admin.related_applications.status |  | unicode |  |  |
| admin.seal |  | bool |  |  |
| admin.ticked |  | bool |  |  |
| bibjson.active |  | bool |  |  |
| bibjson.allows_fulltext_indexing |  | bool |  |  |
| bibjson.alternative_title |  | unicode |  |  |
| bibjson.apc.average_price |  | int |  |  |
| bibjson.apc.currency |  | unicode |  |  |
| bibjson.apc_url |  | unicode |  |  |
| bibjson.archiving_policy.known |  | unicode |  |  |
| bibjson.archiving_policy.nat_lib |  | unicode |  |  |
| bibjson.archiving_policy.other |  | unicode |  |  |
| bibjson.archiving_policy.url |  | unicode |  |  |
| bibjson.article_statistics.statistics |  | bool |  |  |
| bibjson.article_statistics.url |  | unicode |  |  |
| bibjson.author_copyright.copyright |  | unicode |  |  |
| bibjson.author_copyright.url |  | unicode |  |  |
| bibjson.author_pays |  | unicode |  |  |
| bibjson.author_pays_url |  | unicode |  |  |
| bibjson.author_publishing_rights.publishing_rights |  | unicode |  |  |
| bibjson.author_publishing_rights.url |  | unicode |  |  |
| bibjson.country |  | unicode |  |  |
| bibjson.deposit_policy |  | unicode |  |  |
| bibjson.discontinued_date |  | unicode | Date, year first: YYYY-MM-DD |  |
| bibjson.editorial_review.process |  | unicode |  |  |
| bibjson.editorial_review.url |  | unicode |  |  |
| bibjson.format |  | unicode |  |  |
| bibjson.identifier.id |  | unicode |  |  |
| bibjson.identifier.type |  | unicode |  |  |
| bibjson.institution |  | unicode |  |  |
| bibjson.is_replaced_by |  | unicode |  |  |
| bibjson.keywords |  | unicode |  |  |
| bibjson.language |  | unicode |  |  |
| bibjson.license.BY |  | bool |  |  |
| bibjson.license.NC |  | bool |  |  |
| bibjson.license.ND |  | bool |  |  |
| bibjson.license.SA |  | bool |  |  |
| bibjson.license.embedded |  | bool |  |  |
| bibjson.license.embedded_example_url |  | unicode |  |  |
| bibjson.license.open_access |  | bool |  |  |
| bibjson.license.title |  | unicode |  |  |
| bibjson.license.type |  | unicode |  |  |
| bibjson.license.url |  | unicode |  |  |
| bibjson.license.version |  | unicode |  |  |
| bibjson.link.content_type |  | unicode |  |  |
| bibjson.link.type |  | unicode |  |  |
| bibjson.link.url |  | unicode |  |  |
| bibjson.oa_end.number |  | unicode |  |  |
| bibjson.oa_end.volume |  | unicode |  |  |
| bibjson.oa_end.year |  | int |  |  |
| bibjson.oa_start.number |  | unicode |  |  |
| bibjson.oa_start.volume |  | unicode |  |  |
| bibjson.oa_start.year |  | int |  |  |
| bibjson.persistent_identifier_scheme |  | unicode |  |  |
| bibjson.plagiarism_detection.detection |  | bool |  |  |
| bibjson.plagiarism_detection.url |  | unicode |  |  |
| bibjson.provider |  | unicode |  |  |
| bibjson.publication_time |  | int |  |  |
| bibjson.publisher |  | unicode |  |  |
| bibjson.replaces |  | unicode |  |  |
| bibjson.subject.code |  | unicode |  |  |
| bibjson.subject.scheme |  | unicode |  |  |
| bibjson.subject.term |  | unicode |  |  |
| bibjson.submission_charges.average_price |  | int |  |  |
| bibjson.submission_charges.currency |  | unicode |  |  |
| bibjson.submission_charges_url |  | unicode |  |  |
| bibjson.title |  | unicode |  |  |
| created_date |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| id |  | unicode |  |  |
| index.aims_scope_url |  | unicode |  |  |
| index.asciiunpunctitle |  | unicode |  |  |
| index.author_instructions_url |  | unicode |  |  |
| index.classification |  | unicode |  |  |
| index.classification_paths |  | unicode |  |  |
| index.continued |  | unicode |  |  |
| index.country |  | unicode |  |  |
| index.editorial_board_url |  | unicode |  |  |
| index.has_apc |  | unicode |  |  |
| index.has_editor |  | unicode |  |  |
| index.has_editor_group |  | unicode |  |  |
| index.has_seal |  | unicode |  |  |
| index.homepage_url |  | unicode |  |  |
| index.institution_ac |  | unicode |  |  |
| index.issn |  | unicode |  |  |
| index.language |  | unicode |  |  |
| index.license |  | unicode |  |  |
| index.oa_statement_url |  | unicode |  |  |
| index.provider_ac |  | unicode |  |  |
| index.publisher |  | unicode |  |  |
| index.publisher_ac |  | unicode |  |  |
| index.schema_code |  | unicode |  |  |
| index.schema_subject |  | unicode |  |  |
| index.subject |  | unicode |  |  |
| index.title |  | unicode |  |  |
| index.unpunctitle |  | unicode |  |  |
| index.waiver_policy_url |  | unicode |  |  |
| last_manual_update |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| last_reapplication |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| last_updated |  | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
