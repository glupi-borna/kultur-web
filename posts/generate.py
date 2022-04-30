#!/usr/bin/env python3.9

from sys import argv
from os import path
from dataclasses import dataclass, field
from datetime import date, datetime
from babel.dates import format_date
from json import dumps
from slugify import slugify

root = path.dirname(__file__)
args = argv[1:]

def page_wrapper(page):
    return f"""<!DOCTYPE html>
    <html>
        <head>
            <inject post-head />
        </head>
        <body>
            <inject navigation />
            <main>{page}</main>
        </body>
    </html>"""


@dataclass
class PostVariant():
    post: "Post"
    title: str = ""
    body: str = ""
    date: str = ""
    processed: str = ""

    def filename(self, lang: str):
        nice_title = slugify(self.title)
        return f"{self.post.raw_date}-{lang}-{nice_title}"


@dataclass
class Post():
    author: str
    raw_date: str
    date: date
    variants: dict[str, PostVariant] = field(default_factory=dict)


def extract_meta(lines, index):
    current = lines[index]

    if ":" not in current:
        return None, index

    args = current.split(":")
    if len(args) != 2:
        return None, index

    key = args[0].strip()
    value = args[1].strip()

    if value != '"""':
        return { key: value }, index

    value = ""
    count = len(lines)
    while index < count:
        index += 1
        line = lines[index]
        if line.startswith('"""'):
            break
        value += line

    return { key: value.strip() }, index


def process_file(path):
    with open(path, "r") as file:
        lines = file.readlines()

    meta = {}
    count = len(lines)
    index = 0
    while index < count:
        extracted, index = extract_meta(lines, index)
        if extracted:
            meta.update(extracted)
        index += 1

    return make_post(meta)


def write_file(filepath: str, text: str):
    with open(filepath, "w") as file:
        file.writelines(text)


def make_post(meta):
    author = meta["author"]
    post_date = datetime.strptime(meta["date"], "%Y-%m-%d").date()

    post = Post(author=author, date=post_date, raw_date=meta["date"])

    for key, val in meta.items():
        if key.startswith("post"):
            lang = key.split("-")[1]
            if lang not in post.variants:
                post.variants[lang] = PostVariant(post=post, body=val)
            else:
                post.variants[lang].body = val
        elif key.startswith("title"):
            lang = key.split("-")[1]
            if lang not in post.variants:
                post.variants[lang] = PostVariant(post=post, title=val)
            else:
                post.variants[lang].title = val

    for lang in post.variants:
        variant = post.variants[lang]
        variant.date = format_date(post.date, locale=lang)
        variant.processed = "<article>"
        variant.processed += f"<time>{variant.date}</time>"
        variant.processed += f"<cite>{post.author}</cite>"
        variant.processed += f"<h2>{variant.title}</h2>"
        variant.processed += variant.body
        variant.processed += "</article>"

    return post


files_to_process = []
for filename in args:
    if filename.endswith(".post"):
        files_to_process.append(path.join(root, filename))

processed: list[Post] = []
for filepath in files_to_process:
    processed.append(process_file(filepath))

latest_posts: dict[str, PostVariant] = {}

post_list: list[dict] = []
for post in processed:
    current: dict = {}
    langs: list[str] = []

    current["author"] = post.author
    current["date"] = post.raw_date

    for lang, variant in post.variants.items():
        if lang not in latest_posts:
            latest_posts[lang] = variant
        else:
            if variant.post.date > latest_posts[lang].post.date:
                latest_posts[lang] = variant

        langs.append(lang)
        filename = variant.filename(lang)
        current["date-"+lang] = variant.date
        current["title-"+lang] = variant.title
        current["url-"+lang] = "posts/" + filename + ".html"

        outpath = path.join(root, filename)
        write_file(outpath + ".src.html", page_wrapper(variant.processed))

    current["langs"] = langs
    post_list.append(current)

postlist = """<ul class="postlist">"""
processed.sort(key=lambda p: p.date)
for post in processed:
    lang = "hr"
    variant = post.variants.get(lang)
    if variant is None:
        for l, v in post.variants.items():
            lang = l
            variant = v
    postlist += "<li>"
    postlist += f"""<time>{variant.date}</time>"""
    postlist += f"""<a href="posts/{variant.filename(lang)}.html">{variant.title}</a>"""
    postlist +="</li>"
postlist += "</ul>"
outpath = path.join(root, f"postlist.part.html")
write_file(outpath, postlist)

for lang, variant in latest_posts.items():
    outpath = path.join(root, f"latest-{lang}")
    write_file(outpath + ".src.html", page_wrapper(variant.processed))
    write_file(outpath + ".part.html", variant.processed)

outpath = path.join(root, "index.json")
write_file(outpath, dumps(post_list))
