def deep_merge(a, b, overlay=False):
    if isinstance(a, list) and isinstance(b, list):
        for item in b:
            if item not in a:
                a.append(item)
    elif isinstance(a, dict) and isinstance(b, dict):
        for key in b:
            if key in a:
                a[key] = deep_merge(a[key], b[key], overlay=overlay)
            else:
                a[key] = b[key]
    else:
        if overlay:
            return b
    return a