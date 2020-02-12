## Kibana machine scripts

These files run on the doaj-kibana machine - we prune the indexes regularly via cron to keep
enough disk space free, and when the disk is full, we need to re-open the indexes.

On the kibana machine these are run in the global / system python environment.

**prune-indexes.py**: alter the settings at the top of the file to determine how many of each
pattern to keep, run to prune the indexes down to that number.

Run daily with the cron task:

```
  0 7  *   *   *     echo -e "\n\nstart timestamp `date +\%F_\%H\%M\%S`" >> /home/cloo/cron-logs/prune_indexes.log && python /home/cloo/prune_indexes.py >> /home/cloo/cron-logs/prune_indexes.log 2>&1
```

**release_read_only.py**: run once manually to release the read-only lock that ES applies
to all indexes when the disk fills up.