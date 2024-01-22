# nginx for DOAJ

Just a few notes pertinent to the DOAJ's nginx configuration

* symlink these configs on an app server running nginx; that will act as our gateway (IP can be assigned directly or we could use a load balancer)
* symlink to `/etc/nginx/sites-available` and then symlink that in `/etc/nginx/sites-enabled` as normal. Note that there are different configs for test.
* the redirects file must be symlinked on both servers to the `/etc/nginx/` directory, e.g. from, within `deploy/nginx`:
```
sudo ln -sf `pwd`/doaj-redirecs.map /etc/nginx/doaj-redirects.map
```

* There is configuration for certbot / letsencrypt here, but the main app should be behind cloudflare.
* Note there is a customisation to the nginx log format, ensure the corresponding parser is set up in logstash for correct interpretation of CloudFlare's `$cf-connecting-ip` header.
* Any update to these configs will require a `sudo nginx -t && sudo nginx -s reload` to test and reload only if successful; this happens as part of the deployment script as well.
* **There __MUST__ be auth_basic `htpasswd` files for accessing the index and monitoring - ideally separate ones.**
* All of these symlinks and files must be in place for the nginx file to be valid

In summary, for a **test** server you need:
* certbot to produce the certificates
* `htpasswd` files `/etc/nginx/htpasswd_test_es` and `/etc/nginx/htpasswd_test_monitor`
* symlinks to `doaj-redirects.map` in `/etc/nginx/` and the `doaj-test` nginx config in `/etc/nginx/sites-available/`
* symlink to enable `doaj-test` e.g `sudo ln -sf /etc/nginx/sites-available/doaj-test /etc/nginx/sites-enabled/testdoaj.cottagelabs.com`

For **production** that will be:
* certbot to produce certificates (for cloudflare's use proxying over https)
* `htpasswd` files `/etc/nginx/htpasswd_live_es` and `/etc/nginx/htpasswd_live_monitor`
* symlinks to `doaj-redirects.map` in `/etc/nginx/` and the `doaj` nginx config in `/etc/nginx/sites-available/`
* symlink to enable `doaj` e.g `sudo ln -sf /etc/nginx/sites-available/doaj /etc/nginx/sites-enabled/doaj.org`
