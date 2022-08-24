from portality.tasks.old_data_cleanup import OldDataCleanupBackgroundTask
from portality.tasks.helpers import background_helper

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-b", "--background", default=180, type=int, help="number of days to retain the background jobs")
    parser.add_argument("-n", "--notifications", default=180, type=int, help="numebr of days to retain the notifications")
    args = parser.parse_args()

    background_helper.execute_by_bg_task_type(OldDataCleanupBackgroundTask,
                                              bgjob_retention_days=args.background,
                                              noti_retention_days=args.notifications
                                              )
