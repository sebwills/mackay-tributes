import csv
import html
import json
import os
import re
import shutil
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"

CATEGORY_INFO = {
    "CLARITY": "His intellectual strengths, first-principles thinking and insight.",
    "INFORMATION_THEORY": "His work on information theory (outside ITILA).",
    "ITILA": "Mentions of the book ITILA and its influence.",
    "SEWTHA": "Mentions of SEWTHA and sustainability work.",
    "DASHER": "His work on accessibility for disabled people.",
    "PERSON": "His humanity, generosity, bravery, campaigning, and genuineness.",
}


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value.strip())
    value = re.sub(r"-+", "-", value)
    return value or "unknown"


def format_paragraphs(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    blocks = re.split(r"\n\s*\n", text)
    rendered = []
    for block in blocks:
        block = re.sub(r"\s+", " ", block.replace("\n", " ")).strip()
        block = smart_typography(block)
        block = html.escape(block)
        block = enrich_acronyms(block)
        rendered.append(f"<p>{block}</p>")
    return "\n".join(rendered)


def smart_typography(text: str) -> str:
    text = text.replace("--", "—")
    result = []
    open_double = True
    open_single = True
    for i, ch in enumerate(text):
        if ch == '"':
            result.append("“" if open_double else "”")
            open_double = not open_double
        elif ch == "'":
            prev = text[i - 1] if i > 0 else ""
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if prev.isalnum() and nxt.isalnum():
                result.append("’")
            else:
                result.append("‘" if open_single else "’")
                open_single = not open_single
        else:
            result.append(ch)
    return "".join(result)


def enrich_acronyms(text: str) -> str:
    def repl(match):
        key = match.group(0)
        if key == "SEWTHA":
            return (
                '<span class="acronym" data-tooltip="Sustainable Energy Without the Hot Air">'
                '<a href="https://withouthotair.com">SEWTHA</a></span>'
            )
        if key == "ITILA":
            return (
                '<span class="acronym" data-tooltip="Information Theory, Inference, and Learning Algorithms">'
                '<a href="https://www.inference.org.uk/mackay/itila/book.html">ITILA</a></span>'
            )
        return key

    return re.sub(r"\b(SEWTHA|ITILA)\b", repl, text)


def asset_prefix(depth: int) -> str:
    if depth <= 0:
        return "."
    return "/".join([".."] * depth)


def load_template(name: str) -> str:
    return (SRC / "templates" / name).read_text(encoding="utf-8")


def render_page(template: str, **context) -> str:
    for key, value in context.items():
        template = template.replace(f"${key}", value)
    return template


def write_page(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_config():
    return json.loads((SRC / "site.json").read_text(encoding="utf-8"))


def load_tributes():
    tributes = []
    with (ROOT / "tributes.csv").open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tributes.append({
                "section": row.get("Section", "").strip(),
                "name": row.get("Name", "").strip(),
                "name_index": row.get("Name_for_index", "").strip(),
                "how": row.get("How_knew_David", "").strip(),
                "tribute": row.get("Tribute", "").strip(),
            })
    return tributes


def build():
    config = load_config()
    base_url = config.get("base_url", "").rstrip("/")
    template = load_template("page.html")
    default_title = config.get("site_title", "Tributes")
    header_title = config.get("header_title", default_title)
    hero_title = config.get("hero_title", default_title)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)

    # Copy assets
    shutil.copytree(SRC / "assets", DIST / "assets")
    shutil.copytree(ROOT / "images", DIST / "images")

    tributes = load_tributes()

    for tribute in tributes:
        tribute["section_slug"] = slugify(tribute["section"])
        index_name = tribute["name_index"] or tribute["name"]
        tribute["author_slug"] = slugify(index_name) if index_name else "unknown"
        tribute["author_sort"] = index_name.lower() if index_name else "unknown"

    categories = {}
    authors = {}
    for tribute in tributes:
        categories.setdefault(tribute["section"], []).append(tribute)
        authors.setdefault(tribute["author_slug"], []).append(tribute)

    # Home page
    summary_html = "\n".join(f"<p>{html.escape(line)}</p>" for line in config.get("summary", []))
    carousel_items = []
    for tribute in tributes:
        tribute_html = format_paragraphs(tribute["tribute"])
        meta = html.escape(tribute["name"] or "Anonymous")
        how = html.escape(tribute["how"]) if tribute["how"] else ""
        meta_line = f"<strong>{meta}</strong>" + (f" — {how}" if how else "")
        carousel_items.append(
            f"<div class=\"carousel-item\">\n"
            f"  <div class=\"carousel-tribute\">{tribute_html}</div>\n"
            f"  <div class=\"carousel-meta\">{meta_line}</div>\n"
            f"</div>"
        )

    carousel_markup = "\n".join(carousel_items)
    home_content = f"""
<section class=\"hero\">
  <div>
    <h1>{html.escape(hero_title)}</h1>
    {summary_html}
    <div class=\"cta\">
      <a class=\"button primary\" href=\"./category/index.html\">Browse by category</a>
      <a class=\"button\" href=\"./author/index.html\">Browse by author</a>
    </div>
  </div>
  <div class=\"hero-photo\">
    <img src=\"./{html.escape(config.get('image', ''))}\" alt=\"Portrait of Sir David MacKay\" />
    <div class=\"caption\">Photo: David Stern (CC licensed)</div>
  </div>
</section>

<section>
  <h2 class=\"section-title\">A few voices from the archive</h2>
  <div class=\"carousel\" data-carousel>
    <div class=\"carousel-controls\">
      <button class=\"button\" data-carousel-prev>Previous</button>
      <button class=\"button\" data-carousel-next>Next</button>
    </div>
    <div class=\"carousel-items\">
      {carousel_markup}
    </div>
  </div>
</section>
"""

    draft_badge = "<span class=\"draft-badge\">DRAFT</span>" if config.get("is_draft") else ""
    home_html = render_page(
        template,
        title=hero_title,
        canonical=f"{base_url}/" if base_url else "",
        description="Tributes collected for Sir David MacKay FRS.",
        asset_prefix=asset_prefix(0),
        page_class="home",
        site_title=html.escape(header_title) + draft_badge,
        content=home_content,
        page_script="",
    )
    write_page(DIST / "index.html", home_html)

    # Category index
    category_cards = []
    for section, items in sorted(categories.items()):
        slug = slugify(section)
        count = len(items)
        desc = CATEGORY_INFO.get(section, "")
        category_cards.append(
            f"<a class=\"card\" href=\"./{slug}/index.html\">\n"
            f"  <h3 class=\"card-title\">{html.escape(section.title().replace('_', ' '))}</h3>\n"
            f"  <p>{html.escape(desc)}</p>\n"
            f"  <div class=\"card-meta\">{count} tributes</div>\n"
            f"</a>"
        )

    category_cards_markup = "\n".join(category_cards)
    category_index_content = f"""
<section>
  <h1 class=\"section-title\">Browse by category</h1>
  <div class=\"list-grid\">
    {category_cards_markup}
  </div>
</section>
"""

    category_index_html = render_page(
        template,
        title="Browse by category",
        canonical=f"{base_url}/category/" if base_url else "",
        description="Tribute categories.",
        asset_prefix=asset_prefix(1),
        page_class="category-index",
        site_title=html.escape(header_title) + draft_badge,
        content=category_index_content,
        page_script="",
    )
    write_page(DIST / "category" / "index.html", category_index_html)

    # Category pages
    category_keys = sorted(categories.keys())
    for section in category_keys:
        items = categories[section]
        slug = slugify(section)
        desc = CATEGORY_INFO.get(section, "")
        cards = []
        for tribute in items:
            tribute_html = format_paragraphs(tribute["tribute"])
            author = html.escape(tribute["name"] or "Anonymous")
            how = html.escape(tribute["how"]) if tribute["how"] else ""
            meta = f"<strong>{author}</strong>" + (f" — {how}" if how else "")
            cards.append(
                f"<article class=\"tribute-card\">\n"
                f"  <div class=\"tribute-text\">{tribute_html}</div>\n"
                f"  <div class=\"tribute-meta\">{meta}</div>\n"
                f"</article>"
            )

        cards_markup = "\n".join(cards)
        content = f"""
<section class=\"tribute-page\">
  <div class=\"tribute-header\">
    <div class=\"title-block\">
      <h1 class=\"section-title\">{html.escape(section.title().replace('_', ' '))}</h1>
      <p class=\"caption\">{html.escape(desc)}</p>
    </div>
    <div class=\"tribute-nav\">
      <a class=\"button\" href=\"../index.html\">Back to categories</a>
    </div>
  </div>
  <div class=\"tribute-list\" data-shuffle=\"true\">
    {cards_markup}
  </div>
</section>
"""

        page_html = render_page(
            template,
            title=f"{section.title().replace('_', ' ')} tributes",
            canonical=f"{base_url}/category/{slug}/" if base_url else "",
            description=f"Tributes in the {section} category.",
            asset_prefix=asset_prefix(2),
            page_class="category-page",
            site_title=html.escape(header_title) + draft_badge,
            content=content,
            page_script="",
        )
        write_page(DIST / "category" / slug / "index.html", page_html)

    # Author index
    author_cards = []
    for slug, items in sorted(authors.items(), key=lambda x: x[1][0]["author_sort"]):
        display = items[0]["name"] or "Anonymous"
        count = len(items)
        meta = f"<div class=\"card-meta\">{count} tribute{'s' if count != 1 else ''}</div>" if count > 1 else ""
        author_cards.append(
            f"<a class=\"card\" href=\"./{slug}/index.html\">\n"
            f"  <h3 class=\"card-title\">{html.escape(display)}</h3>\n"
            f"  {meta}\n"
            f"</a>"
        )

    author_cards_markup = "\n".join(author_cards)
    author_index_content = f"""
<section>
  <h1 class=\"section-title\">Browse by author</h1>
  <div class=\"list-grid\">
    {author_cards_markup}
  </div>
</section>
"""

    author_index_html = render_page(
        template,
        title="Browse by author",
        canonical=f"{base_url}/author/" if base_url else "",
        description="Tributes by author.",
        asset_prefix=asset_prefix(1),
        page_class="author-index",
        site_title=html.escape(header_title) + draft_badge,
        content=author_index_content,
        page_script="",
    )
    write_page(DIST / "author" / "index.html", author_index_html)

    # Author pages
    author_slugs = [slug for slug, _ in sorted(authors.items(), key=lambda x: x[1][0]["author_sort"])]
    for idx, slug in enumerate(author_slugs):
        items = authors[slug]
        display = items[0]["name"] or "Anonymous"
        prev_slug = author_slugs[idx - 1] if idx > 0 else author_slugs[-1]
        next_slug = author_slugs[idx + 1] if idx + 1 < len(author_slugs) else author_slugs[0]
        panels = []
        for tribute in items:
            tribute_html = format_paragraphs(tribute["tribute"])
            how = html.escape(tribute["how"]) if tribute["how"] else ""
            meta = f"<strong>{html.escape(display)}</strong>" + (f" — {how}" if how else "")
            panels.append(
                f"<section class=\"tribute-panel\">\n"
                f"  <div class=\"tribute-body\">{tribute_html}</div>\n"
                f"  <div class=\"tribute-meta\">{meta}</div>\n"
                f"</section>"
            )

        panels_markup = "\n".join(panels)
        content = f"""
<section class=\"tribute-page\">
  <div class=\"tribute-header\">
    <div class=\"title-block\">
      <h1 class=\"section-title\">{html.escape(display)}</h1>
    </div>
    <div class=\"tribute-nav\">
      <a class=\"button\" href=\"../index.html\">Back to authors</a>
      <button class=\"button\" data-tribute-prev>Previous</button>
      <button class=\"button primary\" data-tribute-next>Next</button>
    </div>
  </div>
  <div class=\"tribute-shell\" data-prev-page=\"../{prev_slug}/index.html\" data-next-page=\"../{next_slug}/index.html\">
    <div class=\"tribute-track\" data-tribute-track data-shuffle=\"true\">
      {panels_markup}
    </div>
  </div>
</section>
"""

        page_html = render_page(
            template,
            title=f"Tribute by {display}",
            canonical=f"{base_url}/author/{slug}/" if base_url else "",
            description=f"Tributes by {display}.",
            asset_prefix=asset_prefix(2),
            page_class="author-page",
            site_title=html.escape(header_title) + draft_badge,
            content=content,
            page_script="",
        )
        write_page(DIST / "author" / slug / "index.html", page_html)


if __name__ == "__main__":
    build()
