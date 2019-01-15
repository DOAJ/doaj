import esprit, os, shutil, tarfile, json, codecs
from portality.core import app
from portality.lib import dates
from portality.store import StoreFactory, StoreException
from portality.api.v1.common import ModelJsonEncoder
from portality.api.v1 import DiscoveryApi, DiscoveryException, jsonify_models
from portality.api.v1 import Api400Error
from urlparse import parse_qs, urlparse
from datetime import datetime

def _save_file(storage, container, typ, day_at_start, results, file_num, tarball):
    # Create a dir for today and save all files in there
    data = json.dumps(results, cls=ModelJsonEncoder)

    filename = os.path.join("doaj_data_" + day_at_start, "{typ}_{file_num}.json".format(typ=typ, file_num=file_num))
    output_file = storage.path(container, filename, create_container=True, must_exist=False)
    dn = os.path.dirname(output_file)
    if not os.path.exists(dn):
        os.makedirs(dn)
    print("Saving file {filename}".format(filename=filename))
    with codecs.open(output_file, "wb", "utf-8") as out_file:
        out_file.write(data)

    print("Adding file {filename} to compressed tar".format(filename=filename))
    tarball.add(output_file, arcname=filename)
    storage.delete(container, filename)

def _get_dir_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def _prune_container(day_at_start):
    # Delete all files and dirs in the container that does not contain today's date
    file_for_today = day_at_start + ".gz"
    container_files = mainStore.list(container)
    # only delete if today's file exists
    if file_for_today not in container_files:
        print("Files not pruned. File {0} is missing".format(file_for_today))
        return
    for container_file in container_files:
        if container_file != file_for_today:
            mainStore.delete(target_name=container_file)


def _copy_on_complete(zipped_path):
    #name = os.path.basename(path)
    #raw_size = _get_dir_size(path)
    #print("Compressing temporary directory {0} ({1} bytes)".format(path, raw_size))
    #zipped_name = name + ".gz"
    #zip_dir = os.path.dirname(path)
    #zipped_path = os.path.join(zip_dir, zipped_name)
    #with tarfile.open(zipped_path, "w:gz") as tar_fo:
    #    tar_fo.add(path)
    zipped_size = os.path.getsize(zipped_path)
    print("Storing from temporary file {0} ({1} bytes)".format(zipped_name, zipped_size))
    mainStore.store(container, zipped_name, source_path=zipped_path)
    # tmpStore.delete(container, name)
    tmpStore.delete(container, zipped_name)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("type", choices=['article','journal', 'all'], help="type of data to export. ")
    parser.add_argument("-c", "--clean", action="store_false", help="Clean any pre-existing output before continuing")
    parser.add_argument("-p", "--prune", action="store_true", help="Delete previous backups if anyafter running current backup")
    args = parser.parse_args()

    tmpStore = StoreFactory.tmp()
    mainStore = StoreFactory.get("api_data")
    container = app.config.get("STORE_API_DATA_CONTAINER")

    if args.clean:
        mainStore.delete(container)

    # create dir with today's date
    day_at_start = dates.today()

    # Do the search and save it
    query = '*'
    page_size = app.config.get("DISCOVERY_BULK_PAGE_SIZE", 1000)
    records_per_file = app.config.get('DISCOVERY_RECORDS_PER_FILE', 100000)

    if args.type == 'all':
        types = ['article', 'journal']
    else:
        types = [args.type]

    out_dir = tmpStore.path(container, "doaj_data_" + day_at_start, create_container=True, must_exist=False)
    out_name = os.path.basename(out_dir)
    zipped_name = out_name + ".tar.gz"
    zip_dir = os.path.dirname(out_dir)
    zipped_path = os.path.join(zip_dir, zipped_name)
    tarball = tarfile.open(zipped_path, "w:gz")


    # Scroll for article and/or journal
    for typ in types:
        batch = []
        file_num = 1
        print("\n" + dates.now() + ": Starting download of " + typ)

        for result in DiscoveryApi.scroll(typ, None, query, page_size):
            batch.append(result)

            if len(batch) >= records_per_file:
                _save_file(tmpStore, container, typ, day_at_start, batch, file_num, tarball)
                batch = []
                file_num += 1

        if len(batch) > 0:
            _save_file(tmpStore, container, typ, day_at_start, batch, file_num, tarball)

    tarball.close()
    print(dates.now() + ": done\n")

    # Copy the source directory to main store
    # out_dir = tmpStore.path(container, day_at_start)
    try:
        _copy_on_complete(zipped_path)
    except Exception as e:
        # TODO: Name exceptions to catch
        tmpStore.delete(container)
        raise StoreException("Error copying data on complete\n" + e.message)

    if args.prune:
        _prune_container(day_at_start)

    tmpStore.delete(container)

