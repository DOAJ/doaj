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
                "name": "string"
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
            "license": [
                {
                    "open_access": true, 
                    "title": "string", 
                    "type": "string", 
                    "url": "string", 
                    "version": "string"
                }
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
    "created_date": "2019-05-14T11:15:40Z", 
    "id": "string", 
    "last_updated": "2019-05-14T11:15:40Z"
}
```

Each of the fields is defined as laid out in the table below.  All fields are optional unless otherwise specified:

| Field | Description | Datatype | Format | Allowed Values |
| ----- | ----------- | -------- | ------ | -------------- |
| admin.in_doaj | Whether the article is in DOAJ, or withdrawn from public view.  You can retrieve this value from DOAJ, but if you provide it back it will be **ignored**. | bool |  |  |
| admin.publisher_record_id | **Deprecated** Your own ID for the record. | unicode |  |  |
| admin.seal | Whether the article is in a journal with the DOAJ Seal.  You can retrieve this value from DOAJ, but if you provide it back it will be **ignored**. | bool |  |  |
| admin.upload_id | An ID for a batch upload.  You can retrieve this value from DOAJ, but if you provide it back it will be **ignored**. | unicode |  |  |
| bibjson.abstract | Article abstract | unicode |  |  |
| bibjson.author.affiliation | An author's affiliation | unicode |  |  |
| bibjson.author.name | An author's name.  If there is an author record then name is **required** | unicode |  |  |
| bibjson.identifier.id | An identifier for the article. | unicode |  |  |
| bibjson.identifier.type | The type of the associated identifier.  Should contain "doi" if available.  An "eissn" or a "pissn" is **required**. | unicode |  |  |
| bibjson.journal.country | The country of the publisher using the ISO-3166 2-letter country codes.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| bibjson.journal.end_page | End page of the article in the journal | unicode |  |  |
| bibjson.journal.language | The language of the Journal using the ISO-639-1 2-letter language codes.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| bibjson.journal.license.open_access | Is the parent journal Open Access? You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | bool |  |  |
| bibjson.journal.license.title | The name of the licence of the parent journal. You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| bibjson.journal.license.type | The type of the licence of the parent journal.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| bibjson.journal.license.url | The URL for the licence terms of the parent journal.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| bibjson.journal.license.version | The version of the licence terms of the parent journal.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| bibjson.journal.number | The issue number of the journal within which this article appears | unicode |  |  |
| bibjson.journal.publisher | The name of the publisher of the journal.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| bibjson.journal.start_page | The start page of the article in the journal | unicode |  |  |
| bibjson.journal.title | The journal title. You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| bibjson.journal.volume | The volume of the journal within which this article appears | unicode |  |  |
| bibjson.keywords | Up to 6 free-text keywords describing this article | unicode |  |  |
| bibjson.link.content_type | The content type of page referenced by the link (for example, text/html) | unicode |  |  |
| bibjson.link.type | The link type.  Should contain "fulltext" and point to the article fulltext URL in bibjson.link.url | unicode |  |  |
| bibjson.link.url | The url | unicode | URL |  |
| bibjson.month | Month of publication for this article | unicode |  |  |
| bibjson.subject.code | Library of Congress Subject Code.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| bibjson.subject.scheme | Library of Congress Subject Scheme.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| bibjson.subject.term | Library of Congress Subject Term.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| bibjson.title | Article title **required** | unicode |  |  |
| bibjson.year | Year of publication for this article | unicode |  |  |
| created_date | Date the record was created in DOAJ. You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
| id | DOAJ ID for this article.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode |  |  |
| last_updated | Date this article was last modified in DOAJ.  You can retrieve this value from DOAJ, and it will be **populated for you** when an article is created | unicode | UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ |  |
