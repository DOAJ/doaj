from portality.models import Article
import csv

def remove_trailing_whitespaces_rec(d):
    for key, value in d.items():
        if isinstance(value, dict):
            return remove_trailing_whitespaces_rec(value)
        if isinstance(value, str):
            d[key] = value.strip()

def remove_trailing_whitespaces(model):
    with open("out.csv", "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["es_type", "ID", "key", "old value", "new value"])

        remove_trailing_whitespaces_rec(model.__dict__)

    return model
