# OutgoingJournal

The JSON structure of the model is as follows:

```json
{
    "admin": {
        "contact": [
            {
                "email": "string", 
                "name": "string"
            }
        ], 
        "in_doaj": true, 
        "owner": "string", 
        "seal": true, 
        "ticked": true
    }, 
    "bibjson": {
        "allows_fulltext_indexing": true, 
        "alternative_title": "string", 
        "apc": {
            "average_price": 0, 
            "currency": "string"
        }, 
        "apc_url": "string", 
        "archiving_policy": {
            "policy": [
                {
                    "domain": "string", 
                    "name": "string"
                }
            ], 
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
        "author_publishing_rights": {
            "publishing_rights": "string", 
            "url": "string"
        }, 
        "country": "string", 
        "deposit_policy": [
            "string"
        ], 
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
                "type": "string", 
                "url": "string"
            }
        ], 
        "oa_end": {
            "number": 0, 
            "volume": 0, 
            "year": 0
        }, 
        "oa_start": {
            "number": 0, 
            "volume": 0, 
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
    "created_date": "2019-07-01T08:13:23Z", 
    "id": "string", 
    "last_updated": "2019-07-01T08:13:23Z"
}
```

Each of the fields is defined as laid out in the table below.  All fields are optional unless otherwise specified:

