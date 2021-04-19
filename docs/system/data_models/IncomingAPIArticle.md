# IncomingArticleDO

The JSON structure of the model is as follows:

```json
{
    "admin": {
        "in_doaj": true,
        "publisher_record_id": "string",
        "seal": true,
        "upload_id": "string"
    },
    "bibjson": {
        "abstract": "string",
        "author": [
            {
                "affiliation": "string",
                "name": "string",
                "orcid_id": "string"
            }
        ],
        "identifier": [
            {
                "id": "string",
                "type": "string"
            }
        ],
        "journal": {
            "country": "string",
            "end_page": "string",
            "language": [
                "string"
            ],
            "number": "string",
            "publisher": "string",
            "start_page": "string",
            "title": "string",
            "volume": "string"
        },
        "keywords": [
            "string"
        ],
        "link": [
            {
                "content_type": "string",
                "type": "string",
                "url": "string"
            }
        ],
        "month": "string",
        "subject": [
            {
                "code": "string",
                "scheme": "string",
                "term": "string"
            }
        ],
        "title": "string",
        "year": "string"
    },
    "created_date": "2021-04-16T12:49:44Z",
    "es_type": "string",
    "id": "string",
    "last_updated": "2021-04-16T12:49:44Z"
}
```

Each of the fields is defined as laid out in the table below.  All fields are optional unless otherwise specified:

| Field | Description | Datatype | Format | Allowed Values |
| ----- | ----------- | -------- | ------ | -------------- |
| admin.in_doaj | Whether the article is in DOAJ, or withdrawn from public view.  You can retrieve this value from DOAJ, but if you provide it back it will be **ignored**. | bool |  |  |
| admin.publisher_record_id | **Deprecated** Your own ID for the record. | str |  |  |
| admin.seal | Whether the article is in a journal with the DOAJ Seal.  You can retrieve this value from DOAJ, but if you provide it back it will be **ignored**. | bool |  |  |
| admin.upload_id | An ID for a batch upload.  You can retrieve this value from DOAJ, but if you provide it back it will be **ignored**. | str |  |  |
| bibjson.abstract | Article abstract | str |  |  |
| bibjson.author.affiliation | An author's affiliation | str |  |  |
| bibjson.author.name | An author's name.  If there is an author record then name is **required** | str |  |  |
| bibjson.author.orcid_id |  | str |  |  |
| bibjson.identifier.id | An identifier for the article. | str |  |  |
| bibjson.identifier.type | The type of the associated identifier.  Should contain "doi" if available.  An "eissn" or a "pissn" is **required**. | str |  |  |
| bibjson.journal.country | The country of the publisher using the ISO-3166 2-letter country codes.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | str |  |  |
| bibjson.journal.end_page | End page of the article in the journal | str |  |  |
| bibjson.journal.language | The language of the Journal using the ISO-639-1 2-letter language codes.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | str |  |  |
| bibjson.journal.number | The issue number of the journal within which this article appears | str |  |  |
| bibjson.journal.publisher | The name of the publisher of the journal.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | str |  |  |
| bibjson.journal.start_page | The start page of the article in the journal | str |  |  |
| bibjson.journal.title | The journal title. You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | str |  |  |
| bibjson.journal.volume | The volume of the journal within which this article appears | str |  |  |
| bibjson.keywords | Up to 6 free-text keywords describing this article | str |  |  |
| bibjson.link.content_type | The content type of page referenced by the link (for example, text/html) | str |  |  |
| bibjson.link.type | The link type.  Should contain "fulltext" and point to the article fulltext URL in bibjson.link.url | str |  |  |
| bibjson.link.url | The url | str | URL |  |
| bibjson.month | Month of publication for this article | str |  |  |
| bibjson.subject.code | Library of Congress Subject Code.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | str |  |  |
| bibjson.subject.scheme | Library of Congress Subject Scheme.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | str |  |  |
| bibjson.subject.term | Library of Congress Subject Term.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | str |  |  |
| bibjson.title | Article title **required** | str |  |  |
| bibjson.year | Year of publication for this article | str |  |  |
| created_date | Date the record was created in DOAJ. You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | str | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| es_type |  | str |  |  |
| id | DOAJ ID for this article.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | str |  |  |
| last_updated | Date this article was last modified in DOAJ.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | str | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
