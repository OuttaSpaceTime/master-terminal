import re
import pathlib
import warnings

import pytest

WIKI = pathlib.Path(__file__).resolve().parent.parent / "wiki"
PAGES = sorted(p for p in WIKI.glob("*.md") if p.name != "index.md")
MAX_LINES = 150


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else None


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_page_frontmatter(page):
    front = frontmatter(page.read_text())
    assert front is not None, "no frontmatter"
    for key in ("title", "tags", "created", "updated"):
        assert re.search(rf"^{key}:", front, re.M), f"missing {key}"
    assert re.search(r"^updated:\s*\d{4}-\d{2}-\d{2}\s*$", front, re.M), "updated is not YYYY-MM-DD"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_page_links_resolve(page):
    for target in re.findall(r"\]\(([^)#:]+\.md)(?:#[^)]*)?\)", page.read_text()):
        assert (WIKI / target).exists(), f"broken link to {target}"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_page_size(page):
    lines = page.read_text().count("\n")
    if lines > MAX_LINES:
        warnings.warn(f"{page.name}: {lines} lines, over {MAX_LINES}: trim history or split the topic")


def test_index_matches_pages():
    linked = set(re.findall(r"\]\(([^)#]+\.md)\)", (WIKI / "index.md").read_text()))
    names = {p.name for p in PAGES}
    assert names - linked == set(), "pages missing from index.md"
    assert linked - names == set(), "index.md links to missing pages"
