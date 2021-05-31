def _check_for_script(data):
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
                    if _check_for_script(x):
                        return True
    return False
