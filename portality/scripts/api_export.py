import esprit, os, shutil, tarfile, json, codecs
from portality.core import app
from portality.lib import dates
from portality.store import StoreFactory
from portality.api.v1.common import ModelJsonEncoder
from portality.api.v1 import DiscoveryApi, DiscoveryException, jsonify_models
from urlparse import parse_qs, urlparse
from datetime import datetime

def _save_file(typ):
    # Create a dir for today and save all files in there
    data = json.dumps(results, cls=ModelJsonEncoder)
    filename = os.path.join(today, "{typ}_{page}.json".format(typ=typ, page=page))
    output_file = tmpStore.path(container, filename, create_container=True, must_exist=False)
    dir = os.path.dirname(output_file)
    if not os.path.exists(dir):
        os.makedirs(dir)
    print("Saving file {filename}".format(filename=filename))
    out = codecs.open(output_file, "wb", "utf-8")
    out.write(data)
    out.close
    return


def _get_last_page():
    url = results.data.get('last', '')
    last_page = None
    if url:
        last_page = parse_qs(urlparse(url).query).get('page', [])
    if last_page:
        return int(last_page[0])
    else:
        return None

def _get_dir_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def _prune_container():
    # Delete all files and dirs in the container that does not contain today's date
    for dir in mainStore.list(container):
        if today not in dir:
            mainStore.delete(target_name=dir)


def _copy_on_complete(path):
    name = os.path.basename(path)
    raw_size = _get_dir_size(path)
    print("Compressing temporary file {x}".format(x=path, y=raw_size))
    zipped_name = name + ".gz"
    dir = os.path.dirname(path)
    zipped_path = os.path.join(dir, zipped_name)
    tar = tarfile.open(zipped_path, "w:gz")
    tar.add(path)
    tar.close()
    zipped_size = os.path.getsize(zipped_path)
    print("Storing from temporary file {x} ({y} bytes)".format(x=zipped_name, y=zipped_size))
    mainStore.store(container, zipped_name, source_path=zipped_path)
    tmpStore.delete(container, name)
    tmpStore.delete(container, zipped_name)
    return


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--type", choices=['articles','journals', 'all'], help="type of data to export. ")
    parser.add_argument("-c", "--clean", action="store_false", help="Clean any pre-existing output before continuing")
    parser.add_argument("-p", "--prune", action="store_true", help="Delete previous backups if anyafter running current backup")
    args = parser.parse_args()

    tmpStore = StoreFactory.tmp()
    mainStore = StoreFactory.get("api_data")
    container = app.config.get("STORE_ANON_DATA_CONTAINER")

    if args.clean:
        mainStore.delete(container)

    # create dir with today's date
    today = datetime.now().strftime("%Y%m%d")

    # Do the search and save it
    query = '*'
    sort = None
    page_size = app.config.get("DISCOVERY_BULK_PAGE_SIZE", 1000)

    # Search articles
    if args.type == 'all' or args.type == 'articles':
        print("\n" + dates.now() + ": Starting download of articles")
        page = 1
        last_page = 1
        while page <= last_page:
            print("articles page {p} of {l}".format(p=page, l=last_page))
            # ctx = app.test_request_context()
            # ctx.push()
            try:
                results = DiscoveryApi.search_articles(query, page, page_size, sort, bulk=True)
            except DiscoveryException as e:
                raise Api400Error(e.message)
            _save_file(typ='articles')
            new_last_page = _get_last_page()
            if new_last_page is not None:
                last_page = new_last_page
            page = page + 1

    # Search journals
    if args.type == 'all' or args.type == 'journals':
        print("\n" + dates.now() + ": Starting download of journals")
        page = 1
        last_page = 1
        while page <= last_page:
            print("journals page {p} of {l}".format(p=page, l=last_page))
            try:
                results = DiscoveryApi.search_journals(query, page, page_size, sort, bulk=True)
            except DiscoveryException as e:
                raise Api400Error(e.message)
            _save_file(typ='journals')
            new_last_page = _get_last_page()
            if new_last_page is not None:
                last_page = new_last_page
            page = page + 1

    print(dates.now() + ": done\n")

    # Copy the source directory to main store
    out_dir = tmpStore.path(container, today)
    _copy_on_complete(out_dir)

    tmpStore.delete(container)

