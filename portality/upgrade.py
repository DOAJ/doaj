"""
~~Migrations:Framework~~
# FIXME: this script requires more work if it's to be used for specified source and target clusters
"""
import json, os, dictdiffer
import logging
from datetime import datetime, timedelta
from copy import deepcopy
from collections import OrderedDict
from portality import models
from portality.dao import ScrollTimeoutException
from portality.lib import plugin
from portality.lib.dataobj import DataStructureException
from portality.lib.seamless import SeamlessException
from portality.dao import ScrollTimeoutException

MODELS = {
    "journal": models.Journal,  #~~->Journal:Model~~
    "article": models.Article,  #~~->Article:Model~~
    "suggestion": models.Suggestion,    #~~->Application:Model~~
    "application": models.Application,
    "account": models.Account,   #~~->Account:Model~~
    "background_job": models.BackgroundJob  #~~->BackgroundJob:Model~~
}

log = logging.getLogger(__name__)


class UpgradeTask(object):

    def upgrade_article(self, article):
        pass


def do_upgrade(definition, verbose, save_batches=None):
    """
    :param definition:
        * init_with_model: record index will be re-generated on save if true
        * keepalive: keepalive time of ES connection (e.g. 1m, 20m)
        * batch: size of save or model_class.bulk
        * scroll_size: size of ES query
    :param verbose:
    :param save_batches:
    :return:
    """
    # get the source and target es definitions
    # ~~->Elasticsearch:Technology~~

    # get the defined batch size
    batch_size = definition.get("batch", 500)

    for tdef in definition.get("types", []):
        print("Upgrading", tdef.get("type"))
        batch = []
        total = 0
        batch_num = 0
        type_start = datetime.now()

        default_query = {
            "query": {"match_all": {}}
        }

        # learn what kind of model we've got
        model_class = MODELS.get(tdef.get("type"))
        max = model_class.count()
        action = tdef.get("action", "update")

        # Iterate through all of the records in the model class
        try:
            for result in model_class.iterate(q=tdef.get("query", default_query), keepalive=tdef.get("keepalive", "1m"), page_size=tdef.get("scroll_size", 1000), wrap=False):

                original = deepcopy(result)
                if tdef.get("init_with_model", True):
                    # instantiate an object with the data
                    try:
                        result = model_class(**result)
                    except (DataStructureException, SeamlessException) as e:
                        print("Could not create model for {0}, Error: {1}".format(result['id'], str(e)))
                        continue

                for function_path in tdef.get("functions", []):
                    fn = plugin.load_function(function_path)
                    result = fn(result)
                    if result is None:
                        log.warning('WARNING! return of [functions] should not None')

                data = result
                _id = result.get("id", "id not specified")
                if isinstance(result, model_class):
                    # run the tasks specified with this object type
                    tasks = tdef.get("tasks", None)
                    if tasks:
                        for func_call, kwargs in tasks.items():
                            getattr(result, func_call)(**kwargs)

                    # run the prep routine for the record
                    try:
                        result.prep()
                    except AttributeError:
                        if verbose:
                            print(tdef.get("type"), result.id, "has no prep method - no, pre-save preparation being done")
                        pass

                    data = result.data
                    _id = result.id

                # add the data to the batch
                if action == 'update':
                    data = _diff(original, data)

                if "id" not in data:
                    data["id"] = _id

                batch.append(data)
                if verbose:
                    print("added", tdef.get("type"), _id, "to batch update")

                # When we have enough, do some writing
                if len(batch) >= batch_size:
                    total += len(batch)
                    batch_num += 1

                    print(datetime.now(), "writing ", len(batch), "to", tdef.get("type"), ";", total, "of", max)

                    if save_batches:
                        fn = os.path.join(save_batches, tdef.get("type") + "." + str(batch_num) + ".json")
                        with open(fn, "w") as f:
                            f.write(json.dumps(batch, indent=2))
                            print(datetime.now(), "wrote batch to file {x}".format(x=fn))

                    model_class.bulk(batch, action=action, req_timeout=120)
                    batch = []
                    # do some timing predictions
                    batch_tick = datetime.now()
                    time_so_far = batch_tick - type_start
                    seconds_so_far = time_so_far.total_seconds()
                    estimated_seconds_remaining = ((seconds_so_far * max) / total) - seconds_so_far
                    estimated_finish = batch_tick + timedelta(seconds=estimated_seconds_remaining)
                    print('Estimated finish time for this type {0}.'.format(estimated_finish))
        except ScrollTimeoutException:
            # Try to write the part-batch to index
            if len(batch) > 0:
                total += len(batch)
                batch_num += 1

                if save_batches:
                    fn = os.path.join(save_batches, tdef.get("type") + "." + str(batch_num) + ".json")
                    with open(fn, "w") as f:
                        f.write(json.dumps(batch, indent=2))
                        print(datetime.now(), "wrote batch to file {x}".format(x=fn))

                print(datetime.now(), "scroll timed out / writing ", len(batch), "to", tdef.get("type"), ";", total, "of", max)
                model_class.bulk(batch, action=action, req_timeout=120)
                batch = []

        # Write the last part-batch to index
        if len(batch) > 0:
            total += len(batch)
            batch_num += 1

            if save_batches:
                fn = os.path.join(save_batches, tdef.get("type") + "." + str(batch_num) + ".json")
                with open(fn, "w") as f:
                    f.write(json.dumps(batch, indent=2))
                    print(datetime.now(), "wrote batch to file {x}".format(x=fn))

            print(datetime.now(), "final result set / writing ", len(batch), "to", tdef.get("type"), ";", total, "of", max)
            model_class.bulk(batch, action=action, req_timeout=120)


def _diff(original, current):
    thediff = {}
    context = thediff

    def recurse(context, c, o):
        dd = dictdiffer.DictDiffer(c, o)
        changed = dd.changed()
        added = dd.added()

        for a in added:
            context[a] = c[a]

        for change in changed:
            sub = c[change]
            if isinstance(c[change], dict):
                context[change] = {}
                recurse(context[change], c[change], o[change])
            else:
                context[change] = sub

    recurse(context, current, original)
    return thediff


if __name__ == "__main__":
    # ~~->Migrate:Script~~
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--upgrade", help="path to upgrade definition")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output to stdout during processing")
    parser.add_argument("-s", "--save", help="save batches to disk in this directory")
    args = parser.parse_args()

    if not args.upgrade:
        print("Please specify an upgrade package with the -u option")
        exit()

    if not (os.path.exists(args.upgrade) and os.path.isfile(args.upgrade)):
        print(args.upgrade, "does not exist or is not a file")
        exit()

    print('Starting {0}.'.format(datetime.now()))

    with open(args.upgrade) as f:
        try:
            instructions = json.loads(f.read(), object_pairs_hook=OrderedDict)
        except:
            print(args.upgrade, "does not parse as JSON")
            exit()

        do_upgrade(instructions, args.verbose, args.save)

    print('Finished {0}.'.format(datetime.now()))
