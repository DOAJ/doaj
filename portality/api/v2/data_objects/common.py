def _check_for_script(data):
    print(data)
    for key, value in data.items():
        if value:
            if isinstance(value, dict):
                if _check_for_script(value):
                    return True
            elif isinstance(value, str):
                if "<script>" in value:
                    return True
            elif isinstance(value, list):
                for x in value:
                    if isinstance(x, str):
                        if "<script>" in value:
                            return True
    return False
