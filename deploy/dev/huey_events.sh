#!/usr/bin/env bash

# ~~LongRunning:Queue->Huey:Technology~~
python -m huey.bin.huey_consumer portality.tasks.consumer_events_queue.events_queue >> ~/huey_events_queue.log 2>&1
