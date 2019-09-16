from portality.models import LCC


def loadLCC(source=None):
    # use delayed imports, as this code will only rarely be run
    import os
    from lxml import etree

    if source is None:
        source = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "lccSubjects.xml")

    doc = etree.parse(open(source))
    root = doc.getroot()

    nodes = {}
    tree = {"name": "LCC", "children": []}
    cpmap = {}

    for element in root.findall("subject"):
        nel = element.find("name")
        cel = element.find("code")
        pel = element.find("parent")

        if nel is None:
            continue

        name = nel.text
        code = None
        parent = None
        if cel is not None:
            code = cel.text
        if pel is not None:
            parent = pel.text

        node = {"name": name}
        if code is not None:
            node["code"] = code

        nodes[name] = node

        if parent is None:
            tree["children"].append(node)
        else:
            cpmap[name] = parent

    for child, parent in cpmap.iteritems():
        cn = nodes.get(child)
        pn = nodes.get(parent)
        if cn is None or pn is None:
            continue
        if "children" not in pn:
            pn["children"] = []
        pn["children"].append(cn)

    lcc = LCC(**tree)
    lcc.save()


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
if not lcc:
    loadLCC()
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
