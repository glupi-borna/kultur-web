#!/usr/bin/env python3.9

from sys import argv
from os import path
from dataclasses import dataclass, field
from datetime import date, datetime
import textwrap
from babel.dates import format_date
from json import dumps
from slugify import slugify

root = path.dirname(__file__)
args = argv[1:]

def dedent(text):
    return textwrap.dedent(text.strip("\n"))


def page_wrapper(page):
    return f"""<!DOCTYPE html>
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <link href="style.css" rel="stylesheet" />
            <script src="main.js"></script>
        </head>
        <body>
            <header>
                <a href="index.html">
                    <img src="assets/kultur-logo-2-black.svg" alt="KulTur logo" />
                    <h1>KULTUR</h1>
                </a>
                <nav>
                    <ul>
                        <li><a trans=home href="index.html">Početna</a></li>
                        <li><a trans=about href="about.html">O nama</a></li>
                        <li><a trans=projects href="projects.html">Projekti</a></li>
                        <div class="spacer"></div>
                        <li><a action=language></a></li>
                        <li><a action=theme>
                            <div class="theme-button">
                                <img src="assets/kultur-logo-2-black.svg" alt="KulTur logo" />
                            </div>
                        </a></li>
                    </ul>
                </nav>
            </header>
            <main>
                <article>
                    {page}
                </article>
            </main>
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
        return f"{self.post.raw_date}-{lang}-{nice_title}.html"


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
        variant.processed = dedent(f"""
            <time>{variant.date}</time>
            <cite>{post.author}</cite>
            <h2>{variant.title}</h2>""") + variant.body

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
        current["url-"+lang] = "posts/" + filename

        outpath = path.join(root, filename)
        with open(outpath, "w") as file:
            file.writelines(page_wrapper(variant.processed))

    current["langs"] = langs
    post_list.append(current)

for lang, variant in latest_posts.items():
    outpath = path.join(root, f"latest-{lang}.html")
    with open(outpath, "w") as file:
        file.writelines(page_wrapper(variant.processed))

outpath = path.join(root, "index.json")
with open(outpath, "w") as file:
    file.writelines(dumps(post_list))

