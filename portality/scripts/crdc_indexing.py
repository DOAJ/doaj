import argparse
import json
import os


def classification2choices(thelcc, level=-2):
    level += 1
    level_indicator = '--'
    if 'children' in thelcc:
        results = []
        if thelcc['name'] not in ["CRDC"]:
            # don't want the root + it doesn't have a code
            results += [(thelcc['code'], level_indicator * level + thelcc['name'])]
        for child in thelcc['children']:
            results += classification2choices(child, level=level)
        return results
    else:
        # this is a leaf
        if 'code' not in thelcc:
            if thelcc['name'] == 'TMP':
                # some weird leaf element at 1st level of the tree
                # don't want to generate a choice for it, just ignore
                return []
        return [(thelcc['code'], level_indicator * level + thelcc['name'])]


def classification2jstree(thelcc):
    if 'children' in thelcc:
        results = []
        if thelcc['name'] in ["CRDC"]:
            for child in thelcc['children']:
                results += classification2jstree(child)
        else:
            # don't want the root + it doesn't have a code
            newnode = {
                "id": thelcc['code'],
                "text": thelcc['name'],
                "children": []
            }
            for child in thelcc['children']:
                newnode['children'] += classification2jstree(child)
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


def classification2flat_code_index(thelcc):
    if 'children' in thelcc:
        results = {}
        if thelcc['name'] not in ["CRDC"]:
            # don't want the root + it doesn't have a code
            results.update({thelcc['code']: thelcc['name']})
        for child in thelcc['children']:
            results.update(classification2flat_code_index(child))
        return results
    else:
        # this is a leaf
        if 'code' not in thelcc:
            if thelcc['name'] == 'TMP':
                # some weird leaf element at 1st level of the tree
                # don't want to generate a choice for it, just ignore
                return {}
        return {thelcc['code']: thelcc['name']}



def main():
    p = argparse.ArgumentParser(description="Index Classification JSON into useful artifacts")
    p.add_argument("classification_file", help="JSON file containing the classification hierarchy (e.g. CRDC)")
    p.add_argument("-o", "--output", help="Output directory for index files.")
    args = p.parse_args()

    with open(args.classification_file) as fh:
        classification = json.load(fh)

    #choices = classification2choices(classification)
    jstree = classification2jstree(classification)
    index_by_code = classification2flat_code_index(classification)

    # we're not generating choices any more, these are obsolete
    # with open(os.path.join(args.output, "choices.json"), "w", encoding="utf-8") as fh:
    #     json.dump(choices, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(args.output, "jstree.json"), "w", encoding="utf-8") as fh:
        json.dump(jstree, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(args.output, "index_by_code.json"), "w", encoding="utf-8") as fh:
        json.dump(index_by_code, fh, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()