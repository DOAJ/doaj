# ~~CMSBuildFragments:Script->CMS:Script~~
import os
import markdown
import shutil
import yaml

from copy import deepcopy
from datetime import datetime

from portality.cms import implied_attr_list

BASE = "cms"
SRC = os.path.join(BASE, "pages")
OUT = os.path.join(BASE, "fragments")
FRONT_MATTER = os.path.join(BASE, "data/frontmatter.yml")
ERROR = os.path.join(BASE, "error_fragments.txt")


def _localise_paths(base_path=None):
    now = datetime.utcnow().timestamp()
    if base_path is None:
        return BASE, SRC, OUT, OUT + "." + str(now), FRONT_MATTER, FRONT_MATTER + "." + str(now), ERROR

    return (os.path.join(base_path, BASE),
            os.path.join(base_path, SRC),
            os.path.join(base_path, OUT),
            os.path.join(base_path, OUT + "." + str(now)),
            os.path.join(base_path, FRONT_MATTER),
            os.path.join(base_path, FRONT_MATTER + "." + str(now)),
            os.path.join(base_path, ERROR))


def _clear_tree(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    for filename in os.listdir(dir):
        filepath = os.path.join(dir, filename)
        try:
            shutil.rmtree(filepath)
        except OSError:
            os.remove(filepath)


def _swap(old, new):
    if os.path.exists(old):
        os.rename(old, old + ".old")
    os.rename(new, old)
    if os.path.exists(old + ".old"):
        try:
            shutil.rmtree(old + ".old")
        except OSError:
            os.remove(old + ".old")


def build(base_path=None):
    #~~->CMSFragments:Build~~
    base_dir, src_dir, out_dir, tmp_out_dir, fm_file, fm_tmp, error_file = None, None, None, None, None, None, None
    try:
        base_dir, src_dir, out_dir, tmp_out_dir, fm_file, fm_tmp, error_file = _localise_paths(base_path)
        _clear_tree(tmp_out_dir)
        if os.path.exists(error_file):
            os.remove(error_file)

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
                outdir = os.path.join(tmp_out_dir, sub_path)
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
                    os.makedirs(outdir)
                with open(out, "w") as g:
                    g.write(body)

        with open(fm_tmp, "w") as f:
            f.write(yaml.dump(fm))

        # we've got to here, so we are ready to shift everything into live position
        _swap(out_dir, tmp_out_dir)
        _swap(fm_file, fm_tmp)

    except Exception as e:
        try:
            print("Error occurred building static pages")
            if error_file:
                with open(error_file, "w") as f:
                    f.write(str(e))

            if tmp_out_dir and os.path.exists(tmp_out_dir):
                shutil.rmtree(tmp_out_dir)

            if out_dir and os.path.exists(out_dir + ".old"):
                os.rename(out_dir + ".old", out_dir)

            if fm_tmp and os.path.exists(fm_tmp):
                os.remove(fm_tmp)

            if fm_file and os.path.exists(fm_file + ".old"):
                os.rename(fm_file + ".old", fm_file)

            raise e

        except:
            print("Error occurred building static pages and could not complete cleanup")
            raise e


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.dirname(os.path.dirname(here))
    build(base_path)