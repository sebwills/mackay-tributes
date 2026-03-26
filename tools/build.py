import argparse
import csv
import html
import json
import os
import re
import shutil
import time
import unicodedata
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"
CATEGORY_INTROS = SRC / "category_intros"
INTRO_URL_TEMPLATE = "https://raw.githubusercontent.com/pilgrimbeart/mackay/refs/heads/main/intro_{key}.md"
TRIBUTES_CSV = ROOT / "tributes.csv"
TRIBUTES_SHEET_EXPORT_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vSTHBL_p4dyp6P3e1Htfkv68EDi1W9POHJ17Xnr0BtnzyjsZC6MymfIu9dSmAa4v9-mH7J0mJWQei00/pub"
    "?gid=45077070&single=true&output=csv"
)
EXPECTED_TRIBUTES_COLUMNS = {
    "Section",
    "Name",
    "How_knew_David",
    "Tribute",
    "Name_for_index",
}


def log(message: str):
    print(f"[build] {message}")


def warn(message: str):
    print(f"[build] WARNING: {message}")


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
                '<span class="acronym" data-acronym>'
                '<button class="acronym-trigger" type="button" aria-expanded="false">SEWTHA</button>'
                '<span class="acronym-popover" hidden>'
                '<a class="acronym-link" href="https://withouthotair.com" target="_blank" rel="noreferrer noopener">'
                'Sustainable Energy Without the Hot Air&nbsp;<span class="acronym-link-icon" aria-hidden="true">&#10548;</span>'
                '</a>'
                '<button class="acronym-close" type="button" aria-label="Close expanded name">x</button>'
                '</span>'
                '</span>'
            )
        if key == "ITILA":
            return (
                '<span class="acronym" data-acronym>'
                '<button class="acronym-trigger" type="button" aria-expanded="false">ITILA</button>'
                '<span class="acronym-popover" hidden>'
                '<a class="acronym-link" href="https://www.inference.org.uk/mackay/itila/book.html" target="_blank" rel="noreferrer noopener">'
                'Information Theory, Inference, and Learning Algorithms&nbsp;<span class="acronym-link-icon" aria-hidden="true">&#10548;</span>'
                '</a>'
                '<button class="acronym-close" type="button" aria-label="Close expanded name">x</button>'
                '</span>'
                '</span>'
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


def category_metadata(config: dict) -> dict:
    metadata = {}
    for item in config.get("categories", []):
        key = item.get("key", "").strip()
        if not key:
            continue
        metadata[key] = {
            "heading": item.get("heading", key.title().replace("_", " ")).strip(),
            "short_description": item.get("short_description", "").strip(),
        }
    return metadata


def category_intro_path(key: str) -> Path:
    return CATEGORY_INTROS / f"intro_{key}.md"


def download_category_intro(key: str):
    url = INTRO_URL_TEMPLATE.format(key=key)
    target = category_intro_path(key)
    CATEGORY_INTROS.mkdir(parents=True, exist_ok=True)
    with urlopen(url) as response:
        content = response.read().decode("utf-8")
    target.write_text(content, encoding="utf-8")


def ensure_category_intro_files(category_keys, download_missing: bool):
    missing = [key for key in category_keys if not category_intro_path(key).exists()]
    if download_missing:
        log("Refreshing all category intro markdown files...")
        for key in category_keys:
            log(f"Downloading category intro for {key}...")
            download_category_intro(key)
        return
    if not missing:
        log("All category intro markdown files already present; no download needed.")
        return
    log(f"Downloading {len(missing)} missing category intro markdown file(s)...")
    for key in missing:
        log(f"Downloading category intro for {key}...")
        download_category_intro(key)


def extract_intro_body(markdown: str) -> str:
    match = re.search(r"^# .*$", markdown, flags=re.MULTILINE)
    if not match:
        return markdown.strip()
    return markdown[match.end():].strip()


def load_category_intro_html(key: str) -> str:
    path = category_intro_path(key)
    body = extract_intro_body(path.read_text(encoding="utf-8"))
    return format_paragraphs(body)


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def fetch_tributes_csv():
    log("Refreshing tributes.csv from published Google Sheet CSV...")
    url = f"{TRIBUTES_SHEET_EXPORT_URL}&_cb={time.time_ns()}"
    request = Request(
        url,
        headers={
            "User-Agent": "mackay-tributes-builder/1.0",
            "Cache-Control": "no-cache, max-age=0",
            "Pragma": "no-cache",
        },
    )
    with urlopen(request, timeout=30) as response:
        content = response.read().decode("utf-8-sig")

    rows = list(csv.reader(content.splitlines()))
    if not rows:
        raise ValueError("Downloaded tributes CSV was empty.")

    columns = set(rows[0])
    missing_columns = sorted(EXPECTED_TRIBUTES_COLUMNS - columns)
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Downloaded tributes CSV is missing expected column(s): {missing}")

    with TRIBUTES_CSV.open("w", encoding="utf-8", newline="") as f:
        f.write(content)
    log(f"Updated {TRIBUTES_CSV.name}.")


def load_tributes():
    tributes = []
    with TRIBUTES_CSV.open(newline="", encoding="utf-8") as f:
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


def resolve_author_identity(index_name: str, fallback_name: str):
    index_name = (index_name or "").strip()
    fallback_name = (fallback_name or "").strip() or "Anonymous"
    if "@" in index_name:
        sort_name, display_name = index_name.split("@", 1)
        sort_name = sort_name.strip() or fallback_name
        display_name = display_name.strip() or fallback_name
    else:
        sort_name = index_name or fallback_name
        display_name = index_name or fallback_name
    return sort_name, display_name


def build(download_category_intros: bool = False, update_tributes_csv: bool = True):
    if update_tributes_csv:
        fetch_tributes_csv()
    else:
        log("Skipping tributes.csv refresh; using local CSV.")

    config = load_config()
    base_url = config.get("base_url", "").rstrip("/")
    template = load_template("page.html")
    default_title = config.get("site_title", "Tributes")
    header_title = config.get("header_title", default_title)
    hero_title = config.get("hero_title", default_title)
    category_info = category_metadata(config)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)

    # Copy assets
    shutil.copytree(SRC / "assets", DIST / "assets")
    shutil.copytree(ROOT / "images", DIST / "images")

    tributes = load_tributes()
    log(f"Loaded {len(tributes)} tribute(s) from {TRIBUTES_CSV.name}.")

    for tribute in tributes:
        tribute["section_slug"] = slugify(tribute["section"])
        sort_name, display_name = resolve_author_identity(tribute["name_index"], tribute["name"])
        tribute["author_display"] = display_name
        tribute["author_slug"] = slugify(display_name)
        tribute["author_sort"] = sort_name.lower()

    categories = {}
    authors = {}
    uncategorized = []
    for tribute in tributes:
        if tribute["section"]:
            categories.setdefault(tribute["section"], []).append(tribute)
        else:
            uncategorized.append(tribute)
        authors.setdefault(tribute["author_slug"], []).append(tribute)

    if uncategorized:
        names = ", ".join(
            tribute["name"] or tribute["author_display"] or "Anonymous"
            for tribute in uncategorized
        )
        warn(
            f"Found {len(uncategorized)} tribute(s) without a category; they will appear on author pages only. "
            f"Authors: {names}"
        )

    ensure_category_intro_files(sorted(categories.keys()), download_category_intros)

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
      <a class=\"button primary\" href=\"./category/\">Browse by category</a>
      <a class=\"button\" href=\"./author/\">Browse by author</a>
      <a class=\"button\" href=\"./carousel/\">Carousel</a>
      <a class=\"button\" href=\"https://forms.gle/mtSp5WvYWQ6MYse87\">Submit a Tribute</a>
    </div>
  </div>
  <div class=\"hero-photo\">
    <img src=\"./{html.escape(config.get('image', ''))}\" alt=\"Portrait of Sir David MacKay\" />
    <div class=\"caption\">Photo: David Stern (CC licensed)</div>
  </div>
