from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.old_data_cleanup import OldDataCleanupBackgroundTask

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-b", "--background", default=180, type=int,
                        help="number of days to retain the background jobs")
    parser.add_argument("-n", "--notifications", default=180, type=int,
                        help="number of days to retain the notifications")
    args = parser.parse_args()

    app.config["TASK_DATA_RETENTION_DAYS"] = {
        "notification": args.notifications,
        "background_job": args.background,
    }
    background_helper.execute_by_bg_task_type(OldDataCleanupBackgroundTask, )
