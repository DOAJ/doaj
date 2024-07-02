"""
functions and logic of priority data
core logic of githubpri
extract data from Github and convert to priority order format
"""

from __future__ import annotations

import csv
import json
import logging
import os
from collections import defaultdict
from typing import TypedDict, Iterable

import pandas as pd

from portality.scripts.githubpri import github_utils
from portality.scripts.githubpri.github_utils import GithubReqSender, Issue

PROJECT_NAME = "DOAJ Kanban"
DEFAULT_COLUMNS = ["Review", "In progress", "To Do"]

DEFAULT_USER = 'Claimable'

log = logging.getLogger(__name__)


class Rule(TypedDict):
    id: str
    labels: list[str]
    columns: list[str]


class PriIssue(TypedDict):
    rule_id: str
    title: str
    issue_url: str
    status: str


class GithubIssue(TypedDict):
    url: str
    issue_number: str
    status: str  # e.g. 'To Do', 'In progress', 'Review'
    title: str
    assignees: list[str]


def load_rules(rules_file) -> list[Rule]:
    if not os.path.exists(rules_file):
        raise FileNotFoundError(f"Rules file [{rules_file}] not found")
    with open(rules_file) as f:
        reader = csv.DictReader(f)
        rules = []
        for row in reader:
            rules.append({
                "id": row["id"],
                "labels": [l.strip() for l in row["labels"].split(",") if l.strip() != ""],
                "columns": [c.strip() for c in row["columns"].split(",") if c.strip() != ""]
            })
    return rules


def create_priorities_excel_data(priorities_file, sender: GithubReqSender) -> dict[str, pd.DataFrame]:
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
    github_owner = 'DOAJ'
    github_repo = 'doajPM'
    project_number = 8

    print(f'Find issues from {github_owner}/{github_repo} project[{project_number}]')
    print(f'Project url: http://github.com/orgs/{github_owner}/projects/{project_number}')

    all_issues = github_utils.find_all_issues(owner=github_owner, repo=github_repo, project_number=project_number,
                                              sender=sender)
    all_issues = list(all_issues)
    print(f'Number of issues found: [{len(all_issues)}]')

    user_priorities = defaultdict(list)
    for priority in load_rules(priorities_file):
        print(f"Applying rule [{json.dumps(priority)}]")
        issues_by_user = _issues_by_user(all_issues, priority)
        print("Unfiltered matches for rule: [{}]".format(
            sorted(i.get("issue_number") for user, issues in issues_by_user.items() for i in issues)
        ))

        for user, issues in issues_by_user.items():
            issues: list[GithubIssue]
            pri_issues = [PriIssue(rule_id=priority.get("id", 1),
                                   title='[{}] {}'.format(github_issue['issue_number'], github_issue['title']),
                                   issue_url=github_issue['url'],
                                   status=github_issue['status'],
                                   )
                          for github_issue in issues]
            pri_issues = [i for i in pri_issues if
                          i['issue_url'] not in {u['issue_url'] for u in user_priorities[user]}]
            for i in pri_issues:
                print('    * [{}]{}'.format(user, i.get('title')))
            user_priorities[user] += pri_issues

    df_list = {}
    for user, pri_issues in user_priorities.items():
        df_list[user] = pd.DataFrame(pri_issues)

    return df_list


def _issues_by_user(issues: Iterable[Issue], priority) -> dict[str, list[GithubIssue]]:
    cols = priority.get("columns", []) or DEFAULT_COLUMNS

    user_issues = defaultdict(list)
    for status_col in cols:
        status_issues = (issue for issue in issues if issue.get("status") == status_col)
        labels = priority.get("labels", [])
        if labels:
            status_issues = (issue for issue in status_issues
                             if set(issue.get('label_names', [])).issuperset(set(labels)))

        status_issues = map(to_github_issue, status_issues)
        for issue in status_issues:
            for assignee in issue['assignees']:
                user_issues[assignee].append(issue)

    return user_issues


def to_github_issue(issue: Issue):
    github_issue = GithubIssue(url=issue.get("url"),
                               issue_number=issue.get("number"),
                               status=issue['status'],
                               title=issue.get("title"),
                               assignees=issue['assignees'] or [DEFAULT_USER]
                               )
    return github_issue
