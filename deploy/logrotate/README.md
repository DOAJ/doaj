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