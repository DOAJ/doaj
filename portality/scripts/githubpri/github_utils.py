"""
functions to interact with "Github" for githubpri
"""
from __future__ import annotations

import functools
import logging
import os
import warnings
from datetime import datetime
from typing import Union, Iterable, TypedDict

import requests
from requests import Response
from requests.auth import HTTPBasicAuth

from portality.lib import dates

URL_API = "https://api.github.com"

AuthLike = Union[dict, tuple, HTTPBasicAuth, None]

log = logging.getLogger(__name__)


class GithubReqSender:
    def __init__(self, token_password, username=None):
        """

        Parameters
        ----------
        token_password
            password of username or github api key
        username
        """
        if token_password is None:
            raise ValueError("api_key or password must be provided")
        self.username_password = (username, token_password)

        self.url_json_cache = {}

    def get(self, url, **req_kwargs) -> Response:
        warnings.warn("use send instead of get", DeprecationWarning)
        return send_request(url, auth=self.username_password, **req_kwargs)

    def send(self, url, method='get', **req_kwargs) -> Response:
        return send_request(url, method=method, auth=self.username_password, **req_kwargs)

    def query_graphql(self, query: str) -> dict:
        return self.send("https://api.github.com/graphql", method='post', json={'query': query}).json()

    @functools.lru_cache(maxsize=102400)
    def send_cached_json(self, url):
        if url in self.url_json_cache:
            return self.url_json_cache[url]

        result = self.send(url).json()
        self.url_json_cache[url] = result
        return result

    def yield_all(self, url, params=None, n_per_page=100) -> Iterable[dict]:
        return yields_all(url, auth=self.username_password, params=params, n_per_page=n_per_page)

    def __hash__(self):
        return hash(self.username_password)

    def __eq__(self, other):
        if not isinstance(other, GithubReqSender):
            return False
        return self.__hash__() == other.__hash__()


def send_request(url, method='get',
                 auth: AuthLike = None,
                 **req_kwargs) -> Response:
    final_req_kwargs = {}
    auth = create_auth(auth)
    if auth is not None:
        final_req_kwargs = {'auth': auth}
    final_req_kwargs.update(req_kwargs)
    resp = requests.request(method, url, **final_req_kwargs)
    if resp.status_code >= 400:
        raise ConnectionError(f'Something wrong in api response: {resp.status_code} {resp.text}')
    return resp


def create_auth(auth: AuthLike) -> HTTPBasicAuth | None:
    """

    Parameters
    ----------
    auth
        accept HTTPBasicAuth, Tuple[username, password], Dict or None

    Returns
    -------
        HTTPBasicAuth

    """

    if auth is not None:
        if isinstance(auth, tuple):
            auth = HTTPBasicAuth(*auth)
        if isinstance(auth, dict):
            auth = HTTPBasicAuth(auth['username'], auth['password'])
    return auth


def get_projects(full_name, auth: AuthLike) -> list[dict]:
    """

    Parameters
    ----------
    full_name
        owner/repo_name -- e.g. 'DOAJ/doajPM'
    auth

    Returns
    -------

    """
    url = f'{URL_API}/repos/{full_name}/projects'
    resp = send_request(url, auth=auth)
    project_list = resp.json()
    return project_list


def get_project(full_name, project_name, auth: AuthLike) -> dict | None:
    project_list = get_projects(full_name, auth)
    names = [p for p in project_list if p.get("name") == project_name]
    if len(names) == 0:
        return None
    if len(names) > 1:
        log.warning(f"Multiple projects found: {project_name}")
    return names[0]


def yields_all(url, auth: AuthLike, params=None, n_per_page=100) -> Iterable[dict]:
    final_params = {"per_page": n_per_page, "page": 1}
    if params is not None:
        final_params.update(params)

    while True:
        items = send_request(url, params=final_params, auth=auth).json()
        yield from items
        if len(items) < n_per_page:
            break

        final_params["page"] += 1


