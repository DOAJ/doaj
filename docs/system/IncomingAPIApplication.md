# IncomingApplication

The JSON structure of the model is as follows:

```json
{
    "admin": {
        "application_status": "string", 
        "contact": [
            {
                "email": "string", 
                "name": "string"
            }
        ], 
        "current_journal": "string", 
        "owner": "string"
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
        "oa_start": {
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
    "created_date": "2019-06-28T15:19:17Z", 
    "id": "string", 
    "last_updated": "2019-06-28T15:19:17Z", 
    "suggestion": {
        "article_metadata": true, 
        "articles_last_year": {
            "count": 0, 
            "url": "string"
        }, 
        "suggested_on": "2019-06-28T15:19:17Z", 
        "suggester": {
            "email": "string", 
            "name": "string"
        }
    }
}
```

Each of the fields is defined as laid out in the table below.  All fields are optional unless otherwise specified:

| Field | Description | Datatype | Format | Allowed Values |
| ----- | ----------- | -------- | ------ | -------------- |
| admin.application_status | Status of the application.  If provided, will be ignored | unicode |  |  |
| admin.contact.email | Email address of the contact for this application | unicode |  |  |
| admin.contact.name | Name for the contact for this application | unicode |  |  |
| admin.current_journal | ID of a journal that you would like to request an update for | unicode |  |  |
| admin.owner | Your user account ID.  If provided, will be ignored and overridden by the account ID related to the API key | unicode |  |  |
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
| bibjson.license.BY | Does the licence have an attribution clause.  You may omit if using one of the defined licence types in application form Q47 - https://doaj.org/application/new#license-container | bool |  |  |
| bibjson.license.NC | Does the licence have a non-commercial clause.  You may omit if using one of the defined licence types in application form Q47 - https://doaj.org/application/new#license-container | bool |  |  |
| bibjson.license.ND | Does the licence have a no-derivatives clause.  You may omit if using one of the defined licence types in application form Q47 - https://doaj.org/application/new#license-container | bool |  |  |
| bibjson.license.SA | Does the licence have a share-alike clause.  You may omit if using one of the defined licence types in application form Q47 - https://doaj.org/application/new#license-container | bool |  |  |
| bibjson.license.embedded | See application form Q45 - https://doaj.org/application/new#license_embedded-container | bool |  |  |
| bibjson.license.embedded_example_url | See application form Q46 - https://doaj.org/application/new#license_embedded_url-container | unicode | URL |  |
| bibjson.license.open_access | see application form Q50 - https://doaj.org/application/new#open_access-container | bool |  |  |
| bibjson.license.title | The name of the licence, which you can leave blank unless it is "other" as per application form Q47 - https://doaj.org/application/new#license-container | unicode |  |  |
| bibjson.license.type | The licence type from application form Q47 - https://doaj.org/application/new#license-container | unicode |  |  |
| bibjson.license.url | see application form Q49 - https://doaj.org/application/new#license_url-container | unicode | URL |  |
| bibjson.license.version | Will be ignored if provided at this point in time | unicode |  |  |
| bibjson.link.type | name of the type of link in bibjson.link.url.  Allowed values and related application form questions are: "homepage" (Q2), "waiver_policy" (Q24), "editorial_board" (Q36), "aims_scope" (Q39), "author_instructions" (Q40), "oa_statement" (Q44) | unicode |  |  |
| bibjson.link.url | url associated with bibjson.link.type | unicode | URL |  |
| bibjson.oa_start.year | see application form Q32 - https://doaj.org/application/new#first_fulltext_oa_year-container | int |  |  |
| bibjson.persistent_identifier_scheme | see application form Q28 - https://doaj.org/application/new#article_identifiers-container | unicode |  |  |
| bibjson.plagiarism_detection.detection | see application form Q41 - https://doaj.org/application/new#plagiarism_screening-container | bool |  |  |
| bibjson.plagiarism_detection.url | see application form Q42 - https://doaj.org/application/new#plagiarism_screening_url-container | unicode | URL |  |
| bibjson.provider | see application form Q8 - https://doaj.org/application/new#platform-container | unicode |  |  |
| bibjson.publication_time | see application form Q43 - https://doaj.org/application/new#publication_time-container | int |  |  |
| bibjson.publisher | see application form Q6 - https://doaj.org/application/new#publisher-container | unicode |  |  |
| bibjson.subject.code | assigned subject code, will be ignored if provided | unicode |  |  |
| bibjson.subject.scheme | assigned subject scheme, will be ignored if provided | unicode |  |  |
| bibjson.subject.term | assigned subject term, will be ignored if provided | unicode |  |  |
| bibjson.submission_charges.average_price | see application form Q19 - https://doaj.org/application/new#submission_charges_amount-container | int |  |  |
| bibjson.submission_charges.currency | see application form Q20 - https://doaj.org/application/new#submission_charges_currency-container | unicode |  |  |
| bibjson.submission_charges_url | see application form Q18 - https://doaj.org/application/new#submission_charges_url-container | unicode | URL |  |
| bibjson.title | see application form Q1 - https://doaj.org/application/new#title-container | unicode |  |  |
| created_date | Date the record was created in DOAJ.  Will be ignored if provided. | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| id | ID assigned by DOAJ for the record.  Will be ignored if provided | unicode |  |  |
| last_updated | Date the record was last updated in DOAJ.  Will be ignored if provided. | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| suggestion.article_metadata | see application form Q29 - https://doaj.org/application/new#metadata_provision-container | bool |  |  |
| suggestion.articles_last_year.count | see application form Q21 - https://doaj.org/application/new#articles_last_year-container | int |  |  |
| suggestion.articles_last_year.url | see application form Q22 - https://doaj.org/application/new#articles_last_year_url-container | unicode | URL |  |
| suggestion.suggested_on | Date the application was made to DOAJ.  Will be ignored if provided | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| suggestion.suggester.email | see application form Q57 - https://doaj.org/application/new#suggester_email-container | unicode |  |  |
| suggestion.suggester.name | see application form Q56 - https://doaj.org/application/new#suggester_name-container | unicode |  |  |
