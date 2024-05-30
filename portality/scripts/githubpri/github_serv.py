"""
functions to interact with "Github" for githubpri
"""
import warnings
from typing import Optional, Union, List, Iterable

import requests
from requests import Response
from requests.auth import HTTPBasicAuth

URL_API = "https://api.github.com"

AuthLike = Union[dict, tuple, HTTPBasicAuth, None]


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


def create_auth(auth: AuthLike) -> Optional[HTTPBasicAuth]:
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


def get_projects(full_name, auth: AuthLike) -> List[dict]:
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
