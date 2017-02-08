# DOAJ Data Models

## Data Objects

* Journal - docs/system/Journal.md
* Suggestion (aka Application) - docs/system/Suggestion.md

## Other Models

### Article

```python
{
    "id" : "<some opaque identifier>",
    "admin" : {
        "in_doaj" : true|false,
        "publisher_record_id" : "<publisher identifier for item>",
        "upload_id" : "<opaque identifier>"
    },
    "bibjson" : {
        "title" : "<title of the article>",
        "identifier": [
            {"type" : "doi", "id" : "<doi>"},
            {"type" : "pissn", "id" : "<print issn>"},
            {"type" : "eissn", "id" : "<electronic issn>"}
            {"type" : "eissn", "id" : "<electronic issn>"}
        ],
        "journal" : {
            "volume" : "journal volume number",
            "number" : "journal issue number",
            "publisher" : "<publisher>",
            "title" : "<journal title (taken from journal record)>"
            "license" : [
                {
                    "title" : "<name of licence>",
                    "type" : "<type>", 
                    "url" : "<url>", 
                    "version" : "<version>",
                    "open_access": true|false,
                }
            ],
            "language" : "[list of journal's languages]",
            "country" : "<country of publication>",
            "issn" : "<issn from journal.bibjson().get_preferred_issn() (taken from journal record)>",
        },
        "year" : "<year of publication>",
        "month" : "<month of publicaiton>",
        "start_page" : "<start page>",
        "end_page" : "<end page>",
        "link" : [
            {
                "url" : "<fulltext url>",
                "type" : "fulltext",
                "content_type" : "<content type of resource>"
            }
        ],
        "abstract" : "<the abstract>",
        "author" : [
            {
                "name" : "<author name>",
                "email" : "<author email>",
                "affiliation" : "<author affiliation>"
            },
        ],
        "keywords" : [<list of free text keywords>],
        "subject" : [
            {
                "scheme" : "<scheme>", 
                "term" : "<term>",
                "code" : "<code>"
            }
        ],
    },
    "history" : [
        {
            "date" : "<date history record created>",
            "bibjson" : { <historic bibjson record> }
        }
    ]
    "index" : {
        "date" : "<date of publication>"
        "date_toc_fv_month" : "<date of publication (duplicated for ToC facetview)>"
        "issn" : [<list of all issns that this item pertains to>],
        "subject" : [<all possible subject keywords>],
        "schema_subject" : [<all subject keywords with schema prefixes>],
        "schema_code" : [<list of subject codes with schema prefixes>]
        "classification" : [<list of classification terms without prefixes>],
        "language" : [<list of languages of the journal>],
        "country" : "<country of journal publication>",
        "license" : [<list of titles of licences>],
        "publisher" : "<publisher>",
        "classification_paths" : [<list of all expanded LCC terms, with parents>],
        "unpunctitle" : "<title without punctuation>",
        "asciiunpunctitle" : "<ascii-folded title without puncuation>"
    },
    "created_date" : "<date created>",
    "last_updated" : "<date record last modified>"
}
```


### Account

```python
{
    "id" : "<the username of the user>",
    "password" : "<hashed password>",
    "name" : "<user's actual name>",
    "email" : "<user's email address>",
    "role" : [<list of user roles>],
    "journal" : [<list of journal ids the user can administer>],
    "api_key" : "<32 character-long hexadecimal key to access API>"
}
```

### File Upload
```python
{
    "id": "<opaque id of upload>",
    "status": "incoming|validated|failed|processed",
    "last_updated": "<last date modified>",
    "created_date": "<date of initial upload>",
    "owner": "<user id of owner>",
    "schema": "<metadata scheme used>",
    "filename": "<filename of upload>",
    "error" : "<any error associated with the upload>"
}
```

## Edit Lock Data Model

```python
{
    "id" : "<opaque id for this lock>",
    "about" : "<opaque id for the journal/suggestion to which it applies>",
    "type" : "<journal/suggestion>",
    "created_date" : "<timestamp this lock record was created>",
    "expires" : "<timestamp for when this lock record expires>",
    "username" : "<user name of the user who holds the lock>"
}
```

## Editor Group Data Model

```python
{
    "id" : "<opaque id for this editor group>",
    "name" : "<human readable name for this editor group>",
    "editor" : "<username of editor which runs this group>",
    "associates" : ["<associate who is part of this group>"],
    "created_date" : "<timestamp for when this group was created>",
    "last_updated" : "<timestamp for when this group was last modified>"
}
```

## Bulk Reapplication Data Model

```python
{
    "id" : "<opaque id for this bulk reapplication>",
    "owner" : "<user account which owns this reapplication>",
    "spreadsheet_name" : "<name by which the spreadsheet is known (both locally and for download)>",
    "created_date" : "<timestamp for when this spreadsheet was created>",
    "last_updated" : "<timestamp for when this spreadsheet was last modified>"
}
```

## Bulk Upload Data Model

```python
{
    "id" : "<opaque id for this bulk upload>",
    "status": "incoming|failed|processed",
    "owner": "<user id of owner>",
    "filename": "<filename of upload>",
    "error" : "<any error associated with the upload>"
    "reapplied" : <number of reapplications processed from this upload>,
    "skipped" : <number of reapplications skipped in this upload>,
    "last_updated": "<last date modified>",
    "created_date": "<date of initial upload>",
    "processed_date": "<date the upload was processed>"
}
```

Note: Editor group names need to be unique within the index
