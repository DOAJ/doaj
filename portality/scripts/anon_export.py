from portality.tasks.anon_export import AnonExportBackgroundTask
from portality.tasks.helpers import background_helper

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--limit", type=int,
                        help="Number of records to export from each type. If you specify e.g. 100, then only the first 100 accounts, 100 journals, 100 articles etc. will be exported. The \"first\" 100 will be ordered by whatever the esprit iterate functionality uses as default ordering, usually alphabetically by record id.")
    parser.add_argument("-c", "--clean", action="store_true", help="Clean any pre-existing output before continuing")
    parser.add_argument("-b", "--batch", default=100000, type=int, help="Output batch sizes")
    args = parser.parse_args()
    if args.limit is not None and args.limit > 0:
        limit = args.limit
    else:
        limit = None

    background_helper.execute_by_bg_task_type(AnonExportBackgroundTask, clean=args.clean,
                                              limit=limit, batch=args.batch)
