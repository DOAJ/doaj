from portality.models import LCC

def lcc2choices(lcc, level=-2):
    level += 1
    level_indicator = '--'
    if 'children' in lcc:
        results = []
        if lcc['name'] != 'LCC':
        # don't want the root + it doesn't have a code
            results += [(lcc['code'], level_indicator * level + lcc['name'])]
        for child in lcc['children']:
            results += lcc2choices(child, level=level)
        return results
    else:
        # this is a leaf
        if 'code' not in lcc:
            if lcc['name'] == 'TMP':
            # some weird leaf element at 1st level of the tree
            # don't want to generate a choice for it, just ignore
                return []
        return [(lcc['code'], level_indicator * level + lcc['name'])]


def lcc2flat_code_index(lcc):
    if 'children' in lcc:
        results = {}
        if lcc['name'] != 'LCC':
        # don't want the root + it doesn't have a code
            results.update({lcc['code']: lcc['name']})
        for child in lcc['children']:
            results.update(lcc2flat_code_index(child))
        return results
    else:
        # this is a leaf
        if 'code' not in lcc:
            if lcc['name'] == 'TMP':
            # some weird leaf element at 1st level of the tree
            # don't want to generate a choice for it, just ignore
                return {}
        return {lcc['code']: lcc['name']}


lcc = LCC.pull('lcc')
lcc_choices = lcc2choices(lcc)

lcc_index_by_code = lcc2flat_code_index(lcc)


def lookup_code(code):
    return lcc_index_by_code[code]