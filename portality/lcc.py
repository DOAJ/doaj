from portality.models import LCC


def lcc2choices(thelcc, level=-2):
    level += 1
    level_indicator = '--'
    if 'children' in thelcc:
        results = []
        if thelcc['name'] != 'LCC':
        # don't want the root + it doesn't have a code
            results += [(thelcc['code'], level_indicator * level + thelcc['name'])]
        for child in thelcc['children']:
            results += lcc2choices(child, level=level)
        return results
    else:
        # this is a leaf
        if 'code' not in thelcc:
            if thelcc['name'] == 'TMP':
            # some weird leaf element at 1st level of the tree
            # don't want to generate a choice for it, just ignore
                return []
        return [(thelcc['code'], level_indicator * level + thelcc['name'])]


def lcc2jstree(thelcc):
    if 'children' in thelcc:
        results = []
        if thelcc['name'] == 'LCC':
            for child in thelcc['children']:
                results += lcc2jstree(child)
        else:
        # don't want the root + it doesn't have a code
            newnode = {
                "id": thelcc['code'],
                "text": thelcc['name'],
                "children": []
            }
            for child in thelcc['children']:
                newnode['children'] += lcc2jstree(child)
            results.append(newnode)

        return results
    else:
        # this is a leaf
        if 'code' not in thelcc:
            if thelcc['name'] == 'TMP':
            # some weird leaf element at 1st level of the tree
            # don't want to generate a choice for it, just ignore
                return []
        return [
            {
                "id": thelcc['code'],
                "text": thelcc['name'],
                "children": []
            }
        ]


def lcc2flat_code_index(thelcc):
    if 'children' in thelcc:
        results = {}
        if thelcc['name'] != 'LCC':
        # don't want the root + it doesn't have a code
            results.update({thelcc['code']: thelcc['name']})
        for child in thelcc['children']:
            results.update(lcc2flat_code_index(child))
        return results
    else:
        # this is a leaf
        if 'code' not in thelcc:
            if thelcc['name'] == 'TMP':
            # some weird leaf element at 1st level of the tree
            # don't want to generate a choice for it, just ignore
                return {}
        return {thelcc['code']: thelcc['name']}


lcc = LCC.pull('lcc')
lcc_choices = []
lcc_jstree = []
lcc_index_by_code = {}
if lcc:
    lcc_choices = lcc2choices(lcc)
    lcc_jstree = lcc2jstree(lcc)
    lcc_index_by_code = lcc2flat_code_index(lcc)


def lookup_code(code):
    return lcc_index_by_code.get(code)