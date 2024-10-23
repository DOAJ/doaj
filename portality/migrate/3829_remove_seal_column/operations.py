def remove_has_seal(obj):
    if 'has_seal' in obj:
        print(f'update record {obj}')
        del obj['has_seal']
    return obj
