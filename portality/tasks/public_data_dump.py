from portality import models
from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.core import app
from portality.lib import dates
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import scheduled_long_queue as queue
from portality.bll import DOAJ
from portality.bll import exceptions

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

        def logger(msg):
            job.add_audit_message(msg)
            job.save()

        svc = DOAJ.publicDataDumpService(logger)
        if clean:
            svc.remove_pdd_container()
            job.add_audit_message("Deleted existing data dump files")
            job.save()

        if types == 'all':
            types = svc.ALL
        else:
            types = [types]

        try:
            svc.dump(types, prune=prune)
        except exceptions.SaveException as e:
            raise BackgroundException("Error generating data dump: {0}".format(e))

        job.add_audit_message(dates.now_str() + ": done")

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
        job = background_helper.create_job(username, cls.__action__,
                                           queue_id=huey_helper.queue_id,
                                           params=params)
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        public_data_dump.schedule(args=(background_job.id,), delay=app.config.get('HUEY_ASYNC_DELAY', 10))


huey_helper = PublicDataDumpBackgroundTask.create_huey_helper(queue)


@huey_helper.register_schedule
def scheduled_public_data_dump():
    user = app.config.get("SYSTEM_USERNAME")
    job = PublicDataDumpBackgroundTask.prepare(user, clean=False, prune=True, types="all")
    PublicDataDumpBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def public_data_dump(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = PublicDataDumpBackgroundTask(job)
    BackgroundApi.execute(task)
