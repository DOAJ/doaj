## DOAJ Logrotate configuration files

* Disable the default nginx logrotate in `/etc/logrotate.d/nginx` by renaming it to `nginx.disabled`
* Check the logfile paths match those configured in `settings.py`, `production.cfg` or `app.cfg`
* Symlink these configs with:

```
sudo ln -s /home/cloo/doaj/src/doaj/deploy/logrotate/doaj-analytics /etc/logrotate.d/doaj-analytics
```

and

```
sudo ln -s /home/cloo/doaj/src/doaj/deploy/logrotate/doaj-nginx /etc/logrotate.d/doaj-nginx
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