import os
import markdown

BASE = "pages"
SRC = os.path.join(BASE, "src")
OUT = os.path.join(BASE, "fragments")

for dirpath, dirnames, filenames in os.walk(SRC):
    for fn in filenames:
        nfn = fn.rsplit(".", 1)[0] + ".html"
        sub_path = dirpath[len(SRC) + 1:]
        outdir = os.path.join(OUT, sub_path)
        out = os.path.join(outdir, nfn)
        input = os.path.join(SRC, sub_path, fn)

        with open(input) as f:
            body = markdown.markdown(f.read(),
                        extensions=[
                            "markdown.extensions.tables",
                            "markdown.extensions.fenced_code"
                        ]
                    )

        if not os.path.exists(outdir):
            os.makedirs(os.path.join(OUT, sub_path))
        with open(out, "w") as g:
            g.write(body)
