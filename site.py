#!/usr/bin/env python3
"""Build the Rush NLP website without a Jekyll runtime.

The original HTML, Markdown, YAML data, and static files remain the source of
truth.  Run ``python site.py`` to write a deployable static website to ``docs``.
"""

from __future__ import annotations

import html
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any

import markdown
import yaml


ROOT = Path(__file__).parent
OUTPUT = ROOT / "docs"
STATIC_DIRECTORIES = ("cv", "images", "logos", "meetings", "papers", "slides")
NAVIGATION = (
    ("Main", "/"),
    ("Blog", "/blog/"),
    ("Group", "/members/"),
    ("Projects", "/projects/"),
    ("Publications", "/papers/"),
)


def load_data(name: str) -> Any:
    with (ROOT / "_data" / f"{name}.yaml").open(encoding="utf-8") as source:
        return yaml.safe_load(source)


def split_front_matter(source: str) -> tuple[dict[str, Any], str]:
    if not source.startswith("---"):
        return {}, source
    _, front_matter, body = source.split("---", 2)
    return yaml.safe_load(front_matter) or {}, body.lstrip()


def resolve(expression: str, context: dict[str, Any], data: dict[str, Any]) -> Any:
    expression = expression.strip()
    if expression.startswith("site.data."):
        value: Any = data
        pieces = expression.split(".")[2:]
    else:
        pieces = expression.split(".")
        value = context.get(pieces.pop(0), "")
    for piece in pieces:
        if isinstance(value, dict):
            value = value.get(piece, "")
        else:
            value = getattr(value, piece, "")
    return value


def render_liquid(template: str, context: dict[str, Any], data: dict[str, Any]) -> str:
    loop = re.compile(r"{%\s*for\s+(\w+)\s+in\s+(.+?)\s*%}(.*?){%\s*endfor\s*%}", re.S)
    condition = re.compile(r"{%\s*if\s+(.+?)\s*%}(.*?)(?:{%\s*else\s*%}(.*?))?{%\s*endif\s*%}", re.S)

    def expand_loop(match: re.Match[str]) -> str:
        variable, collection, inner = match.groups()
        entries = resolve(collection, context, data) or []
        return "".join(render_liquid(inner, {**context, variable: item}, data) for item in entries)

    while loop.search(template):
        template = loop.sub(expand_loop, template)

    def expand_condition(match: re.Match[str]) -> str:
        key, truthy, falsy = match.groups()
        return render_liquid(truthy if resolve(key, context, data) else (falsy or ""), context, data)

    template = condition.sub(expand_condition, template)
    template = re.sub(r"{{\s*'([^']+)'\s*\|\s*prepend:\s*site\.baseurl\s*}}", r"\1", template)
    template = template.replace("{{ BASE_PATH }}", "")

    def variable(match: re.Match[str]) -> str:
        return html.escape(str(resolve(match.group(1), context, data)), quote=False)

    return re.sub(r"{{\s*(.+?)\s*}}", variable, template)


def markdown_to_html(source: str) -> str:
    source = re.sub(r"{%\s*highlight\s+(\w+)\s*%}", r"```\1", source)
    source = re.sub(r"{%\s*endhighlight\s*%}", "```", source)
    source = source.replace("{:toc}", "")
    source = source.replace("{{ BASE_PATH }}", "")
    return markdown.markdown(source, extensions=["extra", "toc", "sane_lists"])


