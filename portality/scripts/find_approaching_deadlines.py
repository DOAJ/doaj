from portality.core import app
from portality.tasks import find_flags_with_approaching_deadline
from portality.background import BackgroundApi

def main():
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    user = app.config.get("SYSTEM_USERNAME")
    job = find_flags_with_approaching_deadline.FindFlagsWithApproachingDeadlineTask.prepare(user)
    task = find_flags_with_approaching_deadline.FindFlagsWithApproachingDeadlineTask(job)
    BackgroundApi.execute(task)

if __name__ == "__main__":
    main()