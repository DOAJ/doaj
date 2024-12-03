#!/usr/bin/env bash

# ~~LongRunning:Queue->Huey:Technology~~
huey_consumer.py portality.tasks.consumer_scheduled_short_queue.scheduled_short_queue >> ~/huey_scheduled_short_queue.log 2>&1