@functools.lru_cache(maxsize=102400)
def get_column_issues(columns_url, col, sender: GithubReqSender):
    print(f"Fetching column issues {col}")
    col_data = sender.send_cached_json(columns_url)
    column_records = [c for c in col_data if c.get("name") == col]
    if len(column_records) == 0:
        log.warning(f"Column not found: {col}")
        return []
    if len(column_records) > 1:
        log.warning(f"Multiple columns found: {col}")

    issues = []
    for card_data in sender.yield_all(column_records[0].get("cards_url")):
        issue_data = sender.send(card_data.get("content_url")).json()
        issues.append(issue_data)

    print("Column issues {x}".format(x=[i.get("number") for i in issues]))
    return issues


class Issue(TypedDict):
    number: int
    title: str
    status: str
    url: str
    assignees: list[str]
    label_names: list[str]
    deadline: datetime | None


def find_all_issues(owner, repo, project_number, sender: GithubReqSender) -> Iterable[Issue]:
    query_template = """
    {
      repository(owner: "%s", name: "%s") {
        projectV2(number: %s) {
          url
          title
          items(first: 100, after: AFTER_CURSOR) {
            pageInfo {
              endCursor
              hasNextPage
            }
            nodes {
              content {
                ... on Issue {
                  id
                  number
                  title
                  state
                  url 
                  stateReason
                  labels (first:100) {
                    nodes {
                      name
                    }
                  }
                  assignees(first: 100) {
                   nodes {
                      name
                      login
                   }
                  }
                }
              }
              fieldValues(first: 100) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    field {
                      ... on ProjectV2SingleSelectField {
                        name
                      }
                    }
                   }
                  ... on ProjectV2ItemFieldDateValue {
                    date
                    field {
                      ... on ProjectV2Field {
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """ % (owner, repo, project_number)

    # Function to fetch all items with pagination
    def fetch_all_items():
        # all_projects = []
        after_cursor = None
        while True:
            # Replace AFTER_CURSOR placeholder in the query template
            query = query_template.replace("AFTER_CURSOR", f'"{after_cursor}"' if after_cursor else "null")

            data = sender.query_graphql(query)

            # Process the data
            project = data['data']['repository']['projectV2']
            items = project['items']['nodes']
            yield from items
            # print(f'items: {len(items)}')
            # all_projects.extend(items)

            # Check if there are more pages
            page_info = project['items']['pageInfo']
            if page_info['hasNextPage']:
                after_cursor = page_info['endCursor']
            else:
                break

    def _to_issue(item):
        content = item['content']
        dls = [f['date'] for f in item['fieldValues']['nodes'] if f and f['field']['name'] == 'Deadline']
        dls = [d for d in dls if d is not None]
        dl = None
        if len(dls) > 0:
            dl = dates.parse(dls[0])
        return Issue(
            number=content['number'],
            title=content['title'],
            url=content['url'],
            assignees=[a['login'] for a in content['assignees']['nodes']],
            status=next((f['name'] for f in item['fieldValues']['nodes']
                         if f and f['field']['name'] == 'Status'), None),
            label_names=[l['name'] for l in content['labels']['nodes']],
            deadline=dl
        )

    # Fetch all items
    all_items = fetch_all_items()
    all_items = (i for i in all_items if i['content'])
    return map(_to_issue, all_items)
    #
    # # Filter to include only issues
    # issues = [item['content'] for item in all_items if 'id' in item['content']]
    # for issue in issues:
    #     print(f"Issue ID: {issue['id']}, Title: {issue['title']}, State: {issue['state']}, URL: {issue['url']}, "
    #           f"State Reason: {issue['stateReason']}")


def main():
    sender = GithubReqSender(os.environ.get('DOAJ_GITHUB_KEY'))
    for i in find_all_issues(sender):
        print(i)


if __name__ == '__main__':
    main()
