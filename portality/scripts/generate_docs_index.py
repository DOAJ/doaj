"""
Generates the index pages for generated documentation
"""

import os

BRANCH_PREFIXES = [
    "feature",
    "hotfix",
    "release"
]


def generate_global_index(file, dir):
    md = "# DOAJ Docs Repo\n\n"
    md += "[View on github pages](https://doaj.github.io/doaj-docs)\n\n"
    md += "Branches with documentation available:\n\n"
    
    top = os.listdir(dir)
    for entry in top:
        if not os.path.isdir(os.path.join(dir, entry)):
            continue
        if entry in BRANCH_PREFIXES:
            second = os.listdir(os.path.join(dir, entry))
            for leaf in second:
                if not os.path.isdir(os.path.join(dir, entry, leaf)):
                    continue
                md += "* [{x}/{y}]({x}/{y}/README.md)".format(x=entry, y=leaf)
        else:
            md += "* [{x}]({x}/README.md)".format(x=entry)

    with open(file, "w", encoding="utf-8") as f:
        f.write(md)


def generate_branch_index(file, dir):
    md = "# Documentation Index for {x}".format(x=os.path.basename(dir) + "\n\n")
    md += _generate_data_models_section(dir)
    md += _generate_coverage_section(dir)
    md += _generate_featuremap_section(dir)
    with open(file, "w", encoding="utf-8") as f:
        f.write(md)


def _generate_data_models_section(dir):
    md = "## Data Models\n\n"
    dir = os.path.join(dir, "data_models")
    for file in os.listdir(dir):
        name = file.split(".")[0]
        md += "* [" + name + "](data_models/" + name + ")\n"
    return md + "\n\n"


def _generate_coverage_section(dir):
    cov = os.path.join(dir, "coverage")
    if not os.path.exists(cov):
        return
    md = "## Test Coverage\n\n"
    md += "* [Coverage Report](coverage/report/index.html)"
    return md + "\n\n"


def _generate_featuremap_section(dir):
    md = "## Feature Map\n\n"
    dir = os.path.join(dir, "featuremap", "html")
    for file in os.listdir(dir):
        name = file.split(".")[0]
        md += "* [" + name + "](featuremap/html/" + file + ")\n"
    return md + "\n\n"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="output filename")
    parser.add_argument("-d", "--dir", help="directory of documentation")
    parser.add_argument("-b", "--branch", action="store_true", help="run in branch indexing mode")
    parser.add_argument("-g", "--all", action="store_true", help="run in global indexing mode")
    args = parser.parse_args()

    if args.branch:
        generate_branch_index(args.file, args.dir)

    if args.all:
        generate_global_index(args.file, args.dir)