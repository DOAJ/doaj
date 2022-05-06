""" collections of wrapper function for helping you to create BackgroundTask

"""
from typing import Callable, Type

from portality import models
from portality.background import BackgroundApi, BackgroundTask
from portality.core import app


def create_job(username, action):
    """ Common way to create BackgroundJob
    """
    job = models.BackgroundJob()
    job.user = username
    job.action = action
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
