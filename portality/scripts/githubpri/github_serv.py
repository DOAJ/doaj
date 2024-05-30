"""
functions to interact with "Github" for githubpri
"""
from typing import Optional, Union

import requests
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

    def get(self, url, **req_kwargs):
        return send_request(url, auth=self.username_password, **req_kwargs)


def send_request(url, method='get',
                 auth: AuthLike = None,
                 **req_kwargs):
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


def get_projects(full_name, auth: AuthLike) -> dict:
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
