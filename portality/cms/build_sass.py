import sass
import os
import shutil

from datetime import datetime

SASS = os.path.join("cms", "sass")
MAIN = os.path.join(SASS, "main.scss")
STYLE = "compressed"
CSS = os.path.join("portality", "static", "doaj", "css", "main.css")
SOURCE_MAP = CSS + ".map"
ERROR = os.path.join("cms", "error_sass.txt")


def _localise_paths(base_path=None):
    now = datetime.utcnow().timestamp()
    if base_path is None:
        return SASS, MAIN, CSS, CSS + "." + str(now), SOURCE_MAP, SOURCE_MAP + "." + str(now), ERROR
    return (os.path.join(base_path, SASS),
            os.path.join(base_path, MAIN),
            os.path.join(base_path, CSS),
            os.path.join(base_path, CSS + "." + str(now)),
            os.path.join(base_path, SOURCE_MAP),
            os.path.join(base_path, SOURCE_MAP + "." + str(now)),
            os.path.join(base_path, ERROR))


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
    sass_file, main_file, css_file, css_tmp, map_file, map_tmp, error_file = None, None, None, None, None, None, None
    try:
        sass_file, main_file, css_file, css_tmp, map_file, map_tmp, error_file = _localise_paths(base_path)

        css, map = sass.compile(filename=main_file,
                     output_style=STYLE,
                     source_map_filename=map_file,
                     include_paths=[sass_file])

        with open(css_tmp, "w") as f:
            f.write(css)

        with open(map_tmp, "w") as f:
            f.write(map)

        _swap(css_file, css_tmp)
        _swap(map_file, map_tmp)

    except Exception as e:
        try:
            print("Error occurred building sass")
            if error_file:
                with open(error_file, "w") as f:
                    f.write(str(e))

            if css_tmp and os.path.exists(css_tmp):
                os.remove(css_tmp)

            if css_file and os.path.exists(css_file + ".old"):
                os.rename(css_file + ".old", css_file)

            if map_tmp and os.path.exists(map_tmp):
                os.remove(map_tmp)

            if map_file and os.path.exists(map_file + ".old"):
                os.rename(map_file + ".old", map_file)

            raise e

        except:
            print("Error occurred building sass and could not complete cleanup")
            raise e


if __name__ == "__main__":
    build()