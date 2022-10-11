""" collections of wrapper function for helping you to create BackgroundTask

"""
import inspect
import pkgutil
from typing import Callable, Type, Iterable, Tuple

from huey import RedisHuey

import portality.tasks
from portality import models, constants
from portality.background import BackgroundApi, BackgroundTask
from portality.core import app
from portality.decorators import write_required
from portality.tasks.redis_huey import long_running, main_queue, configure, schedule


def get_queue_type_by_task_queue(task_queue: RedisHuey):
    if task_queue.name == long_running.name:
        queue_type = constants.BGJOB_QUEUE_TYPE_LONG
    elif task_queue.name == main_queue.name:
        queue_type = constants.BGJOB_QUEUE_TYPE_MAIN
    else:
        app.logger.warn(f'unknown task_queue[{task_queue}]')
        queue_type = constants.BGJOB_QUEUE_TYPE_UNKNOWN
    return queue_type


def create_job(username, action,
               queue_type=constants.BGJOB_QUEUE_TYPE_UNKNOWN,
               task_queue: RedisHuey = None,
               params=None):
    """ Common way to create BackgroundJob
    """
    job = models.BackgroundJob()
    job.user = username
    job.action = action
    if params is not None:
        job.params = params

    if task_queue is not None:
        queue_type = get_queue_type_by_task_queue(task_queue)
    job.queue_type = queue_type
    return job


def submit_by_bg_task_type(background_task: Type[BackgroundTask], **prepare_kwargs):
    """ Common way to submit task by BackgroundTask Class
    """
    user = app.config.get("SYSTEM_USERNAME")
    job = background_task.prepare(user, **prepare_kwargs)
    background_task.submit(job)


def execute_by_job_id(job_id,
                      task_factory: Callable[[models.BackgroundJob], BackgroundTask]):
    """ Common way to execute BackgroundTask by job_id
    """
    job = models.BackgroundJob.pull(job_id)
    task = task_factory(job)
    BackgroundApi.execute(task)


def execute_by_bg_task_type(bg_task_type: Type[BackgroundTask], **prepare_kwargs):
    """ wrapper for execute by BackgroundTask
    """
    user = app.config.get("SYSTEM_USERNAME")
    job = bg_task_type.prepare(user, **prepare_kwargs)
    task = bg_task_type(job)
    BackgroundApi.execute(task)

    return task


class RedisHueyTaskHelper:
    def __init__(self, task_queue: RedisHuey, task_name: str):
        self.task_queue = task_queue
        self.task_name = task_name

    @property
    def queue_type(self):
        return get_queue_type_by_task_queue(self.task_queue)

    def register_schedule(self, fn):
        fn = write_required(script=True)(fn)
        fn = self.task_queue.periodic_task(schedule(self.task_name))(fn)
        return fn

    def register_execute(self, is_load_config=False):
        def wrapper(fn):
            if is_load_config:
                conf = configure(self.task_name)
            else:
                conf = {}

            fn = write_required(script=True)(fn)
            fn = self.task_queue.task(**conf)(fn)
            return fn

        return wrapper


def _get_background_task_spec(module):
    queue_type = None
    task_name = None
    bg_class = None
    for n, member in inspect.getmembers(module):
        if isinstance(member, RedisHuey):
            queue_type = get_queue_type_by_task_queue(member)
        elif (
                inspect.isclass(member)
                and issubclass(member, BackgroundTask)
                and member != BackgroundTask
        ):
            task_name = getattr(member, '__action__', None)
            bg_class = member

        if queue_type and task_name and bg_class:
            return queue_type, task_name, bg_class

    return None


def get_all_background_task_specs() -> Iterable[Tuple[str, str, Type]]:
    module_infos = (m for m in pkgutil.walk_packages(portality.tasks.__path__) if not m.ispkg)
    modules = (mi.module_finder.find_spec(mi.name).loader.load_module(mi.name)
               for mi in module_infos)
    bgspec_list = map(_get_background_task_spec, modules)
    bgspec_list = filter(None, bgspec_list)
    return bgspec_list


def main3():
    bgspec_list = get_all_background_task_specs()
    print(list(bgspec_list))


if __name__ == '__main__':
    main3()
