import re, json, os
from flask import render_template
from portality.app import app
from copy import deepcopy


BLOCK_RE = "{% block (.*?) (.*?)%}"
ENDBLOCK_RE = "{% endblock (.*?)%}"

EXTENDS_RE = "{% extends [\"'](.*?)[\"'] %}"
INCLUDES_RE = "{% include [\"'](.*?)[\"'].*?%}"
IMPORTS_RE = "{% from [\"'](.*?)[\"'].*?%}"

TEMPLATE_DIR = "/home/richard/Dropbox/Code/doaj3/portality/templates"
TEMPLATE_FILTER = "*.html"

OUT_DIR = "/home/richard/tmp/doaj/redhead/"

if not TEMPLATE_DIR.endswith("/"):
    TEMPLATE_DIR += "/"


def analyse_template(template):
    with open(template, "r") as f:
        lines = f.readlines()

    structure = destructure(lines)
    records = analyse(structure, template)
    return records


def destructure(lines):
    structure = {"content": []}

    while len(lines) > 0:
        block_until = -1
        post_end_block_line_content = ""
        for i, line in enumerate(lines):
            bm = re.search(BLOCK_RE, line)
            if bm:
                current_block = bm.group(1)
                is_scoped = "scoped" in bm.group(2)
                idx0 = line.index(bm.group(0))
                idx1 = idx0 + len(bm.group(0))
                before = line[:idx0]
                after = line[idx1:]

                structure["content"].append(before)

                if "blocks" not in structure:
                    structure["blocks"] = {}
                structure["blocks"][current_block] = {"content": [], "scoped": is_scoped}

                l, pos1, pos2 = _find_block_end([after] + lines[i+1:])

                if l is None:
                    structure["blocks"][current_block] = {"content": [after]}
                    structure["blocks"][current_block]["content"] += lines[i+1:]
                elif l == 0:
                    structure["blocks"][current_block] = {"content": [after[:pos1]]}
                    post_end_block_line_content = after[pos2:]
                    block_until = l + i
                else:
                    block_until = l + i
                    structure["blocks"][current_block]["content"] += lines[i+1:block_until]
                    pre_end_block_line_content = lines[block_until][:pos1]
                    post_end_block_line_content = lines[block_until][pos2:]
                    structure["blocks"][current_block]["content"].append(pre_end_block_line_content)

                break

            else:
                structure["content"].append(line)

        remaining = []
        if post_end_block_line_content != "" and post_end_block_line_content is not None:
            remaining.append(post_end_block_line_content)
        if block_until != -1:
            remaining += lines[block_until+1:]
        lines = remaining

    for k, v in structure.get("blocks", {}).items():
        structure["blocks"][k]["structure"] = destructure(v["content"])

    return structure


def _find_block_end(lines):
    blockcount = 0

    for i, line in enumerate(lines):
        block_commands = []
        for bsm in re.finditer(BLOCK_RE, line):
            block_commands.append((bsm.start(), 1, bsm))
        for bem in re.finditer(ENDBLOCK_RE, line):
            block_commands.append((bem.start(), -1, bem))
        block_commands.sort()
        for bc in block_commands:
            blockcount += bc[1]
            if blockcount < 0:
                return i, bc[0], bc[0] + len(bc[2].group(0))

    return None, None, None


def analyse(structure, template_name):
    records = []
    tr = {
        "type": "template",
        "file": template_name[len(TEMPLATE_DIR):]
    }

    if structure.get("blocks"):
        tr["blocks"] = list(structure.get("blocks", {}).keys())

    for i, line in enumerate(structure["content"]):
        ems = re.finditer(EXTENDS_RE, line)
        for em in ems:
            if "extends" not in tr:
                tr["extends"] = []
            tr["extends"].append(em.group(1))

        im = re.search(INCLUDES_RE, line)
        if im:
            if "includes" not in tr:
                tr["includes"] = []
            tr["includes"].append(im.group(1))

    records.append(tr)

    for k, v in structure.get("blocks", {}).items():
        records += _analyse_block(v["structure"], k, template_name, scoped=v.get("scoped", False))

    return records


def _analyse_block(block, block_name, template_name, parent_block=None, scoped=False):
    records = []
    br = {
        "type": "block",
        "name": block_name,
        "file": template_name[len(TEMPLATE_DIR):],
        "parent_block": parent_block,
        "content": False,
        "scoped": scoped
    }

    if block.get("blocks"):
        br["blocks"] = list(block.get("blocks", {}).keys())

    if len([l for l in block.get("content", []) if l.strip() != ""]) > 0:
        br["content"] = True

    for i, line in enumerate(block["content"]):
        im = re.search(INCLUDES_RE, line)
        if im:
            if "includes" not in br:
                br["includes"] = []
            br["includes"].append(im.group(1))

        ip = re.search(IMPORTS_RE, line)
        if ip:
            if "includes" not in br:
                br["includes"] = []
            br["includes"].append(ip.group(1))

    records.append(br)

    for k, v in block.get("blocks", {}).items():
        substructure = v["structure"]
        if substructure:
            records += _analyse_block(substructure, k, template_name, block_name)

    return records


def treeify(records):
    base = _get_base_templates(records)
    base.sort(key=lambda x: x["file"])

    tree = []
    for b in base:
        tree.append(_expand_file_node(b, records))

    return tree