def page_shell(title: str, content: str, path: str) -> str:
    links = "".join(
        f'<a href="{href}" class="{"active" if href == path else ""}">{label}</a>'
        for label, href in NAVIGATION
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Rush NLP research, people, projects, and publications.">
  <title>{html.escape(title)} · Rush NLP</title>
  <link rel="stylesheet" href="/css/site.css">
</head>
<body>
  <header class="site-header"><div class="header-inner">
    <nav aria-label="Primary navigation">{links}</nav>
  </div></header>
  <main class="page-shell">{content}</main>
</body>
</html>"""


def write_page(path: str, title: str, content: str) -> None:
    clean_path = path.strip("/")
    if path == "/":
        destination = OUTPUT / "index.html"
    elif clean_path.endswith(".html"):
        destination = OUTPUT / clean_path
    else:
        destination = OUTPUT / clean_path / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page_shell(title, content, path), encoding="utf-8")


def build_people(groups: list[dict[str, Any]]) -> str:
    sections = []
    for group in groups:
        people = []
        for person in group["people"]:
            image = person.get("pic") or f"https://avatars2.githubusercontent.com/u/{person.get('githubid')}?v=3&s=400"
            name = html.escape(person["name"])
            title = html.escape(person.get("title") or "")
            url = html.escape(person.get("url") or "#", quote=True)
            people.append(f'''<a class="person-card" href="{url}">
              <img src="{html.escape(image, quote=True)}" alt="Portrait of {name}" loading="lazy">
              <span class="person-name">{name}</span>{f'<span class="person-role">{title}</span>' if title else ''}
            </a>''')
        sections.append(f'<section class="people-section"><h1>{html.escape(group["group"])}</h1><div class="people-grid">{"".join(people)}</div></section>')
    return "".join(sections)


def build_blog(posts: list[dict[str, Any]], content: dict[str, Any]) -> str:
    items = []
    latest_by_title = {post["title"]: post for post in reversed(posts)}
    for item in content["posts"]:
        title = item["title"]
        post = latest_by_title.get(title)
        link = item.get("link") or (post["path"] if post else "")
        heading = f'<a href="{html.escape(link, quote=True)}">{html.escape(title)}</a>' if link else html.escape(title)
        metadata = f'<p class="post-date">{post["display_date"]}</p>' if post else ""
        tags = " ".join(f'<span class="post-tag">{html.escape(tag)}</span>' for tag in post["tags"]) if post else ""
        excerpt = html.escape(post["excerpt"]) if post else ""
        items.append(f'''<article class="post-preview">
          {metadata}
          <h2>{heading}</h2>
          {f'<p>{excerpt}</p>' if excerpt else ''}
          {f'<p class="post-tags">{tags}</p>' if tags else ''}
        </article>''')
    return f'''<article class="prose blog-index">
      <h1>Blog</h1>
      {"".join(items)}
    </article>'''


def build_source_page(filename: str, path: str, data: dict[str, Any]) -> None:
    front_matter, body = split_front_matter((ROOT / filename).read_text(encoding="utf-8"))
    title = front_matter.get("title") or "Rush NLP"
    if filename == "index.html":
        home_copy = markdown_to_html((ROOT / "content" / "home.md").read_text(encoding="utf-8"))
        body = body.replace("{% home_copy %}", home_copy)
    body = render_liquid(body, {}, data)
    write_page(path, title, f'<article class="prose content-{Path(filename).stem}">{body}</article>')


def copy_static_files() -> None:
    for directory in STATIC_DIRECTORIES:
        shutil.copytree(ROOT / directory, OUTPUT / directory, dirs_exist_ok=True)
    for filename in ("CNAME", "SEAS.png", "bib-list.js", "bib-publication-list.css"):
        source = ROOT / filename
        if source.exists():
            shutil.copy2(source, OUTPUT / filename)


def build() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUTPUT / "css").mkdir()
    shutil.copy2(ROOT / "css" / "site.css", OUTPUT / "css" / "site.css")
    copy_static_files()

    data = {name: load_data(name) for name in ("members", "papers", "projects", "code", "meetings")}
    blog_content = yaml.safe_load((ROOT / "content" / "blog.yaml").read_text(encoding="utf-8"))
    build_source_page("index.html", "/", data)
    build_source_page("projects.html", "/projects/", data)
    build_source_page("papers.html", "/papers/", data)
    write_page("/members/", "Group", build_people(data["members"]))

    for filename, path in (("rawpapers.md", "/rawpapers/"), ("NamedTensor.md", "/NamedTensor.html"), ("NamedTensor2.md", "/NamedTensor2.html")):
        front_matter, body = split_front_matter((ROOT / filename).read_text(encoding="utf-8"))
        body = render_liquid(body, {}, data)
        write_page(path, front_matter.get("title") or Path(filename).stem, f'<article class="prose longform">{markdown_to_html(body)}</article>')

    for filename in ("latent-nlp-tutorial.html",):
        front_matter, body = split_front_matter((ROOT / filename).read_text(encoding="utf-8"))
        write_page(f"/{filename}", front_matter.get("title") or "Rush NLP", f'<article class="prose longform">{body}</article>')

    posts = []
    for source in (ROOT / "_posts").glob("*.markdown"):
        front_matter, body = split_front_matter(source.read_text(encoding="utf-8"))
        parsed_date, slug = source.stem[:10], source.stem[11:]
        year, month, day = parsed_date.split("-")
        rendered_post = markdown_to_html(body)
        post_title = front_matter.get("title") or slug
        post_path = f"/{year}/{month}/{day}/{slug}.html"
        write_page(post_path, post_title, f'<article class="prose longform">{rendered_post}</article>')
        posts.append({
            "date": parsed_date,
            "display_date": date.fromisoformat(parsed_date).strftime("%B %-d, %Y"),
            "excerpt": front_matter.get("excerpt", ""),
            "path": post_path,
            "tags": front_matter.get("tags", []),
            "title": post_title,
        })
        posts[-1]["feed_item"] = f"<item><title>{html.escape(post_title)}</title><description>{html.escape(rendered_post)}</description><pubDate>{parsed_date}</pubDate><link>{post_path}</link><guid isPermaLink=\"true\">{post_path}</guid></item>"

    posts.sort(key=lambda post: post["date"], reverse=True)
    write_page("/blog/", "Blog", build_blog(posts, blog_content))

    feed = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><rss version=\"2.0\"><channel><title>Rush NLP</title><description>Rush NLP research</description><link>/</link><lastBuildDate>" + str(date.today()) + "</lastBuildDate>" + "".join(post["feed_item"] for post in posts) + "</channel></rss>"
    (OUTPUT / "feed.xml").write_text(feed, encoding="utf-8")
    print(f"Built {OUTPUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    build()
