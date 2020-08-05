from portality import models
from portality.core import app
from portality.lib import dates
from portality.models import cache

from portality.tasks.redis_huey import long_running, schedule
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.store import StoreFactory
from portality.api.v1 import DiscoveryApi
from portality.api.common import ModelJsonEncoder

import os, tarfile, json


class PublicDataDumpBackgroundTask(BackgroundTask):
    """
    This task allows us to generate the public data dumps for the system.  It provides a number of
    configuration options, and it is IMPORTANT to note that in production it MUST only be run with the
    following settings:


         types: all
         clean: False
         prune: True

    If you run this in production with either `journal` or `article` as type,
    then any existing link to the other data type will be no longer available.

    If you run this with clean set True, there is a chance that in the event of an error the live
    data will be deleted, and not replaced with new data.  Better to prune after the
    new data has been generated instead.
    """

    __action__ = "public_data_dump"

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """
        job = self.background_job
        params = job.params

        clean = self.get_param(params, 'clean')
        prune = self.get_param(params, 'prune')
        types = self.get_param(params, 'types')

        tmpStore = StoreFactory.tmp()
        mainStore = StoreFactory.get("public_data_dump")
        container = app.config.get("STORE_PUBLIC_DATA_DUMP_CONTAINER")

        if clean:
            mainStore.delete_container(container)
            job.add_audit_message("Deleted existing data dump files")
            job.save()

        # create dir with today's date
        day_at_start = dates.today()

        # Do the search and save it
        page_size = app.config.get("DISCOVERY_BULK_PAGE_SIZE", 1000)
        records_per_file = app.config.get('DISCOVERY_RECORDS_PER_FILE', 100000)

        if types == 'all':
            types = ['article', 'journal']
        else:
            types = [types]

        urls = {"article" : None, "journal" : None}
        sizes = {"article" : None, "journal" : None}

        # Scroll for article and/or journal
        for typ in types:
            job.add_audit_message(dates.now() + ": Starting export of " + typ)
            job.save()

            out_dir = tmpStore.path(container, "doaj_" + typ + "_data_" + day_at_start, create_container=True, must_exist=False)
            out_name = os.path.basename(out_dir)
            zipped_name = out_name + ".tar.gz"
            zip_dir = os.path.dirname(out_dir)
            zipped_path = os.path.join(zip_dir, zipped_name)
            tarball = tarfile.open(zipped_path, "w:gz")

            file_num = 1
            out_file, path, filename = self._start_new_file(tmpStore, container, typ, day_at_start, file_num)

            first_in_file = True
            count = 0
            for result in DiscoveryApi.scroll(typ, None, None, page_size, scan=True):
                if not first_in_file:
                    out_file.write(",\n")
                else:
                    first_in_file = False
                out_file.write(json.dumps(result))
                count += 1

                if count >= records_per_file:
                    file_num += 1
                    self._finish_file(tmpStore, container, filename, path, out_file, tarball)
                    job.save()
                    out_file, path, filename = self._start_new_file(tmpStore, container, typ, day_at_start, file_num)
                    first_in_file = True
                    count = 0

            if count > 0:
                self._finish_file(tmpStore, container, filename, path, out_file, tarball)
                job.save()

            tarball.close()

            # Copy the source directory to main store
            try:
                filesize = self._copy_on_complete(mainStore, tmpStore, container, zipped_path)
                job.save()
            except Exception as e:
                tmpStore.delete_container(container)
                raise BackgroundException("Error copying {0} data on complete {1}\n".format(typ, str(e)))

            store_url = mainStore.url(container, zipped_name)
            urls[typ] = store_url
            sizes[typ] = filesize

        if prune:
            self._prune_container(mainStore, container, day_at_start, types)
            job.save()

        self.background_job.add_audit_message("Removing temp store container {x}".format(x=container))
        tmpStore.delete_container(container)

        # finally update the cache
        cache.Cache.cache_public_data_dump(urls["article"], sizes["article"], urls["journal"], sizes["journal"])

        job.add_audit_message(dates.now() + ": done")

    def _finish_file(self, storage, container, filename, path, out_file, tarball):
        out_file.write("]")
        out_file.close()

        self.background_job.add_audit_message("Adding file {filename} to compressed tar".format(filename=filename))
        tarball.add(path, arcname=filename)
        storage.delete_file(container, filename)

    def _start_new_file(self, storage, container, typ, day_at_start, file_num):
        filename = self._filename(typ, day_at_start, file_num)
        output_file = storage.path(container, filename, create_container=True, must_exist=False)
        dn = os.path.dirname(output_file)
        if not os.path.exists(dn):
            os.makedirs(dn)
        self.background_job.add_audit_message("Saving to file {filename}".format(filename=filename))

        out_file = open(output_file, "w", encoding="utf-8")
        out_file.write("[")
        return out_file, output_file, filename

    def _filename(self, typ, day_at_start, file_num):
        return os.path.join("doaj_" + typ + "_data_" + day_at_start, "{typ}_batch_{file_num}.json".format(typ=typ, file_num=file_num))

    def _tarball_name(self, typ, day_at_start):
        return "doaj_" + typ + "_data_" + day_at_start + ".tar.gz"

    def _copy_on_complete(self, mainStore, tmpStore, container, zipped_path):
        zipped_size = os.path.getsize(zipped_path)
        zipped_name = os.path.basename(zipped_path)
        self.background_job.add_audit_message("Storing from temporary file {0} ({1} bytes) to container {2}".format(zipped_name, zipped_size, container))
        mainStore.store(container, zipped_name, source_path=zipped_path)
        tmpStore.delete_file(container, zipped_name)
        return zipped_size

    def _prune_container(self, mainStore, container, day_at_start, types):
        # Delete all files and dirs in the container that does not contain today's date
        files_for_today = []
        for typ in types:
            files_for_today.append(self._tarball_name(typ, day_at_start))

        # get the files in storage
        container_files = mainStore.list(container)

        # only delete if today's files exist
        found = 0
        for fn in files_for_today:
            if fn in container_files:
                found += 1

        # only proceed if the files for today are present
        if found != len(files_for_today):
            self.background_job.add_audit_message("Files not pruned. One of {0} is missing".format(",".join(files_for_today)))
            return

        # go through the container files and remove any that are not today's files
        for container_file in container_files:
            if container_file not in files_for_today:
                self.background_job.add_audit_message("Pruning old file {x} from storage container {y}".format(x=container_file, y=container))
                mainStore.delete_file(container, container_file)

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """
        params = {}
        cls.set_param(params, 'clean', False if "clean" not in kwargs else kwargs["clean"] if kwargs["clean"] is not None else False)
        cls.set_param(params, "prune", False if "prune" not in kwargs else kwargs["prune"] if kwargs["prune"] is not None else False)
        cls.set_param(params, "types", "all" if "types" not in kwargs else kwargs["types"] if kwargs["types"] in ["all", "journal", "article"] else "all")

        container = app.config.get("STORE_PUBLIC_DATA_DUMP_CONTAINER")
        if container is None:
            raise BackgroundException("You must set STORE_PUBLIC_DATA_DUMP_CONTAINER in the config")

        # first prepare a job record
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__
        job.params = params
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        public_data_dump.schedule(args=(background_job.id,), delay=10)


@long_running.periodic_task(schedule("public_data_dump"))
@write_required(script=True)
def scheduled_public_data_dump():
    user = app.config.get("SYSTEM_USERNAME")
    job = PublicDataDumpBackgroundTask.prepare(user, clean=False, prune=True, types="all")
    PublicDataDumpBackgroundTask.submit(job)


@long_running.task()
@write_required(script=True)
def public_data_dump(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = PublicDataDumpBackgroundTask(job)
    BackgroundApi.execute(task)
