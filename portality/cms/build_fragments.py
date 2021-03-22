import os
import markdown
import shutil
import yaml
from copy import deepcopy

BASE = "pages"
SRC = os.path.join(BASE, "source")
OUT = os.path.join(BASE, "fragments")
FRONT_MATTER = os.path.join(BASE, "_data/frontmatter.yml")

for filename in os.listdir(OUT):
    filepath = os.path.join(OUT, filename)
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
    "mdx_truly_sane_lists"
]

cfg = {
    'markdown_link_attr_modifier': {
        "new_tab" : "external_only",
        "no_referrer" : "external_only"
    }
}

fm = {}

# Do all the page fragments

for dirpath, dirnames, filenames in os.walk(SRC):
    for fn in filenames:
        nfn = fn.rsplit(".", 1)[0] + ".html"
        sub_path = dirpath[len(SRC) + 1:]
        file_ident = "/" + os.path.join(sub_path, nfn)
        outdir = os.path.join(OUT, sub_path)
        out = os.path.join(outdir, nfn)
        input = os.path.join(SRC, sub_path, fn)

        with open(input) as f:
            md = markdown.Markdown(extensions=extensions, extension_configs=cfg)
            body = md.convert(f.read())

        nm = deepcopy(md.Meta)
        if nm.get("toc") is True:
            nm["toc_tokens"] = md.toc_tokens

        nm["frag"] = file_ident
        fm[file_ident] = nm

        if not os.path.exists(outdir):
            os.makedirs(os.path.join(OUT, sub_path))
        with open(out, "w") as g:
            g.write(body)

with open(FRONT_MATTER, "w") as f:
    f.write(yaml.dump(fm))
