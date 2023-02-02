"""
This script exports all your activity from the DOAJ code and PM issue trackers

Example:

python github_issue_activity.py -u [username] -p [passcode] -s 2021-05-10T00:00:00Z -f 2021-07-15T00:00:00Z -o activity.csv

If you want to see your commit history in a similarly useful form, you can use:

git log --pretty=format:'"%ad","%d","%B"' --date=short --reverse --all --since=[date] --author="[name]"

"""
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import csv

from portality.lib.dates import STD_DATETIME_FMT

ISSUES = [
    "https://api.github.com/repos/DOAJ/doajPM/issues",
    "https://api.github.com/repos/DOAJ/doaj/issues"
]


def toDate(str):
    return datetime.strptime(str, STD_DATETIME_FMT)


def _github_repo_report(issues, username, password, start, finish):
    params = {
        "state": "all",
        "since": start,
        "per_page": 100,
        "page": 1
    }
    auth = HTTPBasicAuth(username, password)

    activity = []
    start = toDate(start)
    finish = toDate(finish)

    while True:
        resp = requests.get(issues, params=params, auth=auth)
        if resp.status_code != 200:
            print(resp.status_code)
            raise Exception(resp.status_code)

        data = resp.json()
        if len(data) == 0:
            break
        params["page"] += 1

        for record in data:
            created_at = toDate(record.get("created_at"))
            if record.get("user", {}).get("login") == username:
                if start < created_at < finish:
                    activity.append([
                        record.get("created_at"),
                        "Issue" if "pull_request" not in record else "PR",
                        record.get("html_url"),
                        record.get("title")
                    ])

            if record.get("comments", 0) > 0:
                comments_url = record.get("comments_url")
                resp2 = requests.get(comments_url, auth=auth)
                comments = resp2.json()
                for c in comments:
                    created_at = toDate(c.get("created_at"))
                    if c.get("user", {}).get("login") == username:
                        if start < created_at < finish:
                            activity.append([
                                c.get("created_at"),
                                "Comment",
                                c.get("html_url")
                            ])

    return activity


def _github_counter(issues, username, password, start, finish):
    params = {
        "state": "all",
        "since": start,
        "per_page": 100,
        "page": 1
    }
    auth = HTTPBasicAuth(username, password)

    activity = []
    start = toDate(start)
    finish = toDate(finish)

    while True:
        resp = requests.get(issues, params=params, auth=auth)
        if resp.status_code != 200:
            print(resp.status_code)
            raise Exception(resp.status_code)

        data = resp.json()
        if len(data) == 0:
            break
        params["page"] += 1

        for record in data:
            created_at = toDate(record.get("created_at"))
            if start < created_at < finish:
                activity.append([
                    record.get("created_at"),
                    "Issue" if "pull_request" not in record else "PR",
                    record.get("html_url")
                ])

            if record.get("comments", 0) > 0:
                comments_url = record.get("comments_url")
                resp2 = requests.get(comments_url, auth=auth)
                comments = resp2.json()
                for c in comments:
                    created_at = toDate(c.get("created_at"))
                    if start < created_at < finish:
                        activity.append([
                            c.get("created_at"),
                            "Comment",
                            c.get("html_url")
                        ])

    return activity


def _issue_titles(issues, username, password, start, finish):
    params = {
        "state": "all",
        "since": start,
        "per_page": 100,
        "page": 1
    }
    auth = HTTPBasicAuth(username, password)

    activity = []
    start = toDate(start)
    finish = toDate(finish)

    while True:
        resp = requests.get(issues, params=params, auth=auth)
        if resp.status_code != 200:
            print(resp.status_code)
            raise Exception(resp.status_code)

        data = resp.json()
        if len(data) == 0:
            break
        params["page"] += 1

        for record in data:
            if "pull_request" not in record and record.get("state") == "closed":
                closed_at = toDate(record.get("closed_at"))
                if start < closed_at < finish and "pull_request" not in record and record.get("state") == "closed":
                    activity.append([
                        record.get("closed_at"),
                        record.get("html_url"),
                        record.get("title"),
                        ", ".join([l.get("name", "") for l in record.get("labels", [])])
                    ])

    return activity



def github_report(username, password, start, finish, out, count_report=False, title_report=False):
    activity = []
    for issue in ISSUES:
        if count_report:
            report = _github_counter(issue, username, password, start, finish)
        elif title_report:
            report = _issue_titles(issue, username, password, start, finish)
        else:
            report = _github_repo_report(issue, username, password, start, finish)
        activity += report

    activity.sort(key=lambda x: x[0])

    with open(out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(activity)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username")
    parser.add_argument("-p", "--password")
    parser.add_argument("-s", "--start")
    parser.add_argument("-f", "--finish")
    parser.add_argument("-o", "--out")
    parser.add_argument("-c", "--count", action="store_true", default=False)
    parser.add_argument("-t", "--title", action="store_true", default=False)
    args = parser.parse_args()

    github_report(args.username, args.password, args.start, args.finish, args.out, args.count, args.title)