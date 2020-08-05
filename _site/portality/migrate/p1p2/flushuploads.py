# drop and re-create the upload type in the index, for use in tracking
# file uploads

import requests
from portality.core import app, initialise_index

upload_url = app.config.get("ELASTIC_SEARCH_HOST") + "/" + app.config.get("ELASTIC_SEARCH_DB") + "/upload"

# delete the index.  We can't just empty it, as we want to reset the mappings too
requests.delete(upload_url)

# just re-initialise the whole index; this will only re-create types that don't already exist
initialise_index(app)
