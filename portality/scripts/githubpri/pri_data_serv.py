"""
functions and logic of priority data
core logic of githubpri
"""

import csv
import json
import logging
import os
from collections import defaultdict
from typing import TypedDict, List, Dict

import pandas as pd

from portality.scripts.githubpri import github_serv
from portality.scripts.githubpri.github_serv import GithubReqSender, get_column_issues

PROJECT_NAME = "DOAJ Kanban"
DEFAULT_COLUMNS = ["Review", "In progress", "To Do"]

DEFAULT_USER = 'Claimable'

log = logging.getLogger(__name__)


class Rule(TypedDict):
    id: str
    labels: List[str]
    columns: List[str]


class PriIssue(TypedDict):
    rule_id: str
    title: str
    issue_url: str
    status: str


class GithubIssue(TypedDict):
    api_url: str
    issue_number: str
    status: str  # e.g. 'To Do', 'In progress', 'Review'
    title: str


def load_rules(rules_file) -> List[Rule]:
    if not os.path.exists(rules_file):
        raise FileNotFoundError(f"Rules file [{rules_file}] not found")
    with open(rules_file, "r") as f:
        reader = csv.DictReader(f)
        rules = []
        for row in reader:
            rules.append({
                "id": row["id"],
                "labels": [l.strip() for l in row["labels"].split(",") if l.strip() != ""],
                "columns": [c.strip() for c in row["columns"].split(",") if c.strip() != ""]
            })
    return rules


def create_priorities_excel_data(priorities_file, sender: GithubReqSender) -> Dict[str, pd.DataFrame]:
    """
    ENV VARIABLE `DOAJ_GITHUB_KEY` will be used if username and password are not provided

    Parameters
    ----------
    priorities_file
    sender

    Returns
    -------
        dict mapping 'username' to 'priority dataframe'
    """

    project_list = github_serv.get_projects('DOAJ/doajPM', auth=sender.username_password)
    project = [p for p in project_list if p.get("name") == PROJECT_NAME][0]
    user_priorities = defaultdict(list)
    for priority in load_rules(priorities_file):
        print("Applying rule [{x}]".format(x=json.dumps(priority)))
        issues_by_user = _issues_by_user(project, priority, sender)
        print("Unfiltered matches for rule: ".format(x=issues_by_user))
        for user, issues in issues_by_user.items():
            print(user)
            for i in issues:
                print('  * [{}] {}'.format(i.get('issue_number'), i.get('title')))

        for user, issues in issues_by_user.items():
            issues: List[GithubIssue]
            pri_issues = [PriIssue(rule_id=priority.get("id", 1),
                                   title='[{}] {}'.format(github_issue['issue_number'], github_issue['title']),
                                   issue_url=_ui_url(github_issue['api_url']),
                                   status=github_issue['status'],
                                   )
                          for github_issue in issues]
            pri_issues = [i for i in pri_issues if
                          i['issue_url'] not in {u['issue_url'] for u in user_priorities[user]}]
            print("Novel issues for rule for user [{x}]".format(x=user))
            for i in pri_issues:
                print('  * {}'.format(i.get('title')))
            user_priorities[user] += pri_issues

    df_list = {}
    for user, pri_issues in user_priorities.items():
        df_list[user] = pd.DataFrame(pri_issues)

    return df_list


def _issues_by_user(project, priority, sender: GithubReqSender) -> Dict[str, List[GithubIssue]]:
    cols = priority.get("columns", []) or DEFAULT_COLUMNS

    user_issues = defaultdict(list)
    for status_col in cols:
        column_issues = get_column_issues(project.get("columns_url"), status_col, sender)
        labels = priority.get("labels", [])
        if labels:
            column_issues = _filter_issues_by_label(column_issues, labels)

        _split_by_user(user_issues, column_issues, status_col)

    return user_issues


def _filter_issues_by_label(issues, labels):
    filtered = []
    for issue in issues:
        issue_labels = issue.get("labels", [])
        label_names = [l.get("name") for l in issue_labels]
        found = 0
        for label in labels:
            if label in label_names:
                found += 1
        if found == len(labels):
            filtered.append(issue)
    return filtered


def _split_by_user(registry: defaultdict, issues: dict, status: str):
    for issue in issues:
        assignees = issue.get("assignees")
        assignees = [a.get("login") for a in assignees] if assignees else [DEFAULT_USER]
        github_issue = GithubIssue(api_url=issue.get("url"),
                                   issue_number=issue.get("number"),
                                   status=status,
                                   title=issue.get("title"),
                                   )
        for assignee in assignees:
            registry[assignee].append(github_issue)


def _ui_url(api_url):
    return "https://github.com/" + api_url[len("https://api.github.com/repos/"):]
