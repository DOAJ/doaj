#!/usr/bin/env bash

huey_consumer.py portality.tasks.consumer_main_queue.main_queue >> ~/huey_main_queue.log 2>&1
