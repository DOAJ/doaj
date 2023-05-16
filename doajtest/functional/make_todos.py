from doajtest.fixtures import ApplicationFixtureFactory
from portality import models
from portality.lib import dates
from datetime import datetime
from portality import constants

EDITOR_GROUPS = [
    "Turkish 1",
    "German1"
]

ASSOCIATES = {
    "Turkish 1": "kamil",
    "German1": "sstuder"
}


def build_application(id, title, lmu_diff, cd_diff, status, editor_group, associate, app_registry, additional_fn=None):
    source = ApplicationFixtureFactory.make_application_source()
    ap = models.Application(**source)
    bj = ap.bibjson()
    bj.title = title
    ap.set_id(id)
    ap.set_last_manual_update(dates.before_now(lmu_diff))
    ap.set_created(dates.before_now(cd_diff))
    ap.set_application_status(status)
    ap.set_editor_group(editor_group)
    ap.set_editor(associate)
    if additional_fn is not None:
        additional_fn(ap)
    ap.save()
    app_registry.append(ap)


if __name__ == "__main__":
    apps = []
    w = 7*24*60*60

    # an application stalled for more than 8 weeks (todo_maned_stalled)
    build_application("maned_stalled_1", "Medical Studies A", 9*w, 9*w, constants.APPLICATION_STATUS_IN_PROGRESS, EDITOR_GROUPS[0], ASSOCIATES[EDITOR_GROUPS[0]], apps)
    build_application("maned_stalled_2", "Medical Studies B", 9*w, 9*w, constants.APPLICATION_STATUS_IN_PROGRESS, EDITOR_GROUPS[1], ASSOCIATES[EDITOR_GROUPS[1]], apps)

    # an application that was created over 10 weeks ago (but updated recently) (todo_maned_follow_up_old)
    build_application("maned_follow_up_old_1", "Journal  of Medieval Folklore", 2 * w, 11 * w, constants.APPLICATION_STATUS_IN_PROGRESS,EDITOR_GROUPS[0], ASSOCIATES[EDITOR_GROUPS[0]], apps)
    build_application("maned_follow_up_old_2", "Journal of Military Factions", 2 * w, 11 * w, constants.APPLICATION_STATUS_IN_PROGRESS, EDITOR_GROUPS[1], ASSOCIATES[EDITOR_GROUPS[1]], apps)

    # an application that was modifed recently into the ready status (todo_maned_ready)
    build_application("maned_ready_1", "Motorsport and Racing", 2 * w, 2 * w, constants.APPLICATION_STATUS_READY,EDITOR_GROUPS[0], ASSOCIATES[EDITOR_GROUPS[0]], apps)
    build_application("maned_ready_2", "Materials Refactoring", 2 * w, 2 * w, constants.APPLICATION_STATUS_READY, EDITOR_GROUPS[1], ASSOCIATES[EDITOR_GROUPS[1]], apps)

    # an application that was modifed recently into the ready status (todo_maned_completed)
    build_application("maned_completed_1", "Mathematica Complexica", 3 * w, 3 * w, constants.APPLICATION_STATUS_COMPLETED,EDITOR_GROUPS[0], ASSOCIATES[EDITOR_GROUPS[0]], apps)
    build_application("maned_completed_2", "Materials Conductivity", 3 * w, 3 * w, constants.APPLICATION_STATUS_COMPLETED, EDITOR_GROUPS[1], ASSOCIATES[EDITOR_GROUPS[1]], apps)

    # an application that was modifed recently into the ready status (todo_maned_assign_pending)
    def assign_pending(ap): ap.remove_editor()
    build_application("maned_assign_pending_1", "Journal of Maps", 4 * w, 4 * w, constants.APPLICATION_STATUS_PENDING,EDITOR_GROUPS[0], ASSOCIATES[EDITOR_GROUPS[0]], apps, assign_pending)
    build_application("maned_assign_pending_2", "Mathematics, Arithmetic and Primes", 4 * w, 4 * w, constants.APPLICATION_STATUS_PENDING, EDITOR_GROUPS[1], ASSOCIATES[EDITOR_GROUPS[1]], apps, assign_pending)