#!/usr/bin/env bash

huey_consumer.py portality.tasks.consumer_long_running.long_running >> ~/huey_long_running.log 2>&1
