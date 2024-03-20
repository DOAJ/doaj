How to create a background job
==============================

### Add a new BackgroundTask class

* Create a new file and new class `BackgroundTask` in `portality/tasks/<task-name>.py`
* `__action__` is the key of the new background job, should not duplicated with other background jobs
* choice a task queue, details of task queue can have find in `portality/tasks/redis_huey.py`

```python
huey_helper = JournalBulkDeleteBackgroundTask.create_huey_helper(main_queue)
```

* add execute function below BackgroundTask class

```python
huey_helper = JournalBulkDeleteBackgroundTask.create_huey_helper(main_queue)


@huey_helper.register_execute(is_load_config=False)
def journal_bulk_delete(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = JournalBulkDeleteBackgroundTask(job)
    BackgroundApi.execute(task)
```

or, using a shortcut function

```python
@huey_helper.register_execute(is_load_config=False)
def journal_bulk_delete(job_id):
    huey_helper.execute_common(job_id)
```

### For Schedule job

* add schedule function in `portality/tasks/<task-name>.py`

```python
@huey_helper.register_schedule
def scheduled_find_discontinued_soon():
    user = app.config.get("SYSTEM_USERNAME")
    job = FindDiscontinuedSoonBackgroundTask.prepare(user)
    FindDiscontinuedSoonBackgroundTask.submit(job)
```

or, using a shortcut function

```python
@huey_helper.register_schedule
def scheduled_find_discontinued_soon():
    huey_helper.scheduled_common(
        to_address_list=app.config.get("TASKS_MONITOR_BGJOBS_TO", [get_system_email(), ]),
        from_address=app.config.get("TASKS_MONITOR_BGJOBS_FROM", get_system_email()),
    )
```

* Update config file, add a new entry in `HUEY_SCHEDULE` of `portality/settings.py` and `dev.cfg` , the key is
  the value of your new `BackgroundTask.__action__`

```python
HUEY_SCHEDULE = {
    ...
"find_discontinued_soon": {"month": "*", "day": "*", "day_of_week": "*", "hour": "0", "minute": "3"},
"datalog_journal_added_update": {"month": "*", "day": "*", "day_of_week": "*", "hour": "0", "minute": "50"},
}
```
* add your new task in `HUEY_SCHEDULE` of `test.cfg` with `CRON_NEVER` value

```python
HUEY_SCHEDULE = {
  ...
    "datalog_journal_added_update": CRON_NEVER,
}
```

### Register your task

* add your execute and schedule function in `portality/tasks/consumer_long_running.py`
  or `portality/tasks/consumer_main_queue.py`
