#!/usr/bin/env python3.9

from os import path, mkdir
from PIL import Image
from io import BytesIO
from json import dumps, loads
from colorama import Fore, Style
from opengraph import OpenGraph
import requests

root = path.dirname(__file__)
CACHE_PATH = path.join(root, "news.cache")
ASSETS_GENERATED_PATH = path.join(root, "..", "assets", "generated")
GENERATED_PATH = path.join(root, "generated")
LINKS_PATH = path.join(root, "news.links")
POST_PATH = path.join(root, "news.post")

def wrap_output(text: str):
    return f'''
date: 2022-7-15
author: Borna Lang
exclude: true
no_wrapper: true
fixed_filename: news

title-hr: Novosti
post-hr: """
<h2>Novosti</h2>

<ul class="news">
    {text}
</ul>
"""

title-en: News
post-en: """
<h2>News</h2>

<ul class="news">
    {text}
</ul>
"""
'''


def write_file(filepath: str, text: str):
    with open(filepath, "w") as file:
        file.writelines(text)

if not path.exists(ASSETS_GENERATED_PATH):
    mkdir(ASSETS_GENERATED_PATH)

if not path.exists(CACHE_PATH):
    write_file(CACHE_PATH, "{}")

def perr(text: str):
    print(f"{Fore.RED}{Style.BRIGHT}{text}{Fore.RESET}{Style.RESET_ALL}")


def psucc(text: str):
    print(f"{Fore.GREEN}{Style.BRIGHT}{text}{Fore.RESET}{Style.RESET_ALL}")


def is_whitespace(text: str):
    for ch in text:
        if ch not in (" ", "\n", "\t"):
            return False
    return True


def news_element(url: str, title: str, imgurl: str, site: str):
    return f"""
        <li><figure>
        <a href="{url}">
            <img src="{imgurl}" alt="{title}">
            <figcaption>{title}</figcaption>
            <cite>{site}</cite>
        </a>
        </figure></li>
    """


def process_news():
    indexed = 0

    with open(LINKS_PATH, "r") as file:
        urls = [l.strip() for l in file.readlines() if l.strip()]

    with open(CACHE_PATH, "r") as file:
        json = "".join(file.readlines())
        cache_data = loads(json)

    print(f"Indexing {len(urls)} news links...")

    out = ""

    for url in urls:
        if url not in cache_data:
            meta = OpenGraph(url=url)

            if not meta.is_valid():
                perr(f"URL '{url}' cannot be parsed with opengraph!")
                continue
            cache_data[url] = meta
            indexed += 1
        else:
            meta = cache_data[url]

        img = meta["image"].split("?")[0]
        href = meta["url"]
        site = meta["site_name"]
        title = meta["title"]

        img_name = path.split(img)[-1]
        img_name = ".".join(img_name.split(".")[:-1]) + ".jpeg"
        img_path = path.join(ASSETS_GENERATED_PATH, img_name)

        if not path.exists(img_path):
            req = requests.get(img)
            if req.status_code != 200:
                perr(f"Got status code {img_data.status_code} when trying to fetch image for link '{url}'!")
                continue
            img_data = BytesIO(req.content)
            img = Image.open(img_data)
            img_data = BytesIO()
            img.save(img_path, "JPEG", optimize=True, quality=70)

        out += news_element(href, title, f"/assets/generated/{img_name}", site)

    write_file(CACHE_PATH, dumps(cache_data))
    write_file(POST_PATH, wrap_output(out))
    psucc(f"Indexing finished, indexed {indexed} new links!")

process_news()
