"""
functions to interact with "Github" for githubpri
"""

import requests
from requests.auth import HTTPBasicAuth


class GithubReqSender:
    def __init__(self, username=None, password_key=None):
        """
        :param password_key:
        password of username or github api key
        """
        if username and password_key is None:
            raise ValueError("api_key or password must be provided")
        self.username_password = (username, password_key)

    def get(self, url, **req_kwargs):
        return send_request_get(url, auth=self.username_password, **req_kwargs)


def send_request_get(url, method='get', auth=None, **req_kwargs):
    """

    Parameters
    ----------
    url
    method
    auth
        accept HTTPBasicAuth, Tuple[username, password], Dict or None
    req_kwargs

    Returns
    -------

    """
    final_req_kwargs = {}
    if auth is not None:
        if isinstance(auth, tuple):
            auth = HTTPBasicAuth(*auth)
        if isinstance(auth, dict):
            auth = HTTPBasicAuth(auth['username'], auth['password'])
        final_req_kwargs |= {'auth': auth}

    final_req_kwargs |= req_kwargs
    return requests.request(method, url, **final_req_kwargs)
