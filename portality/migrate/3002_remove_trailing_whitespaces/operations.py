def remove_trailing_whitespaces(d):
    for key, value in d.items():
        if isinstance(value, dict):
            d[key] = remove_trailing_whitespaces(value)
        if isinstance(value, str):
            d[key] = value.strip()
    return d
