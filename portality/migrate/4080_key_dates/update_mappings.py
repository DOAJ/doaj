from portality.models import Journal, Application
from portality.core import initialise_index, app, es_connection

initialise_index(app, es_connection, only_mappings=[Journal.__type__, Application.__type__], force_mappings=True)