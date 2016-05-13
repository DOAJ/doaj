from portality.core import app
import esprit

nm = {
    "properties" : {
        "bibjson" : {
            "properties" : {
                "discontinued_date" : {
                    "type" : "date",
                    "format" : "dateOptionalTime"
                }
            }
        }
    }
}

conn = esprit.raw.Connection(app.config.get("ELASTIC_SEARCH_HOST"), app.config.get("ELASTIC_SEARCH_DB"))
esprit.raw.put_mapping(conn, "journal", nm, es_version=app.config.get("ELASTIC_SEARCH_VERSION", "1.7.5"))
