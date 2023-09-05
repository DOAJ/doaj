def remove_blanks(obj) -> dict:
    if not isinstance(obj, dict):
        return obj

    for k, v in obj.items():
        if isinstance(v, dict):
            obj[k] = remove_blanks(v)

        elif isinstance(v, list):
            if not v:
                continue
            if isinstance(v[0], dict):
                obj[k] = [remove_blanks(item) for item in v]
            elif isinstance(v[0], str):
                obj[k] = [item.strip() for item in v]

        elif isinstance(v, str) and v != v.strip():
            print(f'remove blanks: {k} = [{v}]')
            obj[k] = v.strip()

    return obj
