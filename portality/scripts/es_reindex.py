# ~~ESReindex:CLI~~
"""
This script is useful to create new index with any new mapping changes if applicable and copy the content from old index to new index
run the script:
portality/scripts/es_reindex.py <json file path>
ex:
portality/scripts/es_reindex.py -u <full path>/portality/migrate/3575_make_notes_searchable/migrate.json

example json file:
{
	"new_version": "-20231109", #new index version
	"old_version": "-20230901", #old index version
	"types": [
		{
			"type" : "application", #model type
			"migrate": true,  #if migration required true or false
			"set_alias": false #set to true if alias has to be set with base name ex: doaj-application
		},
		{
			"type": "journal",
			"migrate": true,
			"set_alias": false
		}
	]
}
"""

import json
import time
import elasticsearch
from elasticsearch import helpers
from elasticsearch.exceptions import NotFoundError, RequestError, ConnectionError, AuthorizationException

from portality.core import app
from portality.lib import es_data_mapping


def do_import(config):
    # create a connection with timeout
    es_connection = elasticsearch.Elasticsearch(app.config['ELASTICSEARCH_HOSTS'],
                                                verify_certs=app.config.get("ELASTIC_SEARCH_VERIFY_CERTS", True),
                                                timeout=60*10)

    # get the versions
    version = config.get("new_version")
    previous_version = config.get("old_version")

    # get the types we are going to work with
    print("==Carrying out the following import==")
    for s in config.get("types", []):
        if s.get("migrate", False) is True:
            print(s.get("type"))

    print("\n")

    text = input("Continue? [y/N] ")
    if text.lower() != "y":
        exit()

    # get all available mappings
    mappings = es_data_mapping.get_mappings(app)

    # Iterate through the types then
    # 1. create new index
    # 2. re index with old index
    # 3. set alias for new index
    for s in config.get("types", []):
        import_type = s["type"]
        if import_type in mappings:

            # index names
            default_index_name = app.config['ELASTIC_SEARCH_DB_PREFIX'] + import_type
            new_index = default_index_name + version
            old_index = default_index_name + previous_version

            if not es_connection.indices.exists(new_index):
                try:
                    # create new index
                    r = es_connection.indices.create(index=new_index, body=mappings[import_type])
                    print("Creating ES Type + Mapping in index {0} for {1}; status: {2}".format(new_index, import_type, r))

                    # reindex from the old index
                    print("Reindexing from {0} to {1}".format(old_index, new_index))
                    retry_count = 0
                    max_retries = 5
                    success = False
                    while not success and retry_count < max_retries:
                        try:
                            result, errors = helpers.reindex(client=es_connection, source_index=old_index,
                                                            target_index=new_index)
                            if errors:
                                print(f"Some documents failed to reindex: {import_type}", errors)
                            else:
                                success = True
                                print(f"Reindex completed successfully: {import_type}", result)
                                # add alias
                                if s.get("set_alias", False):
                                    es_connection.indices.put_alias(index=new_index, name=default_index_name)
                                    print("alias set for {0} as {1}".format(new_index, default_index_name))
                                else:
                                    print("alias not set for {0}".format(new_index))
                        except ConnectionError:
                            retry_count += 1
                            print(f"Timeout occurred, retrying {retry_count}/{max_retries}")
                            time.sleep(10)  # Wait for 10 seconds before retrying

                    if not success:
                        print("Failed to complete the reindexing after several retries.")

                except ConnectionError as e:
                    print(f"Failed to connect to Elasticsearch server. {e.info}")
                except NotFoundError as e:
                    print(f"The specified index or alias does not exist. {e.info}")
                except RequestError as e:
                    print(f"Bad request: {e.info}")
                except AuthorizationException as e:
                    print(f"You do not have permission to perform this operation. {e.info}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
            else:
                print("ES Type + Mapping already exists in index {0} for {1}".format(new_index, import_type))


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("config", help="Config file path to migrate")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.loads(f.read())

    do_import(config)