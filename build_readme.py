import pathlib
import re
import urllib.request
import json
from xml.etree import ElementTree

ROOT = pathlib.Path(__file__).parent.resolve()

ATOM_FEED_URL = "https://mdaisuke.net/atom.xml"
TIL_FEED_URL = "https://raw.githubusercontent.com/DaisukeMiyazaki/TIL/main/feed.xml"
GITHUB_USER = "DaisukeMiyazaki"
GITHUB_REPOS_URL = f"https://api.github.com/users/{GITHUB_USER}/repos?sort=updated&per_page=5&type=owner"


def fetch_blog_posts(n=5):
    req = urllib.request.Request(ATOM_FEED_URL)
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml = resp.read()
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ElementTree.fromstring(xml)
    entries = root.findall("atom:entry", ns)[:n]
    posts = []
    for entry in entries:
        title = entry.find("atom:title", ns).text
        link = entry.find("atom:link", ns).attrib["href"]
        updated = entry.find("atom:updated", ns).text[:10]
        posts.append({"title": title, "url": link, "date": updated})
    return posts


def fetch_til_entries(n=5):
    req = urllib.request.Request(TIL_FEED_URL)
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml = resp.read()
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ElementTree.fromstring(xml)
    entries = root.findall("atom:entry", ns)[:n]
    items = []
    for entry in entries:
        title = entry.find("atom:title", ns).text
        link = entry.find("atom:link", ns).attrib["href"]
        updated = entry.find("atom:updated", ns).text[:10]
        items.append({"title": title, "url": link, "date": updated})
    return items


def fetch_recent_repos(n=5):
    req = urllib.request.Request(GITHUB_REPOS_URL)
    req.add_header("Accept", "application/vnd.github.v3+json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        repos = json.loads(resp.read())
    results = []
    for repo in repos[:n]:
        if repo.get("fork"):
            continue
        results.append({
            "name": repo["name"],
            "url": repo["html_url"],
            "description": repo.get("description") or "",
            "updated": repo["updated_at"][:10],
        })
    return results[:n]


def replace_section(content, marker, new_content):
    pattern = re.compile(
        rf"(<!-- {marker} starts -->).+?(<!-- {marker} ends -->)",
        re.DOTALL,
    )
    return pattern.sub(
        rf"\1\n{new_content}\n\2",
        content,
    )


if __name__ == "__main__":
    readme = (ROOT / "README.md").read_text()

    # Blog posts
    posts = fetch_blog_posts()
    posts_md = "\n".join(
        f"* [{p['title']}]({p['url']}) - {p['date']}" for p in posts
    )
    readme = replace_section(readme, "blog", posts_md)

    # TIL
    til_entries = fetch_til_entries()
    til_md = "\n".join(
        f"* [{t['title']}]({t['url']}) - {t['date']}" for t in til_entries
    )
    readme = replace_section(readme, "til", til_md)

    # Recent repos
    repos = fetch_recent_repos()
    repos_md = "\n".join(
        f"* [{r['name']}]({r['url']}) - {r['description']}" for r in repos
    )
    readme = replace_section(readme, "repos", repos_md)

    (ROOT / "README.md").write_text(readme)
