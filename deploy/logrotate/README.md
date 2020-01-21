## DOAJ Logrotate configuration files

* Disable the default nginx logrotate in `/etc/logrotate.d/nginx` by renaming it to `nginx.disabled`
* Check the logfile paths match those configured in `settings.py`, `production.cfg` or `app.cfg`
* Copy these logrotate configs (files must be owned by root so symlinking isn't worth the bother)
  The filemode should be 644.
* If the root password has expired, crons won't run. Check this is set with `sudo chage -l root`
  and set with `sudo passwd root` if necessary.

```
sudo cp /home/cloo/doaj/src/doaj/deploy/logrotate/doaj-analytics /etc/logrotate.d/doaj-analytics
```

and

```
sudo cp /home/cloo/doaj/src/doaj/deploy/logrotate/doaj-nginx /etc/logrotate.d/doaj-nginx
```

For the AWS S3 upload to work correctly, the correct credentials must be saved in `~/.aws/`, and 
the directory symlinked to `/root/.aws` so that the upload can be run by root via cron.

```
sudo ln -s /home/cloo/.aws /root/.aws
```

**If these credentials are missing or invalid the logs will be deleted permanently**

Log uploads can be checked on the S3 bucket with the following command:

```
aws --profile doaj-nginx-logs s3 ls s3://doaj-nginx-logs
```