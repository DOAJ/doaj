import os
import markdown
import shutil
import yaml

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
    "meta",
    "markdown.extensions.tables",
    "markdown.extensions.fenced_code",
    'attr_list',
    'markdown_link_attr_modifier'
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
            # body = markdown.markdown(f.read(),
            #             extensions=extensions,
            #             extension_configs=cfg
            #         )

        meta = md.Meta

        # do some format conversions so we have propertly structured yaml come out
        nm = {}
        for k, v in meta.items():
            nm[k] = v[0] if len(v) == 1 else v
            if nm[k] == "true":
                nm[k] = True
            elif nm[k] == "false":
                nm[k] = False
            elif nm[k].isdigit():
                nm[k] = int(nm[k])

        nm["frag"] = file_ident
        fm[file_ident] = nm

        if not os.path.exists(outdir):
            os.makedirs(os.path.join(OUT, sub_path))
        with open(out, "w") as g:
            g.write(body)

with open(FRONT_MATTER, "w") as f:
    f.write(yaml.dump(fm))
