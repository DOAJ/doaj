from portality.tasks.auto_assign_editor_group_data import AutoAssignEditorGroupDataTask
from portality.tasks.helpers import background_helper
from portality.models.background import StdOutBackgroundJob

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--no-prune", action="store_true", help="Suppress pruning of existing routing data")

    args = parser.parse_args()
    prune = not args.no_prune
    background_helper.execute_by_bg_task_type(AutoAssignEditorGroupDataTask, job_wrapper=StdOutBackgroundJob, prune=prune)