def _expand_file_node(record, records):
    b = record

    node = {
        "name": b["file"],
        "blocks": [],
        "includes": [],
        "extensions": []
    }

    blockset = []
    for block in b.get("blocks", []):
        for r in records:
            if r["type"] == "block" and r["file"] == b["file"] and r["name"] == block:
                blockset.append(r)

    blockset.sort(key=lambda x: x["name"])
    for bs in blockset:
        br = _expand_block_node(bs, records)
        node["blocks"].append(br)

    extensions = []
    for r in records:
        if r["type"] == "template" and b["file"] in r.get("extends", []):
            extensions.append(r)

    extensions.sort(key=lambda x: x["file"])
    for ex in extensions:
        exr = _expand_file_node(ex, records)
        node["extensions"].append(exr)

    includes = []
    if "includes" in b:
        for r in records:
            if r["type"] == "template" and r["file"] in b["includes"]:
                includes.append(r)

        includes.sort(key=lambda x: x["file"])
        for inc in includes:
            incn = _expand_file_node(inc, records)
            node["includes"].append(incn)

    return node


def _expand_block_node(record, records):
    b = record

    node = {
        "name": b["name"],
        "blocks": [],
        "includes": [],
        "content": b["content"],
        "overridden_by": [],
        "overrides": [],
        "scoped": b.get("scoped", False)
    }

    blockset = []
    for block in b.get("blocks", []):
        for r in records:
            if r["type"] == "block" and r["file"] == b["file"] and r["name"] == block:
                blockset.append(r)

    blockset.sort(key=lambda x: x["name"])
    for bs in blockset:
        br = _expand_block_node(bs, records)
        node["blocks"].append(br)

    includes = []
    if "includes" in b:
        for r in records:
            if r["type"] == "template" and r["file"] in b["includes"]:
                includes.append(r)

        includes.sort(key=lambda x: x["file"])
        for inc in includes:
            incn = _expand_file_node(inc, records)
            node["includes"].append(incn)

    overridden_by = []
    for r in records:
        if r["type"] == "block" and r["name"] == b["name"] and r["file"] != b["file"]:
            paths = _extension_paths(r["file"], b["file"], records)
            if len(paths) > 0:
                overridden_by.append((r, paths))

    overridden_by.sort(key=lambda x: x[0]["file"])
    for ov, paths in overridden_by:
        node["overridden_by"].append({
            "file": ov["file"],
            "content": ov["content"],
            "paths": paths
        })

    overrides = []
    for r in records:
        if r["type"] == "block" and r["name"] == b["name"] and r["file"] != b["file"]:
            paths = _extension_paths(b["file"], r["file"], records)
            if len(paths) > 0:
                overrides.append((r, paths))

    overrides.sort(key=lambda x: x[0]["file"])
    for ov, paths in overrides:
        node["overrides"].append({
            "file": ov["file"],
            "content": ov["content"],
            "paths": paths
        })

    return node


def _extension_paths(child, parent, records):
    paths = [[child]]

    def get_record(file):
        for r in records:
            if r["type"] == "template" and r["file"] == file:
                return r
        return None

    def navigate(node, path):
        paths = []
        current_record = get_record(node)
        extends = current_record.get("extends", [])
        if len(extends) == 0:
            return [path]
        for ex in extends:
            local_path = deepcopy(path)
            local_path.append(ex)
            paths.append(local_path)
        return paths

    while True:
        all_new_paths = []
        for p in paths:
            new_paths = navigate(p[-1], p)
            all_new_paths += new_paths

        if all_new_paths != paths:
            paths = all_new_paths
        else:
            paths = all_new_paths
            break

    parent_paths = []
    for p in paths:
        p.reverse()
        if parent in p:
            idx = p.index(parent)
            parent_paths.append(p[idx:])
    return parent_paths


def serialise(tree):
    ctx = app.test_request_context("/")
    ctx.push()
    return render_template("redhead/tree.html", tree=tree)


def _get_base_templates(records):
    base = []
    includes = set()
    for r in records:
        if r["type"] == "template" and r.get("extends") is None:
            base.append(r)
        if "includes" in r:
            includes.update(r["includes"])

    base_index = [r.get("file") for r in base]

    removes = []
    for inc in includes:
        if inc in base_index:
            idx = base_index.index(inc)
            removes.append(idx)

    removes.sort(reverse=True)
    for r in removes:
        del base[r]

    return base


def block_treeify(records):
    base = _get_base_templates(records)

    tree = []
    for b in base:
        blockset = []
        for block in b.get("blocks", []):
            for r in records:
                if r["type"] == "block" and r["file"] == b["file"] and r["name"] == block:
                    blockset.append(r)

        blockset.sort(key=lambda x: x["name"])
        for bs in blockset:
            br = _expand_block_node(bs, records)
            node["blocks"].append(br)

        tree.append({
            "name": block,
            "files": [b["file"]],
            "children": []
        })

    return tree

records = []

for (root, dirs, files) in os.walk(TEMPLATE_DIR, topdown=True):
    for f in files:
        if f.endswith(".html"):
            template = os.path.join(root, f)
            print("Analysing", template)
            records += analyse_template(template)

with open(os.path.join(OUT_DIR, "redhead_records.json"), "w") as f:
    f.write(json.dumps(records, indent=2))

tree = treeify(records)

with open(os.path.join(OUT_DIR, "redhead_tree.json"), "w") as f:
    f.write(json.dumps(tree, indent=2))

html = serialise(tree)
with open(os.path.join(OUT_DIR, "redhead_tree.html"), "w") as f:
    f.write(html)

block_tree = block_treeify(records)

with open(os.path.join(OUT_DIR, "redhead_blocks.json"), "w") as f:
    f.write(json.dumps(block_tree, indent=2))