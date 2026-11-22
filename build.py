#!/usr/bin/env -S uv run

import os
import re
import shutil
import subprocess
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

BASE = Path(__file__).parent
CONTENT = BASE / "content"
OUT = BASE / "public"

env = Environment(loader=FileSystemLoader(BASE / "templates"))
layout = env.get_template("base.j2")


def git(*args):
    try:
        return subprocess.run(
            ["git", *args], cwd=BASE, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def version():
    return git("rev-parse", "--short", "HEAD") or os.environ.get("GITHUB_SHA", "dev")[:7]


def repo():
    if os.environ.get("GITHUB_REPOSITORY"):
        return os.environ["GITHUB_REPOSITORY"]
    remote = git("remote", "get-url", "origin")
    match = re.search(r"github\.com[:/](.+?)(?:\.git)?/?$", remote)
    return match.group(1) if match else ""


def commit_url(rev):
    name = repo()
    if not name or rev == "dev":
        return ""
    return f"https://github.com/{name}/commit/{rev}"


def main():
    rev = version()
    url = commit_url(rev)

    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(BASE / "root", OUT)
    shutil.copytree(BASE / "static", OUT / "static")

    for src in sorted(CONTENT.glob("*.md")):
        title = "" if src.stem == "index" else src.stem.replace("-", " ").title()
        body = markdown.markdown(src.read_text(), extensions=["tables", "fenced_code"])
        dest = OUT / f"{src.stem}.html"
        dest.write_text(layout.render(title=title, content=body, version=rev, version_url=url))
        print(f"{src.name} -> {dest.name}")


if __name__ == "__main__":
    main()
