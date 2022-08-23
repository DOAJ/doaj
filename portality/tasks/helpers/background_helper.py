""" collections of wrapper function for helping you to create BackgroundTask

"""
from typing import Callable, Type

from portality import models
from portality.background import BackgroundApi, BackgroundTask
from portality.core import app
from portality.decorators import write_required

TaskFactory = Callable[[models.BackgroundJob], BackgroundTask]


def create_job(username, action, params=None):
    """ Common way to create BackgroundJob
    """
    job = models.BackgroundJob()
    job.user = username
    job.action = action
    if params is not None:
        job.params = params
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


def get_value_safe(key, default_v, kwargs, default_cond_fn=None):
    v = kwargs.get(key, default_v)
    default_cond_fn = default_cond_fn or (lambda _v: _v is None)
    if default_cond_fn(v):
        v = default_v
    return v


def submit_by_background_job(background_job, execute_fn):
    """ Common way of BackgroundTask.submit
    """
    background_job.save()
    execute_fn.schedule(args=(background_job.id,), delay=10)


def create_execute_fn(redis_huey, task_factory: TaskFactory):
    @redis_huey.task()
    @write_required(script=True)
    def _execute_fn(job_id):
        execute_by_job_id(job_id, task_factory)

    return _execute_fn
