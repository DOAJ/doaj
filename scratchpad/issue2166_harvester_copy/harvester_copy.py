import esprit
from portality.core import initialise_index, app


conn = esprit.raw.Connection(host='http://localhost:9200', index='doaj')

print('Deleting the new harvester type \'harvester_state\' and its erroneous data')
esprit.raw.delete(conn, type='harvester_state')

print('Initialising the index to re-create the mapping for \'harvester_state\'')
initialise_index(app)

print('Copying all data from \'state\' to \'harvester_state\'')
esprit.tasks.copy(source_conn=conn, source_type='state', target_conn=conn, target_type='harvester_state')
