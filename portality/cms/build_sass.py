import sass
import os

SASS = os.path.join("pages", "_sass")
MAIN = os.path.join(SASS, "main.scss")
STYLE = "compressed"
CSS = os.path.join("portality", "static", "doaj", "css", "main.css")
SOURCE_MAP = CSS + ".map"

css, map = sass.compile(filename=MAIN,
             output_style=STYLE,
             source_map_filename=SOURCE_MAP,
             include_paths=[SASS])

with open(CSS, "w") as f:
    f.write(css)

with open(SOURCE_MAP, "w") as f:
    f.write(map)
