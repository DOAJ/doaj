"""
Generates the index pages for generated documentation
"""

import os

def generate_docs_index(file, dir):
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
    args = parser.parse_args()
    generate_docs_index(args.file, args.dir)