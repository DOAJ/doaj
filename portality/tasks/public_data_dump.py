from portality import models
from portality.core import app
from portality.lib import dates

from portality.tasks.redis_huey import long_running, schedule
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.store import StoreFactory
from portality.api.v1 import DiscoveryApi
from portality.api.v1.common import ModelJsonEncoder

import os, codecs, tarfile, json


class PublicDataDumpBackgroundTask(BackgroundTask):

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
        mainStore = StoreFactory.get("api_data")
        container = app.config.get("STORE_API_DATA_CONTAINER")

        if clean:
            mainStore.delete(container)

        # create dir with today's date
        day_at_start = dates.today()

        # Do the search and save it
        query = '*'
        page_size = app.config.get("DISCOVERY_BULK_PAGE_SIZE", 1000)
        records_per_file = app.config.get('DISCOVERY_RECORDS_PER_FILE', 100000)

        if types == 'all':
            types = ['article', 'journal']
        else:
            types = [types]

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
            job.add_audit_message(dates.now() + u": Starting download of " + typ)

            for result in DiscoveryApi.scroll(typ, None, query, page_size):
                batch.append(result)

                if len(batch) >= records_per_file:
                    self._save_file(tmpStore, container, typ, day_at_start, batch, file_num, tarball)
                    batch = []
                    file_num += 1

            if len(batch) > 0:
                self._save_file(tmpStore, container, typ, day_at_start, batch, file_num, tarball)

        tarball.close()
        job.add_audit_message(dates.now() + u": done")

        # Copy the source directory to main store
        try:
            self._copy_on_complete(mainStore, tmpStore, container, zipped_path)
        except Exception as e:
            tmpStore.delete(container)
            raise BackgroundException("Error copying data on complete\n" + e.message)

        if prune:
            self._prune_container(mainStore, container, day_at_start)

        tmpStore.delete(container)

    def _save_file(self, storage, container, typ, day_at_start, results, file_num, tarball):
        # Create a dir for today and save all files in there
        data = json.dumps(results, cls=ModelJsonEncoder)

        filename = os.path.join("doaj_data_" + day_at_start, "{typ}_{file_num}.json".format(typ=typ, file_num=file_num))
        output_file = storage.path(container, filename, create_container=True, must_exist=False)
        dn = os.path.dirname(output_file)
        if not os.path.exists(dn):
            os.makedirs(dn)

        self.background_job.add_audit_message(u"Saving file {filename}".format(filename=filename))
        with codecs.open(output_file, "wb", "utf-8") as out_file:
            out_file.write(data)

        self.background_job.add_audit_message(u"Adding file {filename} to compressed tar".format(filename=filename))
        tarball.add(output_file, arcname=filename)
        storage.delete(container, filename)

    def _copy_on_complete(self, mainStore, tmpStore, container, zipped_path):
        zipped_size = os.path.getsize(zipped_path)
        zipped_name = os.path.basename(zipped_path)
        self.background_job.add_audit_message(u"Storing from temporary file {0} ({1} bytes)".format(zipped_name, zipped_size))
        mainStore.store(container, zipped_name, source_path=zipped_path)
        tmpStore.delete(container, zipped_name)

    def _prune_container(self, mainStore, container, day_at_start):
        # Delete all files and dirs in the container that does not contain today's date
        file_for_today = "doaj_data_" + day_at_start + ".tar.gz"
        container_files = mainStore.list(container)
        # only delete if today's file exists
        if file_for_today not in container_files:
            self.background_job.add_audit_message(u"Files not pruned. File {0} is missing".format(file_for_today))
            return
        for container_file in container_files:
            if container_file != file_for_today:
                mainStore.delete(target_name=container_file)

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
        cls.set_param(params, 'clean', kwargs.get("clean", False))
        cls.set_param(params, "prune", kwargs.get("prune", False))
        cls.set_param(params, "types", kwargs.get("types", "all"))

        container = app.config.get("STORE_API_DATA_CONTAINER")
        if container is None:
            raise BackgroundException("You must set STORE_API_DATA_CONTAINER in the config")

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
    job = PublicDataDumpBackgroundTask.prepare(user, clean=True, prune=True, types="all")
    PublicDataDumpBackgroundTask.submit(job)


@long_running.task()
@write_required(script=True)
def public_data_dump(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = PublicDataDumpBackgroundTask(job)
    BackgroundApi.execute(task)
