#!/usr/bin/env bash

# ~~LongRunning:Queue->Huey:Technology~~
huey_consumer.py portality.tasks.consumer_events_queue.events_queue >> ~/huey_events_queue.log 2>&1
