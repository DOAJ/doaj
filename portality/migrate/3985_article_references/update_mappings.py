from portality.models import Article
from portality.core import initialise_index, app, es_connection

initialise_index(app, es_connection, only_mappings=[Article.__type__], force_mappings=True)
