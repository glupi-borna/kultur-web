#!/usr/bin/env python3.9

from pathlib import Path
from os import path
import re

root = path.dirname(__file__)
parts: dict[str, str] = {}


identifier = "[A-Za-z_0-9\-]+"
re_injection = re.compile(f"""<inject\s+({identifier})\s*/>""")

def read_file(filepath: Path) -> str:
    with open(filepath, "r") as file:
        return "".join(file.readlines())


def inject_parts(text: str):
    return re_injection.sub(repl=lambda k: parts[k[1]], string=text)


for filepath in Path(root).rglob("*.part.html"):
    basename = path.basename(filepath)
    partname = str(basename).removesuffix(".part.html")
    parts[partname] = read_file(filepath)

for filepath in Path(root).rglob("*.src.html"):
    replaced_text = inject_parts(read_file(filepath))
    new_filepath = str(filepath).removesuffix(".src.html") + ".html"

    with open(new_filepath, "w") as file:
        file.writelines(replaced_text)
