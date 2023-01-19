from portality.lib import dates
from portality.bll import DOAJ


def mark_notifications_seen(until):
    notifications_svc = DOAJ.notificationsService()
    notifications_svc.mark_all_as_seen(until=until)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--until", help="mark all notifications before this as seen")
    args = parser.parse_args()

    until = dates.parse(args.until)

    mark_notifications_seen(until)