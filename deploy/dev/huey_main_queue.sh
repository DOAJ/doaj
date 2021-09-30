#!/usr/bin/env bash

# ~~Main:Queue->Huey:Technology~~
huey_consumer.py portality.tasks.consumer_main_queue.main_queue >> ~/huey_main_queue.log 2>&1