</section>

<section>
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

    def header_nav_markup(asset_prefix_value: str) -> str:
        return f"""
      <nav class=\"site-nav\" data-site-nav>
        <a href=\"https://forms.gle/mtSp5WvYWQ6MYse87\">Submit a Tribute</a>
        <a href=\"{asset_prefix_value}/carousel/\">Carousel</a>
        <a href=\"{asset_prefix_value}/about/\">About</a>
        <a href=\"{asset_prefix_value}/category/\">Browse by category</a>
        <a href=\"{asset_prefix_value}/author/\">Browse by author</a>
      </nav>""".strip()

    home_html = render_page(
        template,
        title=hero_title,
        canonical=f"{base_url}/" if base_url else "",
        description="Tributes collected for Sir David MacKay FRS.",
        asset_prefix=asset_prefix(0),
        page_class="home",
        site_title=html.escape(header_title) + draft_badge,
        header_right=header_nav_markup(asset_prefix(0)),
        content=home_content,
        page_script="",
    )
    write_page(DIST / "index.html", home_html)

    # Showcase carousel page
    showcase_items = []
    for tribute in tributes:
        tribute_html = format_paragraphs(tribute["tribute"])
        meta = html.escape(tribute["name"] or "Anonymous")
        how = html.escape(tribute["how"]) if tribute["how"] else ""
        meta_line = f"<strong>{meta}</strong>" + (f" — {how}" if how else "")
        words = count_words(tribute["tribute"])
        showcase_items.append(
            f"<article class=\"showcase-card\" data-showcase-item data-words=\"{words}\">\n"
            f"  <div class=\"showcase-card-inner\">\n"
            f"    <div class=\"showcase-tribute-viewport\">\n"
            f"      <div class=\"showcase-tribute\">{tribute_html}</div>\n"
            f"    </div>\n"
            f"    <div class=\"showcase-meta\">{meta_line}</div>\n"
            f"    <div class=\"showcase-progress\" aria-hidden=\"true\"><div class=\"showcase-progress-bar\" data-showcase-progress></div></div>\n"
            f"  </div>\n"
            f"</article>"
        )

    showcase_markup = "\n".join(showcase_items)
    showcase_content = f"""
<section class=\"showcase-page-shell\" data-showcase>
  <div class=\"showcase-settings\">
    <button class=\"showcase-gear\" type=\"button\" aria-label=\"Show carousel speed settings\" aria-expanded=\"false\" data-showcase-gear>⚙</button>
    <div class=\"showcase-controls\" hidden data-showcase-controls>
      <div class=\"showcase-controls-label\">Advance speed</div>
      <div class=\"showcase-speed-options\">
        <button class=\"showcase-speed-button\" type=\"button\" data-showcase-speed=\"0.8\">Slower</button>
        <button class=\"showcase-speed-button\" type=\"button\" data-showcase-speed=\"1\">Normal</button>
        <button class=\"showcase-speed-button\" type=\"button\" data-showcase-speed=\"1.25\">Faster</button>
      </div>
      <label class=\"showcase-toggle\" for=\"showcase-event-mode\">
        <span class=\"showcase-controls-label showcase-controls-label-inline\">Event mode</span>
        <input id=\"showcase-event-mode\" class=\"showcase-toggle-input\" type=\"checkbox\" data-showcase-event-toggle />
        <span class=\"showcase-toggle-ui\" aria-hidden=\"true\"></span>
      </label>
      <div class=\"showcase-controls-links\" data-showcase-controls-links>
        <a href=\"https://forms.gle/mtSp5WvYWQ6MYse87\">Submit a Tribute</a>
        <a href=\"../\">Home</a>
        <a href=\"../about/\">About</a>
        <a href=\"../category/\">Browse by category</a>
        <a href=\"../author/\">Browse by author</a>
      </div>
    </div>
  </div>
  <div class=\"showcase-stage\" data-showcase-stage>
    {showcase_markup}
  </div>
</section>
"""

    showcase_html = render_page(
        template,
        title="Tribute Carousel",
        canonical=f"{base_url}/carousel/" if base_url else "",
        description="Projection-friendly rotating tribute showcase.",
        asset_prefix=asset_prefix(1),
        page_class="showcase-page",
        site_title=html.escape(header_title) + draft_badge,
        header_right=f"""
      <div class=\"showcase-header-right\" data-showcase-header-right>
        {header_nav_markup(asset_prefix(1))}
        <div class=\"showcase-event-banner\" data-showcase-event-banner>
          <div class=\"showcase-event-copy\">
            <span class=\"showcase-event-site\">davidmackay.uk</span>
            <span class=\"showcase-event-separator\"> - </span>
            <span class=\"showcase-event-label\">submit a tribute:</span>
          </div>
          <img class=\"showcase-event-qr\" src=\"{asset_prefix(1)}/images/submit_QR.png\" alt=\"QR code for submitting a tribute\" />
        </div>
      </div>""".strip(),
        content=showcase_content,
        page_script="",
    )
    write_page(DIST / "carousel" / "index.html", showcase_html)

    about_content = """
<section>
  <h1 class=\"section-title\">About</h1>
  <div class=\"tribute-card\">
    <div class=\"tribute-text\">
      <p>David J. C. MacKay (1967-2016) combined clarity of thought with kindness and curiosity, changing people’s lives directly and indirectly across many different subjects. He had a rare talent for turning messy questions into crisp, checkable reasoning and an insistence on numbers, not adjectives, delivered with wit, warmth and compassion.</p>
      <p>This website gathers recollections from people who knew David either personally or through his works: as teacher, colleague, collaborator, creator, mentor and friend. Varied in style and length, together they aim to preserve something of his voice and influence.</p>
      <p>We’ve attempted the hopeless task of organising them by topic, but inevitably there’s a lot of overlap because, as David was fond of saying, “everything is connected”.</p>
      <p class=\"caption\">Compiled and introduced by Pilgrim Beart with assistance from Seb Wills, March 2026.</p>
    </div>
  </div>
</section>
"""

    about_html = render_page(
        template,
        title="About",
        canonical=f"{base_url}/about/" if base_url else "",
        description="About this tribute website for David J. C. MacKay.",
        asset_prefix=asset_prefix(1),
        page_class="about-page",
        site_title=html.escape(header_title) + draft_badge,
        header_right=header_nav_markup(asset_prefix(1)),
        content=about_content,
        page_script="",
    )
    write_page(DIST / "about" / "index.html", about_html)

    # Category index
    category_cards = []
    for section, items in sorted(categories.items()):
        slug = slugify(section)
        count = len(items)
        info = category_info.get(section, {})
        heading = info.get("heading", section.title().replace("_", " "))
        desc = info.get("short_description", "")
        category_cards.append(
            f"<a class=\"card\" href=\"./{slug}/\">\n"
            f"  <h3 class=\"card-title\">{html.escape(heading)}</h3>\n"
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
        header_right=header_nav_markup(asset_prefix(1)),
        content=category_index_content,
        page_script="",
    )
    write_page(DIST / "category" / "index.html", category_index_html)

    # Category pages
    category_keys = sorted(categories.keys())
    for section in category_keys:
        items = categories[section]
        slug = slugify(section)
        info = category_info.get(section, {})
        heading = info.get("heading", section.title().replace("_", " "))
        short_desc = info.get("short_description", "")
        intro_html = load_category_intro_html(section)
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
      <h1 class=\"section-title\">{html.escape(heading)}</h1>
    </div>
    <div class=\"tribute-nav\">
      <a class=\"button\" href=\"../\">Back to categories</a>
    </div>
  </div>
  <div class=\"tribute-list\" data-shuffle=\"true\">
    <div class=\"category-intro\" data-shuffle-fixed=\"true\">{intro_html}</div>
    {cards_markup}
  </div>
