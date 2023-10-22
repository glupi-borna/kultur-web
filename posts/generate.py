#!/usr/bin/env python3.9

from sys import argv
from os import path, mkdir
from dataclasses import dataclass, field
from typing import Optional
from datetime import date, datetime
from babel.dates import format_date
from json import dumps
from slugify import slugify
from colorama import Fore, Style

root = path.dirname(__file__)
args = argv[1:]


if not path.exists(path.join(root, "generated")):
    mkdir(path.join(root, "generated"))

def perr(text: str):
    print(f"{Fore.RED}{Style.BRIGHT}{text}{Fore.RESET}{Style.RESET_ALL}")


def psucc(text: str):
    print(f"{Fore.GREEN}{Style.BRIGHT}{text}{Fore.RESET}{Style.RESET_ALL}")


def is_whitespace(text: str):
    for ch in text:
        if ch not in (" ", "\n", "\t"):
            return False
    return True


def page_wrapper(page: str):
    return f"""<!DOCTYPE html>
    <html>
        <head>
            <inject head />
        </head>
        <body>
            <inject navigation />
            <main>{page}</main>
            <inject footer />
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
        if self.post.fixed_filename:
            return f"{self.post.fixed_filename}-{lang}"
        nice_title = slugify(self.title)
        return f"{self.post.raw_date}-{lang}-{nice_title}"


@dataclass
class Post():
    path: str
    author: str
    raw_date: str
    date: date
    exclude: bool
    as_part: bool
    no_wrapper: bool
    fixed_filename: str
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
    start_index = index

    value = ""
    count = len(lines)
    while index < count:
        index += 1
        line = lines[index]
        if line.startswith('"""'):
            break
        if index == start_index+1:
            if not line.startswith("<"):
                line = f"<p>{line}"
        if is_whitespace(line):
            line = "<p>"
        value += line

    return { key: value.strip() }, index


def process_file(path: str):
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

    return make_post(meta, path)


def write_file(filepath: str, text: str):
    with open(filepath, "w") as file:
        file.writelines(text)


def make_post(meta: dict[str, str], path: str) -> Post:
    author = meta["author"]
    post_date = datetime.strptime(meta["date"], "%Y-%m-%d").date()
    exclude = meta["exclude"].lower() == "true" if "exclude" in meta else False
    as_part = meta["as_part"].lower() == "true" if "as_part" in meta else False
    no_wrapper = meta["no_wrapper"].lower() == "true" if "no_wrapper" in meta else False
    fixed_filename = meta["fixed_filename"] if "fixed_filename" in meta else ""

    post = Post(
        path=path,
        author=author,
        date=post_date,
        raw_date=meta["date"],
        exclude=exclude,
        as_part=as_part,
        no_wrapper=no_wrapper,
        fixed_filename=fixed_filename)

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

    if not post.exclude:
        variants_text = f"<ul hidden>"
        for lang in post.variants:
            variant = post.variants[lang]
            variants_text += f"""<a variant="{lang}" hidden href="/posts/generated/{variant.filename(lang)}.html">{lang}</a>"""
        variants_text += "</ul>"
    else:
        variants_text = ""

    if not post.no_wrapper:
        for lang in post.variants:
            variant = post.variants[lang]
            variant.date = format_date(post.date, locale=lang)
            variant.processed = "<article>"
            variant.processed += f"{variants_text}"
            variant.processed += f"<time>{variant.date}</time>"
            variant.processed += f"<cite>{post.author}</cite>"
            variant.processed += f"<h2>{variant.title}</h2>"
            variant.processed += variant.body
            variant.processed += "</article>"
    else:
        for lang in post.variants:
            variant = post.variants[lang]
            variant.processed += variant.body

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
        if not post.exclude:
            if lang not in latest_posts:
                latest_posts[lang] = variant
            else:
                if variant.post.date > latest_posts[lang].post.date:
                    latest_posts[lang] = variant

        langs.append(lang)
        filename = variant.filename(lang)
        current["date-"+lang] = variant.date
        current["title-"+lang] = variant.title
        current["url-"+lang] = "posts/generated/" + filename + ".html"

        outpath = path.join(root, "generated", filename)
        if not post.as_part:
            write_file(outpath + ".src.html", page_wrapper(variant.processed))
        else:
            write_file(outpath + ".part.html", variant.processed)

    current["langs"] = langs
    if not post.exclude:
        post_list.append(current)

postlist = """<ul class="postlist">"""
processed.sort(key=lambda p: p.date)
for post in processed:
    if post.exclude:
        continue

    lang = "hr"
    var = post.variants.get(lang)

    if var is None:
        for l, v in post.variants.items():
            lang = l
            var = v
            break

    if var is None:
        perr(f"Warning: Post {post.path} has no variants!")
        continue

    postlist += "<li>"
    postlist += f"""<time>{var.date}</time>"""
    postlist += f"""<a prepare href="posts/generated/{var.filename(lang)}.html">{var.title}</a>"""
    postlist +="</li>"

postlist += "</ul>"
outpath = path.join(root, "generated", "postlist.part.html")
write_file(outpath, postlist)

for lang, variant in latest_posts.items():
    outpath = path.join(root, "generated", f"latest-{lang}")
    write_file(outpath + ".src.html", page_wrapper(variant.processed))
    write_file(outpath + ".part.html", variant.processed)

outpath = path.join(root, "index.json")
write_file(outpath, dumps(post_list))
psucc(f"Processed {len(processed)} post(s), catalogued {len(post_list)} post(s).")
