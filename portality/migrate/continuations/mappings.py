from portality.core import app, es_connection
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

esprit.raw.put_mapping(es_connection, "journal", nm, es_version=app.config.get("ELASTIC_SEARCH_VERSION", "1.7.5"))
