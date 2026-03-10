## Logstash pipelines

To be placed in `/etc/logstash/conf.d/` on the kibana monitor machine.

* filebeat-nginx-sampled.conf - our production config for parsing NGINX logs via cloudflare, uses sampling to reduce DNS lookups. Understands a few of the possible access log formats we see.
	+ Note, this needs to be changed if the NGINX log format is adjusted (e.g. cf-connecting-ip is Cloudflare specific, and added TLS version to logs)
* filebeat-nginx-min.conf.disabled - unused nginx logs minimal configuration (fast)
* filebeat-nginx.conf.disabled - unused nginx logs configuration which disables DNS lookup (medium)

In addition, the following changes were made to `/etc/logstash/logstash.yml` to improve throughput:

```
...

# How many events to retrieve from inputs before sending to filters+workers
#
pipeline.batch.size: 250
#
# How long to wait in milliseconds while polling for the next event
# before dispatching an undersized batch to filters+outputs
#
pipeline.batch.delay: 5

...
```

Also worth noting, this command to run logstash and validate a specific pipeline configuration file:

```
sudo /usr/share/logstash/bin/logstash --config.test_and_exit -f /etc/logstash/conf.d/filebeat-nginx-sampled.conf
```