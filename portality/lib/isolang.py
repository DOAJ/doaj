from portality.datasets import languages_iso639_2 as ISO_639_2

def find(lang):
    key = lang.lower()
    for row in ISO_639_2:
        if key in [r.lower() for r in row]:
            return as_dict(row)

def as_dict(row):
    return {
        "alpha3" : row[0],
        "alt3" : row[1],
        "alpha2": row[2],
        "name" : row[3],
        "fr" : row[4]
    }