from flask import request


def get_remote_addr():
    if request:
        return request.headers.get("cf-connecting-ip", request.remote_addr)
    return None
