"""
Script to run application autochecks from the command line.

Usage:
    python portality/scripts/application_autochecks.py <application_id> [-s <status_on_complete>]
"""

from portality import constants
from portality.core import app
from portality.tasks import application_autochecks
from portality.background import BackgroundApi

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Run application autochecks for a given application")
    parser.add_argument("application_id", help="The ID of the application to run autochecks on")
    parser.add_argument("-s", "--status_on_complete", default=constants.APPLICATION_STATUS_PENDING, help="Status to set on the application after autochecks complete")
    args = parser.parse_args()

    user = app.config.get("SYSTEM_USERNAME")
    job = application_autochecks.ApplicationAutochecks.prepare(user, application=args.application_id, status_on_complete=args.status_on_complete)
    task = application_autochecks.ApplicationAutochecks(job)
    BackgroundApi.execute(task)
