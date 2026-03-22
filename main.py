import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from html import escape, unescape
from pathlib import Path

import markdown


ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
ASSETS_DIR = ROOT / "assets"
BOOKS_DIR = ROOT / "books"
METADATA_PATH = ROOT / "metadata.json"
INTRODUCTION_PATH = ROOT / "INTRODUCTION.md"
PROFILE_README_PATH = ROOT / "joshszep" / "README.md"
SITE_CSS_PATH = ASSETS_DIR / "site.css"
SITE_JS_PATH = ASSETS_DIR / "site.js"
REQUIRED_ASSET_PATHS = {
    ASSETS_DIR / "hero-dark.png",
    ASSETS_DIR / "hero-gif-dark.gif",
    ASSETS_DIR / "hero-gif-light.gif",
    ASSETS_DIR / "hero-light.png",
    ASSETS_DIR / "icon.png",
    ASSETS_DIR / "photo.jpeg",
    SITE_CSS_PATH,
    SITE_JS_PATH,
}


@dataclass(slots=True)
class Book:
    id: str
    title: str
    description: str
    published_date: datetime
    published: bool

    @property
    def cover_name(self) -> str:
        return f"{self.id}.png"

    @property
    def description_name(self) -> str:
        return f"{self.id}.md"

    @property
    def launch_url(self) -> str:
        return f"https://{self.id}.joshszep.com"


@dataclass(slots=True)
class Link:
    id: str
    title: str
    url: str
    description: str


@dataclass(slots=True)
class SiteMetadata:
    introduction: str
    books: list[Book]
    links: list[Link]


def load_metadata() -> SiteMetadata:
    raw = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    books = [
        Book(
            id=item["id"],
            title=item["title"],
            description=load_book_description(item["id"]),
            published_date=datetime.strptime(item["published_date"], "%Y-%m-%d"),
            published=bool(item.get("published", False)),
        )
        for item in raw.get("books", [])
    ]
    links = [
        Link(
            id=item["id"],
            title=item["title"],
            url=item["url"],
            description=item.get("description", ""),
        )
        for item in raw.get("links", [])
    ]
    books.sort(key=lambda book: book.published_date, reverse=True)
    return SiteMetadata(
        introduction=load_introduction_markdown(),
        books=books,
        links=links,
    )


def load_introduction_markdown() -> str:
    return INTRODUCTION_PATH.read_text(encoding="utf-8").strip()


def load_book_description(book_id: str) -> str:
    description_path = BOOKS_DIR / f"{book_id}.md"
    return description_path.read_text(encoding="utf-8").strip()


def sanitize_profile_markdown(markdown_text: str) -> str:
    blocked_prefixes = (
        "📞",
        "📧",
        "🔗 [LinkedIn]",
    )
    filtered_lines = [
        line for line in markdown_text.splitlines() if not line.strip().startswith(blocked_prefixes)
    ]
    return "\n".join(filtered_lines)


def render_markdown_html(markdown_text: str) -> str:
    return markdown.markdown(markdown_text, extensions=["extra", "sane_lists"])


def markdown_to_plain_text(markdown_text: str) -> str:
    html = render_markdown_html(markdown_text)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def render_profile_html(markdown_text: str) -> str:
    html = render_markdown_html(sanitize_profile_markdown(markdown_text))
    html = re.sub(r"<hr\s*/?>", "", html)
    return html


def load_manifesto_html() -> str:
    manifesto_markdown = (ROOT / "MANIFESTO.md").read_text(encoding="utf-8")
    return render_markdown_html(manifesto_markdown)


