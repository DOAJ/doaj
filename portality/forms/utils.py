def expanded2compact(expanded, join_lists=None, repeat_lists=None):
    if join_lists is None:
        join_lists = {}
    if repeat_lists is None:
        repeat_lists = []

    compact = {}
    for k, v in expanded.items():
        if isinstance(v, list) and len(v) > 0:
            if isinstance(v[0], dict):
                i = 0
                for entry in v:
                    sub = expanded2compact(entry)
                    for k2, v2 in sub.items():
                        nk = k + "-" + str(i) + "-" + k2
                        compact[nk] = v2
                    i += 1
            else:
                if k in join_lists:
                    compact[k] = join_lists[k].join(v)
                elif k in repeat_lists:
                    i = 0
                    for v2 in v:
                        compact[k + "-" + str(i)] = v2
                        i += 1
                else:
                    compact[k] = v
        elif isinstance(v, dict):
            sub = expanded2compact(v)
            for k2, v2 in sub.items():
                nk = k + "-" + k2
                compact[nk] = v2
        else:
            compact[k] = v
    return compact
