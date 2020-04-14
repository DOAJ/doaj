import esprit, requests
from portality.core import app, es_connection, initialise_index

initialise_index(app, es_connection)

live = esprit.raw.Connection(app.config.get("DOAJGATE_URL"), "doaj", auth=requests.auth.HTTPBasicAuth(app.config.get("DOAJGATE_UN"), app.config.get("DOAJGATE_PW")), verify_ssl=False, port=app.config.get("DOAJGATE_PORT"))
local = esprit.raw.Connection(app.config.get("ELASTIC_SEARCH_HOST"), app.config.get("ELASTIC_SEARCH_DB"))

esprit.tasks.copy(live, "account", local, "account", method="GET")
esprit.tasks.copy(live, "journal", local, "journal", method="GET")
esprit.tasks.copy(live, "suggestion", local, "suggestion", method="GET")
esprit.tasks.copy(live, "article", local, "article", limit=100000, method="GET")
esprit.tasks.copy(live, "editor_group", local, "editor_group", method="GET")