| Field | Description | Datatype | Format | Allowed Values |
| ----- | ----------- | -------- | ------ | -------------- |
| admin.contact.email | Email address of the contact for this journal | unicode |  |  |
| admin.contact.name | Name for the contact for this journal | unicode |  |  |
| admin.in_doaj | Whether the journal appears in the public corpus of DOAJ | bool |  |  |
| admin.owner | The user ID who owns the journal.  If accessing this via the API | unicode |  |  |
| admin.seal | Does the journal qualify for the DOAJ Seal | bool |  |  |
| admin.ticked | Is the journal ticked?  This means that it has successfully re-applied for continued presence in DOAJ | bool |  |  |
| bibjson.allows_fulltext_indexing | See application form Q27 - https://doaj.org/application/new#crawl_permission-container | bool |  |  |
| bibjson.alternative_title | See application form Q3 - https://doaj.org/application/new#alternative_title-container | unicode |  |  |
| bibjson.apc.average_price | Only required if there are processing charges, see application form Q13 and Q15 - https://doaj.org/application/new#processing_charges-container, https://doaj.org/application/new#processing_charges_amount-container | int |  |  |
| bibjson.apc.currency | Only required if there are processing charges, see application form Q13 and Q15 - https://doaj.org/application/new#processing_charges-container, https://doaj.org/application/new#processing_charges_currency-container | unicode |  |  |
| bibjson.apc_url | See application form Q14 - https://doaj.org/application/new#processing_charges_url-container | unicode | URL |  |
| bibjson.archiving_policy.policy.domain | The name if either "A national library" or "Other" archiving policy is in bibjson.archiving_policy.policy.name else omitted, as per application form Q25 - https://doaj.org/application/new#digital_archiving_policy-container | unicode |  |  |
| bibjson.archiving_policy.policy.name | The name of the archiving policy.  One from the list on application form Q25 - https://doaj.org/application/new#digital_archiving_policy-container | unicode |  |  |
| bibjson.archiving_policy.url | As per application form Q26 - https://doaj.org/application/new#digital_archiving_policy_url-container | unicode | URL |  |
| bibjson.article_statistics.statistics | See application form Q30 - https://doaj.org/application/new#download_statistics-container | bool |  |  |
| bibjson.article_statistics.url | See application form Q31 - https://doaj.org/application/new#download_statistics_url-container | unicode | URL |  |
| bibjson.author_copyright.copyright | See application form Q52 - https://doaj.org/application/new#copyright-container | unicode |  |  |
| bibjson.author_copyright.url | See application form Q53 - https://doaj.org/application/new#copyright_url-container | unicode | URL |  |
| bibjson.author_publishing_rights.publishing_rights | see application form Q54 - https://doaj.org/application/new#publishing_rights-container | unicode |  |  |
| bibjson.author_publishing_rights.url | see application form Q55 - https://doaj.org/application/new#publishing_rights_url-container | unicode | URL |  |
| bibjson.country | see application form Q12 - https://doaj.org/application/new#country-container | unicode |  |  |
| bibjson.deposit_policy | see application form Q51 - https://doaj.org/application/new#deposit_policy-container | unicode |  |  |
| bibjson.editorial_review.process | see application form Q37 - https://doaj.org/application/new#review_process-container | unicode |  | Editorial review, Peer review, Blind peer review, Double blind peer review, Open peer review, None |
| bibjson.editorial_review.url | see application form Q38 - https://doaj.org/application/new#review_process_url-container | unicode | URL |  |
| bibjson.format | see application form Q33: https://doaj.org/application/new#fulltext_format-container | unicode |  |  |
| bibjson.identifier.id | The ISSN(s) of the journal.  Related bibjson.identifier.type must be "pissn" or "eissn" as needed. | unicode |  |  |
| bibjson.identifier.type | The identifier type.  Should be one of "pissn" or "eissn" | unicode |  |  |
| bibjson.institution | as per application form Q7 - https://doaj.org/application/new#society_institution-container | unicode |  |  |
| bibjson.keywords | as per application form Q34 - https://doaj.org/application/new#keywords-container | unicode |  |  |
| bibjson.language | as per application form Q35 - https://doaj.org/application/new#languages-container | unicode | 2 letter ISO language code |  |
| bibjson.license.BY | Does the licence have an attribution clause. | bool |  |  |
| bibjson.license.NC | Does the licence have a non-commercial clause. | bool |  |  |
| bibjson.license.ND | Does the licence have a no-derivatives clause. | bool |  |  |
| bibjson.license.SA | Does the licence have a share-alike clause. | bool |  |  |
| bibjson.license.embedded | See application form Q45 - https://doaj.org/application/new#license_embedded-container | bool |  |  |
| bibjson.license.embedded_example_url | See application form Q46 - https://doaj.org/application/new#license_embedded_url-container | unicode | URL |  |
| bibjson.license.open_access | see application form Q50 - https://doaj.org/application/new#open_access-container | bool |  |  |
| bibjson.license.title | The name of the licence | unicode |  |  |
| bibjson.license.type | The licence type from application form Q47 - https://doaj.org/application/new#license-container | unicode |  |  |
| bibjson.license.url | see application form Q49 - https://doaj.org/application/new#license_url-container | unicode | URL |  |
| bibjson.license.version | Licence version, if known. | unicode |  |  |
| bibjson.link.type | name of the type of link in bibjson.link.url.  Allowed values and related application form questions are: "homepage" (Q2), "waiver_policy" (Q24), "editorial_board" (Q36), "aims_scope" (Q39), "author_instructions" (Q40), "oa_statement" (Q44) | unicode |  |  |
| bibjson.link.url | url associated with bibjson.link.type | unicode | URL |  |
| bibjson.oa_end.number | final issue number published Open Access.  **Deprecated** | int |  |  |
| bibjson.oa_end.volume | final volume number published Open Access.  **Deprecated** | int |  |  |
| bibjson.oa_end.year | final year published Open Access.  **Deprecated** | int |  |  |
| bibjson.oa_start.number | first issue published Open Access.  **Deprecated** | int |  |  |
| bibjson.oa_start.volume | first volume published Open Access.  **Deprecated** | int |  |  |
| bibjson.oa_start.year | see application form Q32 - https://doaj.org/application/new#first_fulltext_oa_year-container | int |  |  |
| bibjson.persistent_identifier_scheme | see application form Q28 - https://doaj.org/application/new#article_identifiers-container | unicode |  |  |
| bibjson.plagiarism_detection.detection | see application form Q41 - https://doaj.org/application/new#plagiarism_screening-container | bool |  |  |
| bibjson.plagiarism_detection.url | see application form Q42 - https://doaj.org/application/new#plagiarism_screening_url-container | unicode | URL |  |
| bibjson.provider | see application form Q8 - https://doaj.org/application/new#platform-container | unicode |  |  |
| bibjson.publication_time | see application form Q43 - https://doaj.org/application/new#publication_time-container | int |  |  |
| bibjson.publisher | see application form Q6 - https://doaj.org/application/new#publisher-container | unicode |  |  |
| bibjson.subject.code | assigned subject code | unicode |  |  |
| bibjson.subject.scheme | assigned subject scheme | unicode |  |  |
| bibjson.subject.term | assigned subject term | unicode |  |  |
| bibjson.submission_charges.average_price | see application form Q19 - https://doaj.org/application/new#submission_charges_amount-container | int |  |  |
| bibjson.submission_charges.currency | see application form Q20 - https://doaj.org/application/new#submission_charges_currency-container | unicode |  |  |
| bibjson.submission_charges_url | see application form Q18 - https://doaj.org/application/new#submission_charges_url-container | unicode | URL |  |
| bibjson.title | see application form Q1 - https://doaj.org/application/new#title-container | unicode |  |  |
| created_date | Date the record was created in DOAJ. | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| id | ID assigned by DOAJ for the record. | unicode |  |  |
| last_updated | Date the record was last updated in DOAJ. | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
