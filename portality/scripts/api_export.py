import esprit, os, shutil, tarfile, json, codecs
from portality.core import app
from portality.lib import dates
from portality.store import StoreFactory, StoreException
from portality.api.v1.common import ModelJsonEncoder
from portality.api.v1 import DiscoveryApi, DiscoveryException, jsonify_models
from portality.api.v1 import Api400Error
from urlparse import parse_qs, urlparse
from datetime import datetime

def _save_file(typ, day_at_start, results, record_count):
    # Create a dir for today and save all files in there
    file_count = 1
    records_per_file = app.config.get('DISCOVERY_RECORDS_PER_FILE', 100000)
    if (record_count % records_per_file) == 0:
        file_count = (record_count / records_per_file) + 1

    data = json.dumps(results, cls=ModelJsonEncoder)

    filename = os.path.join(day_at_start, "{typ}_{file_count}.json".format(typ=typ, file_count=file_count))
    output_file = tmpStore.path(container, filename, create_container=True, must_exist=False)
    dn = os.path.dirname(output_file)
    if not os.path.exists(dn):
        os.makedirs(dn)
    print("Saving file {filename}".format(filename=filename))
    with codecs.open(output_file, "ab", "utf-8") as out_file:
        out_file.write(data + '\n')


def _get_last_page(results):
    url = results.data.get('last', '')
    last_page = None
    if url:
        last_page = parse_qs(urlparse(url).query).get('page', [])
    if last_page:
        return int(last_page[0])
    return None


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
            mainStore.delete(target_name=fn)


def _copy_on_complete(path):
    name = os.path.basename(path)
    raw_size = _get_dir_size(path)
    print("Compressing temporary file {0} ({1} bytes)".format(path, raw_size))
    zipped_name = name + ".gz"
    zip_dir = os.path.dirname(path)
    zipped_path = os.path.join(zip_dir, zipped_name)
    with tarfile.open(zipped_path, "w:gz") as tar_fo:
        tar_fo.add(path)
    zipped_size = os.path.getsize(zipped_path)
    print("Storing from temporary file {0} ({1} bytes)".format(zipped_name, zipped_size))
    mainStore.store(container, zipped_name, source_path=zipped_path)
    tmpStore.delete(container, name)
    tmpStore.delete(container, zipped_name)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--type", choices=['article','journal', 'all'], help="type of data to export. ")
    parser.add_argument("-c", "--clean", action="store_false", help="Clean any pre-existing output before continuing")
    parser.add_argument("-p", "--prune", action="store_true", help="Delete previous backups if anyafter running current backup")
    args = parser.parse_args()

    tmpStore = StoreFactory.tmp()
    mainStore = StoreFactory.get("api_data")
    container = app.config.get("STORE_ANON_DATA_CONTAINER")

    if args.clean:
        mainStore.delete(container)

    # create dir with today's date
    day_at_start = dates.today()

    # Do the search and save it
    query = '*'
    page_size = app.config.get("DISCOVERY_BULK_PAGE_SIZE", 1000)

    if args.type == 'all':
        types = ['article', 'journal']
    else:
        types = [args.type]

    # Scroll for article and/or journal
    for typ in types:
        print("\n" + dates.now() + ": Starting download of " + typ)
        count = 0
        for result in DiscoveryApi.scroll(typ, None, query, page_size)
            count += 1
            _save_file(typ, day_at_start, result, count)

    print(dates.now() + ": done\n")

    # Copy the source directory to main store
    out_dir = tmpStore.path(container, day_at_start)
    try:
        _copy_on_complete(out_dir)
    except Exception as e:
        # TODO: Name exceptions to catch
        raise StoreException("Error copying data on complete\n" + e.message)

    if args.prune:
        _prune_container(day_at_start)

    tmpStore.delete(container)

