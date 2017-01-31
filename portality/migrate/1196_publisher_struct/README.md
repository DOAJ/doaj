# 1196_publisher_struct

RJ 31-01-2017

Migration script to be run to convert incorrect index.publisher fields to correct form, caused
by incorrect struct.  See issue 1196.

Run

    python portality/upgrade.py -u portality/migrate/1196_publisher_struct/publisher_struct.json