</section>
"""

        page_html = render_page(
            template,
            title=f"{heading} tributes",
            canonical=f"{base_url}/category/{slug}/" if base_url else "",
            description=short_desc or f"Tributes in the {heading} category.",
            asset_prefix=asset_prefix(2),
            page_class="category-page",
            site_title=html.escape(header_title) + draft_badge,
            header_right=header_nav_markup(asset_prefix(2)),
            content=content,
            page_script="",
        )
        write_page(DIST / "category" / slug / "index.html", page_html)

    # Author index
    author_cards = []
    for slug, items in sorted(authors.items(), key=lambda x: x[1][0]["author_sort"]):
        display = items[0]["author_display"]
        count = len(items)
        meta = f"<div class=\"card-meta\">{count} tribute{'s' if count != 1 else ''}</div>" if count > 1 else ""
        author_cards.append(
            f"<a class=\"card\" href=\"./{slug}/\">\n"
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
        header_right=header_nav_markup(asset_prefix(1)),
        content=author_index_content,
        page_script="",
    )
    write_page(DIST / "author" / "index.html", author_index_html)

    # Author pages
    author_slugs = [slug for slug, _ in sorted(authors.items(), key=lambda x: x[1][0]["author_sort"])]
    for idx, slug in enumerate(author_slugs):
        items = authors[slug]
        display = items[0]["author_display"]
        prev_slug = author_slugs[idx - 1] if idx > 0 else author_slugs[-1]
        next_slug = author_slugs[idx + 1] if idx + 1 < len(author_slugs) else author_slugs[0]
        panels = []
        for tribute in items:
            tribute_html = format_paragraphs(tribute["tribute"])
            how = html.escape(tribute["how"]) if tribute["how"] else ""
            full_name = tribute["name"] or display
            meta = f"<strong>{html.escape(full_name)}</strong>" + (f" — {how}" if how else "")
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
      <a class=\"button\" href=\"../\">Back to authors</a>
      <button class=\"button\" data-tribute-prev>Previous</button>
      <button class=\"button primary\" data-tribute-next>Next</button>
    </div>
  </div>
  <div class=\"tribute-shell\" data-prev-page=\"../{prev_slug}/\" data-next-page=\"../{next_slug}/\">
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
            header_right=header_nav_markup(asset_prefix(2)),
            content=content,
            page_script="",
        )
        write_page(DIST / "author" / slug / "index.html", page_html)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update-tributes-csv",
        dest="update_tributes_csv",
        action="store_true",
        default=True,
        help="Refresh tributes.csv from the Google Sheet before building (default: enabled).",
    )
    parser.add_argument(
        "--no-update-tributes-csv",
        dest="update_tributes_csv",
        action="store_false",
        help="Skip refreshing tributes.csv from the Google Sheet and build from the local file as-is.",
    )
    parser.add_argument(
        "--download-category-intros",
        action="store_true",
        help="Refresh all category intro markdown files before building.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        build(
            download_category_intros=args.download_category_intros,
            update_tributes_csv=args.update_tributes_csv,
        )
    except URLError as exc:
        raise SystemExit(
            "Failed to download remote build data. "
            f"Use `python3 tools/build.py --no-update-tributes-csv` to build from the local CSV instead. ({exc})"
        ) from exc
    except ValueError as exc:
        raise SystemExit(f"Failed to refresh tributes CSV: {exc}") from exc
