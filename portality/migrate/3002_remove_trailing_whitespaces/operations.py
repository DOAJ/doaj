from portality.models import Article
import csv


def remove_trailing_whitespaces_rec(d):
    for key, value in d.items():
        if isinstance(value, dict):
            return remove_trailing_whitespaces_rec(value)
        if isinstance(value, str):
            d[key] = value.strip()


def remove_trailing_whitespaces(model):
    remove_trailing_whitespaces_rec(model.__dict__)
    return model
