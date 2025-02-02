""" collections of wrapper function for helping you to create BackgroundTask
~~BackgroundTasks:Feature~~
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
from portality.tasks.redis_huey import long_running, main_queue, events_queue, scheduled_long_queue, scheduled_short_queue, configure, schedule

TaskFactory = Callable[[models.BackgroundJob], BackgroundTask]
_queue_for_action = None


def get_queue_id_by_task_queue(task_queue: RedisHuey):
    if task_queue is None:
        return constants.BGJOB_QUEUE_ID_UNKNOWN
    elif task_queue.name == long_running.name:
        return constants.BGJOB_QUEUE_ID_LONG
    elif task_queue.name == main_queue.name:
        return constants.BGJOB_QUEUE_ID_MAIN
    elif task_queue.name == events_queue.name:
        return constants.BGJOB_QUEUE_ID_EVENTS
    elif task_queue.name == scheduled_long_queue.name:
        return constants.BGJOB_QUEUE_ID_SCHEDULED_LONG
    elif task_queue.name == scheduled_short_queue.name:
        return constants.BGJOB_QUEUE_ID_SCHEDULED_SHORT
    else:
        app.logger.warning(f'unknown task_queue[{task_queue}]')
        return constants.BGJOB_QUEUE_ID_UNKNOWN


def create_job(username, action,
               queue_id=constants.BGJOB_QUEUE_ID_UNKNOWN,
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
        queue_id = get_queue_id_by_task_queue(task_queue)
    job.queue_id = queue_id
    return job


def submit_by_bg_task_type(background_task: Type[BackgroundTask], **prepare_kwargs):
    """ Common way for BackgroundTask register_schedule """
    user = app.config.get("SYSTEM_USERNAME")
    job = background_task.prepare(user, **prepare_kwargs)
    background_task.submit(job)


def execute_by_job_id(job_id, task_factory: TaskFactory):
    """ Common way to execute BackgroundTask by job_id """
    job = models.BackgroundJob.pull(job_id)
    task = task_factory(job)
    BackgroundApi.execute(task)


def execute_by_bg_task_type(bg_task_type: Type[BackgroundTask], job_wrapper=None, **prepare_kwargs):
    """ wrapper for execute by BackgroundTask """
    user = app.config.get("SYSTEM_USERNAME")
    job = bg_task_type.prepare(user, **prepare_kwargs)
    if job_wrapper is not None:
        job = job_wrapper(job)
    task = bg_task_type(job)
    BackgroundApi.execute(task)

    return task


def register_execute(task_queue, task_name=None, script=True):
    """
    decorator for register background job execute function
    """

    def wrapper(fn):
        if task_name:
            conf = configure(task_name)
        else:
            conf = {}

        fn = write_required(script=script)(fn)
        try:
            fn = task_queue.task(**conf)(fn)
        except ValueError:
            # It's already registered - that's okay, we've probably accessed the _status endpoint and loaded the module
            return None
        return fn

    return wrapper


class RedisHueyTaskHelper:
    """
    some shortcut functions that help you implement functions that background job needed
    """

    def __init__(self, task_queue: RedisHuey, bgtask: Type[BackgroundTask]):
        self.task_queue = task_queue
        self.task_name = bgtask.__action__
        self.task_factory = bgtask

    @property
    def queue_id(self):
        return get_queue_id_by_task_queue(self.task_queue)

    def register_schedule(self, fn):
        fn = write_required(script=True)(fn)
        try:
            fn = self.task_queue.periodic_task(schedule(self.task_name))(fn)
        except ValueError:
            # It's already registered - that's okay, we've probably accessed the _status endpoint and loaded the module
            return None
        return fn

    def register_execute(self, is_load_config=False):
        return register_execute(self.task_queue,
                                self.task_name if is_load_config else None)

    def execute_common(self, job_id):
        """ Common way to execute BackgroundTask by job_id """
        execute_by_job_id(job_id, self.task_factory)

    def scheduled_common(self, **prepare_kwargs):
        """ Common way for BackgroundTask register_schedule """
        submit_by_bg_task_type(self.task_factory, **prepare_kwargs)


def _get_background_task_spec(module):
    queue_id = None
    task_name = None
    bg_class = None
    for n, member in inspect.getmembers(module):
        if isinstance(member, RedisHuey):
            queue_id = get_queue_id_by_task_queue(member)
        elif (
                inspect.isclass(member)
                and issubclass(member, BackgroundTask)
                and member != BackgroundTask
        ):
            task_name = getattr(member, '__action__', None)
            bg_class = member

        if queue_id and task_name and bg_class:
            return queue_id, task_name, bg_class

    return None


def lookup_queue_for_action(action):
    """ Find which queue an action is registered to, by action name """
    """ Inspect the background tasks to find some useful details. Store in a singleton to reduce work. """
    global _queue_for_action

    if _queue_for_action is None:
        _queue_for_action = {_action: _queue for _queue, _action, _class in get_all_background_task_specs()}

    return _queue_for_action.get(action, constants.BGJOB_QUEUE_ID_UNKNOWN)


def get_all_background_task_specs() -> Iterable[Tuple[str, str, Type]]:
    def _load_bgtask_safe(_mi):
        try:
            return _mi.module_finder.find_spec(_mi.name).loader.load_module(_mi.name)
        except RuntimeError as e:
            if 'No configuration for scheduled action' in str(e):
                app.logger.warning(f'config for {_mi.name} not found')
                return None
            raise e

    module_infos = (m for m in pkgutil.walk_packages(portality.tasks.__path__) if not m.ispkg)
    modules = (_load_bgtask_safe(mi) for mi in module_infos)
    modules = filter(None, modules)
    bgspec_list = map(_get_background_task_spec, modules)
    bgspec_list = filter(None, bgspec_list)
    return bgspec_list


def get_value_safe(key, default_v, kwargs, default_cond_fn=None):
    """ get value from kwargs and return default_v if condition  match
    """
    v = kwargs.get(key, default_v)
    default_cond_fn = default_cond_fn or (lambda _v: _v is None)
    if default_cond_fn(v):
        v = default_v
    return v


def submit_by_background_job(background_job, execute_fn):
    """ Common way of `BackgroundTask.submit`
    """
    background_job.save()
    execute_fn.schedule(args=(background_job.id,), delay=app.config.get('HUEY_ASYNC_DELAY', 10))


def create_execute_fn(task_queue: RedisHuey, task_factory: TaskFactory, task_name=None, script=True):
    """ Common way to create execute_fn for BackgroundTask """

    @register_execute(task_queue, task_name=task_name, script=script)
    def _execute_fn(job_id):
        execute_by_job_id(job_id, task_factory)

    return _execute_fn
