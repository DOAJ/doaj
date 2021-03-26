import sass
import os

SASS = os.path.join("pages", "_sass")
MAIN = os.path.join(SASS, "main.scss")
STYLE = "compressed"
CSS = os.path.join("portality", "static", "doaj", "css", "main.css")
SOURCE_MAP = CSS + ".map"


def build(base_path=None):

    sass_file, main_file, css_file, map_file = _localise_paths(base_path)

    css, map = sass.compile(filename=main_file,
                 output_style=STYLE,
                 source_map_filename=map_file,
                 include_paths=[sass_file])

    with open(css_file, "w") as f:
        f.write(css)

    with open(map_file, "w") as f:
        f.write(map)


def _localise_paths(base_path=None):
    if base_path is None:
        return SASS, MAIN, CSS, SOURCE_MAP
    return (os.path.join(base_path, SASS),
            os.path.join(base_path, MAIN),
            os.path.join(base_path, CSS),
            os.path.join(base_path, SOURCE_MAP))


if __name__ == "__main__":
    build()