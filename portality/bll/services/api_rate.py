import datetime
import functools

from portality.api import Api429Error
from portality.core import app
from portality.lib import flask_utils, dates
from portality.models import Account
from portality.models.api_log import ApiLog, ApiRateQuery

ROLE_API_RATE_T2 = 'api_rate_t2'


def count_api_rate(src: str, target: str) -> float:
    minutes = 1
    since = dates.now() - datetime.timedelta(minutes=minutes)
    ApiLog.refresh()
    count = ApiLog.count(body=ApiRateQuery(src=src, target=target, since=since).query())
    rate = count / minutes
    return rate


class ApiRateService:

    @staticmethod
    def track_api_rate(endpoint_fn):
        """
        Decorator for endpoint function to track API rate
        it will add api_log and throw 429 error if rate limit exceeded
        """

        @functools.wraps(endpoint_fn)
        def fn(*args, **kwargs):
            from flask import request

            # define src
            src = None
            api_user = None
            if 'api_key' in request.values:
                api_key = request.values['api_key']
                api_user = Account.pull_by_api_key(api_key)
                if api_user is None:
                    app.logger.debug(f'api_key [{api_key}] not found src[{flask_utils.get_remote_addr()}]')
                else:
                    src = api_key

            if src is None:
                src = flask_utils.get_remote_addr()

            target = request.url_rule.endpoint

            # rate checking
            cur_api_rate = count_api_rate(src, target)
            limited_api_rate = ApiRateService.get_allowed_rate(api_user)
            app.logger.debug(f'track_api_rate src[{src}] target[{target}] '
                      f'cur_rate[{cur_api_rate}] limited[{limited_api_rate}]')
            if cur_api_rate >= limited_api_rate:
                app.logger.info(f'reject src[{src}] target[{target}] rate[{cur_api_rate} >= {limited_api_rate}]')
                raise Api429Error('Rate limit exceeded')
            else:
                ApiLog.create(src, target)

            return endpoint_fn(*args, **kwargs)

        return fn

    @staticmethod
    def get_allowed_rate(api_user: Account = None) -> float:
        if api_user is not None and ApiRateService.is_t2_user(api_user):
            return app.config.get('RATE_LIMITS_PER_MIN_T2', 1000)

        return ApiRateService.get_default_api_rate()

    @staticmethod
    def get_default_api_rate():
        return app.config.get('RATE_LIMITS_PER_MIN_DEFAULT', 10)

    @staticmethod
    def is_t2_user(api_user: Account) -> bool:
        return isinstance(api_user, Account) and api_user.has_role(ROLE_API_RATE_T2)
