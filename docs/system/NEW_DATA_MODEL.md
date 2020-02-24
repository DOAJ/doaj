An overall data model covering both journals and applications.

One type may have some admin fields and not others and vice versa.

```json
{
    "id" : "id",
    "created_date" :  "created date",
    "last_manual_update" : "last manual edit",
    "last_update" : "last update of any kind",
    "admin": {
        "application_status" : "status",
        "bulk_upload": "string", 
        "contact": [
            {
                "email": "string", 
                "name": "string"
            }
        ], 
        "current_journal" : "string",
        "current_application": "string", 
        "editor": "string", 
        "editor_group": "string", 
        "in_doaj": true, 
        "notes": [
            {
                "id" : "<note id>",
                "date": "2018-01-25T09:45:44Z", 
                "note": "string"
            }
        ], 
        "owner": "string", 
        "related_journal" : "string",
        "related_applications": [
            {
                "application_id": "string", 
                "date_accepted": "2018-01-25T09:45:44Z", 
                "status": "string"
            }
        ], 
        "seal": true, 
        "ticked": true,
        "suggested_on" : "date suggested",
        "suggester": {
            "email": "string", 
            "name": "string"
        }
    }, 
    "bibjson" : {
        "alternative_title" : "Alt",
        "apc" : {
            "has_apc" : true,
            "max" : [
                {"currency" : "GBP", "price" :  1000}
            ],
            "url" : "<apc url>"
        },
        "article" : {
            "embedded_license": true,
            "embedded_license_example" : "<example url>",
            "orcid" : true
        },
        "boai" : true,
        "copyright" : {
            "author_retains" : true,
            "url" : "<terms url>"
        },
        "deposit_policy" : {
            "has_policy" : true,
            "is_registered" : true,
            "service" : ["<service name>"]
        },
        "discontinued_date" : "<date>",
        "editorial" : {
            "review_process" : ["<review process>"],
            "review_url" : "<editorial review url>",
            "board_url" : "<editorial board url>"
        },
        "eissn" : "<eissn>",
        "is_replaced_by" : ["<issn>"],
        "institution" : {
            "name" : "Institution",
            "country" : "institution country"
        },
        "keywords" : ["<keyword>"],
        "language" : ["<language code>"],
        "license" : [
            {
                "type" : "CC BY",
                "BY" : true,
                "NC" : true,
                "ND" : true,
                "SA" : true,
                "url" : "<licence terms url>"
            }
        ],
        "other_charges" : {
            "has_other_charges" : true,
            "url" : "<other charges url>"
        },
        "pid_scheme" : {
            "has_pid_scheme" : true,
            "scheme" : ["<scheme name>"]
        },
        "pissn" : "<pissn>",
        "plagiarism" : {
            "detection" : true,
            "url" : "<plagiarism url>"
        },
        "preservation" : {
            "has_preservation" : true,
            "service" : ["<service name>"],
            "national_library" : "National Library Name",
            "other" : "<service name>",
            "url" : "<preservation url>"
        },
        "publication_time_weeks" : 5,
        "publisher" : {
            "name" : "publisher",
            "country" : "publisher country"
        },
        "ref" : {
            "oa_statement" : "<oa_statement url>",
            "journal" : "<journal url>",
            "aims_scope" : "<aims/scope url>",
            "author_instructions" : "<author instructions url>",
            "license_terms" : "<license terms url>"
        },
        "replaces" : [],
        "subject" : [
            {
                "code": "string", 
                "scheme": "string", 
                "term": "string"
            }
        ],
        "title" : "Title",
        "waiver" : {
            "has_waiver" : true,
            "url" : "<waiver policy url>"
        }
    },
    "index": {
        "asciiunpunctitle": "string", 
        "classification": [
            "string"
        ], 
        "classification_paths": [
            "string"
        ], 
        "continued": "string",
        "country" : "string", 
        "has_editor": "string", 
        "has_editor_group": "string", 
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
        "unpunctitle": "string"
    }
}
```