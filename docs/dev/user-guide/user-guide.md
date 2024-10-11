`manage_background_jobs` / `manage-bgjobs` commands example
==========================================================


Prepare data
------------


* update dev.cfg to turn on all background job 
```
CRON_ALWAYS = {"month": "*", "day": "*", "day_of_week": "*", "hour": "*", "minute": "*"}

# Disable the bigger huey tasks. Crontabs must be for unique times to avoid delays due to perceived race conditions
HUEY_SCHEDULE = {
                "sitemap": CRON_ALWAYS,
                "reporting": CRON_ALWAYS,
                "journal_csv": CRON_ALWAYS,
                "read_news": CRON_ALWAYS,
                "article_cleanup_sync": CRON_ALWAYS,
                "async_workflow_notifications": CRON_ALWAYS,
                "request_es_backup": CRON_ALWAYS,
                "check_latest_es_backup": CRON_ALWAYS,
                "prune_es_backups": CRON_ALWAYS,
                "public_data_dump": CRON_ALWAYS,
                "harvest": CRON_ALWAYS,
                "anon_export": CRON_ALWAYS,
                "old_data_cleanup": CRON_ALWAYS,
                "monitor_bgjobs": CRON_ALWAYS,
                "find_discontinued_soon": CRON_ALWAYS,
}
```

* run your `scheduled_short` background job consumer 
```
~/venv/doaj/bin/huey_consumer.py portality.tasks.consumer_scheduled_short_queue.scheduled_short_queue
```

* wait 10 ~ 30 minute for generate some background jobs



`report` Example
----------------

* run report to check progress 
```
~/venv/doaj/bin/mange-bgjobs report 

```

* simulate db an redis async cases and try cleanup command 
```

redis-cli

# remove last 3 records on mainqueue
redis> LTRIM huey.redis.doajmainqueue 0 -4

redis> exit

# you will found 3 record only in DB
~/venv/doaj/bin/mange-bgjobs report 

# run cleanup to remove delta records 
~/venv/doaj/bin/mange-bgjobs clean
```


`rm-all` Example
------------------
* show current queued jobs
```
~/venv/doaj/bin/mange-bgjobs report 
```

* run `rm-all`
```
~/venv/doaj/bin/mange-bgjobs rm-all
```

* check results 
```
~/venv/doaj/bin/mange-bgjobs report 
```