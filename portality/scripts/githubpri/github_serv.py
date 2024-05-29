"""
functions to interact with "Github" for githubpri
"""

import requests
from requests.auth import HTTPBasicAuth

HEADERS = {"Accept": "application/vnd.github+json"}


class GithubReqSender:
    def __init__(self, username=None, password_key=None):
        """
        :param password_key:
        password of username or github api key
        """
        self.username = username
        self.password_key = password_key
        if self.password_key is None:
            raise ValueError("api_key or password must be provided")

    def _create_github_request_kwargs(self) -> dict:
        req_kwargs = {'headers': dict(HEADERS)}
        req_kwargs['auth'] = HTTPBasicAuth(self.username, self.password_key)
        return req_kwargs

    def get(self, url, **req_kwargs):
        final_req_kwargs = self._create_github_request_kwargs()
        final_req_kwargs.update(req_kwargs)
        return requests.get(url, **final_req_kwargs)
