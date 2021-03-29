import os
import shutil

from jinja2 import FileSystemLoader
from flask import render_template

# import from the `app` module, as this will have all the webroutes mounted
from portality.app import app

BASE = "cms"
SRC = os.path.join(BASE, "templates", "main")
SUPP = os.path.join(BASE, "templates", "supplementary")
OUT = os.path.join(BASE, "components")


def _localise_paths(base_path=None):
    if base_path is None:
        return BASE, SRC, OUT, SUPP

    return (os.path.join(base_path, BASE),
            os.path.join(base_path, SRC),
            os.path.join(base_path, OUT),
            os.path.join(base_path, SUPP))


def build(base_path=None):

    base_dir, src_dir, out_dir, supp_dir = _localise_paths(base_path)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    for filename in os.listdir(out_dir):
        filepath = os.path.join(out_dir, filename)
        try:
            shutil.rmtree(filepath)
        except OSError:
            os.remove(filepath)

    current_paths = app.jinja_env.loader.searchpath
    app.jinja_env.loader = FileSystemLoader([os.path.join(src_dir), os.path.join(supp_dir)] + current_paths)

    ctx = app.test_request_context("/")
    ctx.push()

    # Do all the templates
    for dirpath, dirnames, filenames in os.walk(src_dir):
        for fn in filenames:
            sub_path = dirpath[len(src_dir) + 1:]
            file_ident = os.path.join(sub_path, fn)
            outdir = os.path.join(out_dir, sub_path)
            out = os.path.join(outdir, fn)

            compiled = render_template(file_ident)

            if not os.path.exists(outdir):
                os.makedirs(os.path.join(out_dir, sub_path))
            with open(out, "w") as g:
                g.write(compiled)

    ctx.pop()

    # reset the jinja environment in case we're called in context
    app.jinja_env.loader = FileSystemLoader(current_paths)

    # TODO: write the output to a temporary directory until we are sure that everything works.  Then at this final stage
    # remove the old files and replace with the new ones.
    #
    # If we fail anywhere along the line, cleanup and exit with a suitable exit code

if __name__ == "__main__":
    build()