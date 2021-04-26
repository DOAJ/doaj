import os

def generate_docs_index(file, dir):
    md = "# Documentation Index for {x}".format(x=os.path.basename(dir) + "\n\n")
    md += _generate_data_models_section(dir)
    with open(file, "w", encoding="utf-8") as f:
        f.write(md)


def _generate_data_models_section(dir):
    md = "## Data Models\n\n"
    dir = os.path.join(dir, "data_models")
    for file in os.listdir(dir):
        name = file.split(".")[0]
        md += "* [data_models/" + name + "](" + name + ")\n"
    return md


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="output filename")
    parser.add_argument("-d", "--dir", help="directory of documentation")
    args = parser.parse_args()
    generate_docs_index(args.file, args.dir)