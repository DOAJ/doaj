#!/usr/bin/env bash

# ~~LongRunning:Queue->Huey:Technology~~
python -m huey.bin.huey_consumer portality.tasks.consumer_scheduled_long_queue.scheduled_long_queue >> ~/huey_scheduled_long_queue.log 2>&1