def copy_required_assets(books: list[Book]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    required_files = set(REQUIRED_ASSET_PATHS)
    required_files.update(BOOKS_DIR / book.cover_name for book in books)

    for asset_path in required_files:
        if not asset_path.exists():
            raise FileNotFoundError(f"Required asset is missing: {asset_path}")
        shutil.copy2(asset_path, OUTPUT_DIR / asset_path.name)


def build_book_cards(books: list[Book]) -> str:
    cards: list[str] = []
    for book in books:
        description = book.description.strip() or (
            "Available now on its launch page." if book.published else "A forthcoming work."
        )
        description_html = render_markdown_html(description)
        cta = (
            f'<a class="book-link" href="{escape(book.launch_url)}">Visit launch page</a>'
            if book.published
            else '<span class="book-link muted">Coming soon</span>'
        )
        cards.append(
            f"""
            <article class=\"book-card\">
                <div class=\"cover-shell\">
                    <img src=\"{escape(book.cover_name)}\" alt=\"Cover for {escape(book.title)}\" loading=\"lazy\">
                </div>
                <div class=\"book-meta\">
                    <h3>{escape(book.title)}</h3>
                    <div class=\"book-description\">{description_html}</div>
                    {cta}
                </div>
            </article>
            """.strip()
        )
    return "\n".join(cards)


def build_link_cards(links: list[Link]) -> str:
    return "\n".join(
        f"""
        <a class=\"link-card\" href=\"{escape(link.url)}\">
            <span class=\"link-card-title\">{escape(link.title)}</span>
            <span class=\"link-card-description\">{escape(link.description)}</span>
        </a>
        """.strip()
        for link in links
    )


def build_manifesto_section(manifesto_html: str) -> str:
    return f'''
        <section id="manifesto" class="manifesto-section">
            <div class="manifesto-shell">
                <div class="section-heading reveal">
                    <div>
                        <p class="eyebrow">Manifesto</p>
                    </div>
                </div>
                <div class="manifesto-content">
                    {manifesto_html}
                </div>
            </div>
        </section>
    '''


def build_header() -> str:
    return """
        <header class=\"topbar\">
            <div class=\"topbar-inner\">
                <a class=\"wordmark\" href=\"#top\">
                    <img src=\"icon.png\" alt=\"Site icon\">
                    <span>Joshua Szepietowski</span>
                </a>
                <nav class=\"section-nav\" aria-label=\"Primary\">
                    <a class=\"section-nav-link\" href=\"#manifesto\">Manifesto</a>
                    <a class=\"section-nav-link\" href=\"#books\">Books</a>
                    <a class=\"section-nav-link\" href=\"#profile\">Profile</a>
                    <a class=\"section-nav-link\" href=\"#links\">Links</a>
                </nav>
                <button class=\"theme-toggle\" type=\"button\" aria-label=\"Toggle color theme\">Theme</button>
            </div>
        </header>
    """.strip()


def build_hero_section(introduction: str) -> str:
    introduction_html = render_markdown_html(introduction)
    return f"""
        <section class=\"hero\">
            <button class=\"hero-visual reveal\" type=\"button\" aria-pressed=\"false\" aria-label=\"Toggle animated hero image\"></button>
            <div class=\"hero-copy reveal\">
                {introduction_html}
            </div>
        </section>
    """.strip()


def build_books_section(books: list[Book]) -> str:
    return f"""
        <section id=\"books\">
            <div class=\"section-heading reveal\">
                <div>
                    <p class=\"eyebrow\">Books</p>
                </div>
            </div>
            <div class=\"book-grid\">
                {build_book_cards(books)}
            </div>
        </section>
    """.strip()


def build_profile_section(profile_html: str) -> str:
    return f"""
        <section id=\"profile\">
            <div class=\"section-heading reveal\">
                <div>
                    <p class=\"eyebrow\">Profile</p>
                    <h2>Software engineering background and resume.</h2>
                </div>
            </div>
            <div class=\"profile-panel reveal\">
                <aside class=\"profile-aside\">
                    <div class=\"portrait-frame\">
                        <img src=\"photo.jpeg\" alt=\"Portrait of Joshua Szepietowski\" loading=\"lazy\">
                    </div>
                    <div class=\"profile-note\">
                        Two decades building backend systems, teams, and delivery workflows, alongside an ongoing body of fiction.
                    </div>
                </aside>
                <article class=\"profile-content\">{profile_html}</article>
            </div>
        </section>
    """.strip()


def build_links_section(links: list[Link]) -> str:
    return f"""
        <section id=\"links\">
            <div class=\"section-heading reveal\">
                <div>
                    <p class=\"eyebrow\">Links</p>
                    <h2>Continue elsewhere.</h2>
                    <p>A short list of places where the rest of the work lives.</p>
                </div>
            </div>
            <div class=\"link-grid\">
                {build_link_cards(links)}
            </div>
        </section>
    """.strip()


def build_page_sections(metadata: SiteMetadata, profile_html: str) -> str:
    sections = [
        build_hero_section(metadata.introduction),
        build_manifesto_section(load_manifesto_html()),
        build_books_section(metadata.books),
        build_profile_section(profile_html),
        build_links_section(metadata.links),
    ]
    return "\n\n                ".join(sections)


def build_html(metadata: SiteMetadata, profile_html: str) -> str:
    page_sections = build_page_sections(metadata, profile_html)
    meta_description = markdown_to_plain_text(metadata.introduction)
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Joshua Szepietowski</title>
    <meta name=\"description\" content=\"{escape(meta_description)}\">
    <link rel=\"icon\" href=\"icon.png\">
    <link rel=\"stylesheet\" href=\"site.css\">
</head>
<body>
    <div class=\"page-shell\">
        <div class=\"container\">
            {build_header()}

            <main id=\"top\">
                {page_sections}
            </main>

            <footer class=\"footer\"></footer>
        </div>
    </div>
    <script src=\"site.js\"></script>
</body>
</html>
"""


def write_site(html: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "index.html"
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main() -> None:
    metadata = load_metadata()
    profile_markdown = PROFILE_README_PATH.read_text(encoding="utf-8")
    profile_html = render_profile_html(profile_markdown)
    copy_required_assets(metadata.books)
    output_path = write_site(build_html(metadata, profile_html))
    print(f"Built site at {output_path}")


if __name__ == "__main__":
    main()
