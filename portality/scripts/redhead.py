import re, json, os

BLOCK_RE = "{% block (.*?) %}"
ENDBLOCK_RE = "{% endblock (.*?)%}"

EXTENDS_RE = "{% extends \"(.*?)\" %}"
INCLUDES_RE = "{% include \"(.*?)\".*?%}"

TEMPLATE_DIR = "/home/richard/Dropbox/Code/doaj3/portality/templates"
TEMPLATE_FILTER = "*.html"

# TEMPLATE = "/home/richard/Dropbox/Code/doaj3/portality/templates/layouts/dashboard_base.html"

records = []

for (root, dirs, files) in os.walk(TEMPLATE_DIR, topdown=True):
    for f in files:
        if f.endswith(".html"):
            template = os.path.join(root, f)
            break


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
                idx0 = line.index(bm.group(0))
                idx1 = idx0 + len(bm.group(0))
                before = line[:idx0]
                after = line[idx1:]

                structure["content"].append(before)

                if "blocks" not in structure:
                    structure["blocks"] = {}
                structure["blocks"][current_block] = {"content": []}

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
        "file": template_name,
    }

    if structure.get("blocks"):
        tr["blocks"] = list(structure.get("blocks", {}).keys())

    for i, line in enumerate(structure["content"]):
        em = re.match(EXTENDS_RE, line)
        if em:
            tr["extends"] = em.group(1)

        im = re.search(INCLUDES_RE, line)
        if im:
            if "includes" not in tr:
                tr["includes"] = []
            tr["includes"].append(im.group(1))

    records.append(tr)

    for k, v in structure.get("blocks", {}).items():
        records += _analyse_block(v["structure"], k, template_name)

    return records

def _analyse_block(block, block_name, template_name, parent_block=None):
    records = []
    br = {
        "type": "block",
        "name": block_name,
        "file": template_name,
        "parent_block": parent_block
    }

    if block.get("blocks"):
        br["blocks"] = list(block.get("blocks", {}).keys())

    for i, line in enumerate(block["content"]):
        im = re.search(INCLUDES_RE, line)
        if im:
            if "includes" not in br:
                br["includes"] = []
            br["includes"].append(im.group(1))

    records.append(br)

    # print(block)
    for k, v in block.get("blocks", {}).items():
        substructure = v["structure"]
        if substructure:
            records += _analyse_block(substructure, k, template_name, block_name)

    return records

structure = destructure(lines)
# print(json.dumps(structure, indent=2))

analysis = analyse(structure, TEMPLATE)
print(json.dumps(analysis, indent=2))

