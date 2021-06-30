#!/usr/bin/env bash

# reload the nginx config if syntax is OK
sudo nginx -t && sudo nginx -s reload
