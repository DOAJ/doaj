import os
import markdown
import shutil
import yaml

from copy import deepcopy

from portality.cms import implied_attr_list

BASE = "cms"
SRC = os.path.join(BASE, "pages")
OUT = os.path.join(BASE, "fragments")
FRONT_MATTER = os.path.join(BASE, "data/frontmatter.yml")

def _localise_paths(base_path=None):
    if base_path is None:
        return BASE, SRC, OUT, FRONT_MATTER

    return (os.path.join(base_path, BASE),
            os.path.join(base_path, SRC),
            os.path.join(base_path, OUT),
            os.path.join(base_path, FRONT_MATTER))


def build(base_path=None):

    base_dir, src_dir, out_dir, fm_file = _localise_paths(base_path)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    for filename in os.listdir(out_dir):
        filepath = os.path.join(out_dir, filename)
        try:
            shutil.rmtree(filepath)
        except OSError:
            os.remove(filepath)

    extensions = [
        "full_yaml_metadata",
        "toc",
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        'attr_list',
        'markdown_link_attr_modifier',
        "mdx_truly_sane_lists",
        "codehilite",
        implied_attr_list.ImpliedAttrListExtension()
    ]

    cfg = {
        'markdown_link_attr_modifier': {
            "new_tab" : "external_only",
            "no_referrer" : "external_only"
        },
        "codehilite" : {
            "css_class" : "highlight"
        }
    }

    fm = {}

    # Do all the page fragments

    for dirpath, dirnames, filenames in os.walk(src_dir):
        for fn in filenames:
            nfn = fn.rsplit(".", 1)[0] + ".html"
            sub_path = dirpath[len(src_dir) + 1:]
            file_ident = "/" + os.path.join(sub_path, nfn)
            outdir = os.path.join(out_dir, sub_path)
            out = os.path.join(outdir, nfn)
            input = os.path.join(src_dir, sub_path, fn)

            with open(input) as f:
                md = markdown.Markdown(extensions=extensions, extension_configs=cfg)
                body = md.convert(f.read())

            nm = deepcopy(md.Meta)
            if nm is None:
                nm = {}
            if nm.get("toc") is True:
                nm["toc_tokens"] = md.toc_tokens

            nm["frag"] = file_ident
            fm[file_ident] = nm

            if not os.path.exists(outdir):
                os.makedirs(os.path.join(out_dir, sub_path))
            with open(out, "w") as g:
                g.write(body)

    with open(fm_file, "w") as f:
        f.write(yaml.dump(fm))

    # TODO: write the output to a temporary directory until we are sure that everything works.  Then at this final stage
    # remove the old files and replace with the new ones.
    #
    # If we fail anywhere along the line, cleanup and exit with a suitable exit code

if __name__ == "__main__":
    build()