from portality.core import app
from portality.store import StoreFactory
from portality import models, constants
from portality.lib import dates
from portality.api.current import DiscoveryApi
from portality.bll import exceptions

import os
import tarfile
import json

class PublicDataDumpService:
    ARTICLE = "article"
    JOURNAL = "journal"
    ALL = [ARTICLE, JOURNAL]

    def __init__(self, logger=None):
        self.logger = logger if logger is not None else lambda x: None

    def remove_pdd_container(self, store=None):
        """
        Empty the public data dump container.
        """
        container = app.config.get("STORE_PUBLIC_DATA_DUMP_CONTAINER")

        if store is None:
            store = StoreFactory.get(constants.STORE__SCOPE__PUBLIC_DATA_DUMP)

        store.delete_container(container)

    def dump_type(self, type, dump_start_time=None, store=None):
        if dump_start_time is None:
            dump_start_time = dates.now()
        dump_date = dates.format(dump_start_time, dates.FMT_DATE_STD)

        container = app.config.get("STORE_PUBLIC_DATA_DUMP_CONTAINER")
        tmpStore = StoreFactory.tmp()

        out_dir = tmpStore.path(container,
                                "doaj_" + type + "_data_" + dump_date,
                                create_container=True,
                                must_exist=False)

        out_name = os.path.basename(out_dir)
        zipped_name = out_name + ".tar.gz"
        zip_dir = os.path.dirname(out_dir)
        zipped_path = os.path.join(zip_dir, zipped_name)
        tarball = tarfile.open(zipped_path, "w:gz")

        file_num = 1
        out_file, path, filename = self._start_new_file(tmpStore, container, type, dump_date, file_num)

        page_size = app.config.get("DISCOVERY_BULK_PAGE_SIZE", 1000)
        records_per_file = app.config.get('DISCOVERY_RECORDS_PER_FILE', 100000)

        first_in_file = True
        count = 0
        for result in DiscoveryApi.scroll(type, None, None, page_size, scan=True):
            if not first_in_file:
                out_file.write(",\n")
            else:
                first_in_file = False
            out_file.write(json.dumps(result))
            count += 1

            if count >= records_per_file:
                file_num += 1
                self._finish_file(tmpStore, container, filename, path, out_file, tarball)
                out_file, path, filename = self._start_new_file(tmpStore, container, type, dump_date, file_num)
                first_in_file = True
                count = 0

        if count > 0:
            self._finish_file(tmpStore, container, filename, path, out_file, tarball)

        tarball.close()

        if store is None:
            store = StoreFactory.get(constants.STORE__SCOPE__PUBLIC_DATA_DUMP)

        # Copy the source directory to main store
        try:
            filesize = self._copy_on_complete(store, tmpStore, container, zipped_path)
        except Exception as e:
            raise exceptions.SaveException("Error copying {0} data on complete {1}\n".format(type, str(e)))
        finally:
            tmpStore.delete_container(container)

        store_url = store.url(container, zipped_name)
        return container, zipped_name, filesize, store_url

    def dump(self, types=None, store=None, prune=True):
        if store is None:
            store = StoreFactory.get(constants.STORE__SCOPE__PUBLIC_DATA_DUMP)

        dump_start_time = dates.now()
        if types is None:
            types = self.ALL

        dd = models.DataDump()
        dd.dump_date = dump_start_time

        for typ in types:
            self.logger("Starting export of " + typ)
            result = self.dump_type(typ, dump_start_time, store=store)

            match typ:
                case self.ARTICLE:
                    dd.set_article_dump(*result)
                case self.JOURNAL:
                    dd.set_journal_dump(*result)

        dd.save()

        if prune:
            self.prune(store=store)

    def get_premium_dump(self):
        # Get the latest data dump
        return models.DataDump.find_latest()

    def get_free_dump(self, cutoff=None):
        if cutoff is None:
            cutoff = dates.before_now(app.config.get("NON_PREMIUM_DELAY_SECONDS") + 86400)

        # get the first dump after the cutoff
        option = models.DataDump.first_dump_after(cutoff=cutoff)
        if option is not None:
            return option

        # if there was no such dump, just return the latest
        return models.DataDump.find_latest()

    def get_temporary_url(self, data_dump: models.DataDump, type):
        container, filename = None, None
        match type:
            case self.ARTICLE:
                container = data_dump.article_container
                filename = data_dump.article_filename
            case self.JOURNAL:
                container = data_dump.journal_container
                filename = data_dump.journal_filename

        if container is None or filename is None:
            raise exceptions.NoSuchPropertyException("Cannot find container and filename for {type} data dump".format(type=type))

        main_store = StoreFactory.get(constants.STORE__SCOPE__PUBLIC_DATA_DUMP)
        store_url = main_store.temporary_url(container, filename,
                                             timeout=app.config.get("PUBLIC_DATA_DUMP_URL_TIMEOUT", 3600))
        return store_url

    def prune(self, store=None):
        if store is None:
            store = StoreFactory.get(constants.STORE__SCOPE__PUBLIC_DATA_DUMP)

        # First we're going to remove all the files for data dump records which are too old to keep
        total = models.DataDump.count()
        old_dds = models.DataDump.all_dumps_before(dates.before_now(app.config.get("NON_PREMIUM_DELAY_SECONDS") + 86400))

        # if removing the old_dds would leave us without any data dump records, then don't do anything
        if total <= len(old_dds):
            self.logger("Not removing any old data dump records, as this would leave us with none")
            return

        for dd in old_dds:
            ac = dd.article_container
            af = dd.article_filename
            store.delete_file(ac, af)

            jc = dd.journal_container
            jf = dd.journal_filename
            store.delete_file(jc, jf)

            dd.delete()

        # Second we're going to check the container for files which don't have index records, and
        # clean them up

        # get the files in storage
        container = app.config.get("STORE_PUBLIC_DATA_DUMP_CONTAINER")
        container_files = store.list(container)

        # if the filename doesn't match anything, remove the file
        for cf in container_files:
            dd = models.DataDump.find_by_filename(cf)
            if dd is None:
                self.logger("No related index record; Deleting file {x} from storage container {y}".format(x=cf, y=container))
                store.delete_file(container, cf)

    def _start_new_file(self, storage, container, typ, day_at_start, file_num):
        filename = self._filename(typ, day_at_start, file_num)
        output_file = storage.path(container, filename, create_container=True, must_exist=False)
        dn = os.path.dirname(output_file)
        if not os.path.exists(dn):
            os.makedirs(dn)
        self.logger("Saving to file {filename}".format(filename=filename))

        out_file = open(output_file, "w", encoding="utf-8")
        out_file.write("[")
        return out_file, output_file, filename

    def _filename(self, typ, day_at_start, file_num):
        return os.path.join("doaj_" + typ + "_data_" + day_at_start, "{typ}_batch_{file_num}.json".format(typ=typ, file_num=file_num))

    def _finish_file(self, storage, container, filename, path, out_file, tarball):
        out_file.write("]")
        out_file.close()

        self.logger("Adding file {filename} to compressed tar".format(filename=filename))
        tarball.add(path, arcname=filename)
        storage.delete_file(container, filename)

    def _copy_on_complete(self, mainStore, tmpStore, container, zipped_path):
        zipped_size = os.path.getsize(zipped_path)
        zipped_name = os.path.basename(zipped_path)
        self.logger("Storing from temporary file {0} ({1} bytes) to container {2}".format(zipped_name, zipped_size, container))
        mainStore.store(container, zipped_name, source_path=zipped_path)
        tmpStore.delete_file(container, zipped_name)
        return zipped_size
