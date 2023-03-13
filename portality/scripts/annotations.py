from portality.tasks.annotations import Annotations
from portality.tasks.helpers import background_helper
from portality.models.background import StdOutBackgroundJob

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--application", help="ID of application on which to run annotations")

    args = parser.parse_args()
    if args.application is None:
        print("You must specify an application id with the -a argument")
        exit(1)

    background_helper.execute_by_bg_task_type(Annotations,
                                              job_wrapper=StdOutBackgroundJob,
                                              application=args.application)
