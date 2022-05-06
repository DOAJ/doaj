import portality.scripts.anon_export as anon_export_core
from portality import background_helper
from portality.background import BackgroundTask
from portality.decorators import write_required
from portality.tasks.redis_huey import main_queue, schedule


class AnonExportBackgroundTask(BackgroundTask):
    __action__ = "anon_export"

    def run(self):
        # KTODO get params
        anon_export_core.anon_export()
        self.background_job.add_audit_message("Anon export completed")

    def cleanup(self):
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        # KTODO set params
        # params = {}
        # cls.set_param(params, 'clean', False if "clean" not in kwargs else kwargs["clean"] if kwargs["clean"] is not None else False)
        # cls.set_param(params, "prune", False if "prune" not in kwargs else kwargs["prune"] if kwargs["prune"] is not None else False)
        # cls.set_param(params, "types", "all" if "types" not in kwargs else kwargs["types"] if kwargs["types"] in ["all", "journal", "article"] else "all")
        return background_helper.create_job(username=username,
                                            action=cls.__action__)

    @classmethod
    def submit(cls, background_job):
        background_job.save()
        anon_export.schedule(args=(background_job.id,), delay=10)


@main_queue.periodic_task(schedule(AnonExportBackgroundTask.__action__))
@write_required(script=True)
def scheduled_anon_export():
    # KTODO assign params
    background_helper.submit_by_bg_task_type(AnonExportBackgroundTask)


@main_queue.task()
@write_required(script=True)
def anon_export(job_id):
    background_helper.execute_by_job_id(job_id, AnonExportBackgroundTask)
