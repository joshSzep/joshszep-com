from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path

import markdown


ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
ASSETS_DIR = ROOT / "assets"
BOOKS_DIR = ROOT / "books"
METADATA_PATH = ROOT / "metadata.json"
PROFILE_README_PATH = ROOT / "joshszep" / "README.md"


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
            description=item.get("description", ""),
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
        introduction=raw["introduction"],
        books=books,
        links=links,
    )


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


def render_profile_html(markdown_text: str) -> str:
    html = render_markdown_html(sanitize_profile_markdown(markdown_text))
    html = re.sub(r"<hr\s*/?>", "", html)
    return html


def load_manifesto_html() -> str:
    manifesto_markdown = (ROOT / "MANIFESTO.md").read_text(encoding="utf-8")
    return render_markdown_html(manifesto_markdown)


def copy_required_assets(books: list[Book]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    required_files = {
        ASSETS_DIR / "hero-dark.png",
        ASSETS_DIR / "hero-light.png",
        ASSETS_DIR / "icon.png",
        ASSETS_DIR / "photo.jpeg",
    }
    required_files.update(BOOKS_DIR / book.cover_name for book in books)

    for asset_path in required_files:
        if not asset_path.exists():
            raise FileNotFoundError(f"Required asset is missing: {asset_path}")
        shutil.copy2(asset_path, OUTPUT_DIR / asset_path.name)


def build_book_cards(books: list[Book]) -> str:
    cards: list[str] = []
    for book in books:
        status = "Published" if book.published else "Upcoming"
        description = book.description.strip() or (
            "Available now on its launch page." if book.published else "A forthcoming work."
        )
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
                    <div class=\"book-meta-top\">
                        <p class=\"eyebrow\">{escape(status)}</p>
                    </div>
                    <h3>{escape(book.title)}</h3>
                    <p class=\"book-description\">{escape(description)}</p>
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
        <section id="manifesto" style="width:100%;padding:4.5rem 0;">
            <div class="manifesto-shell" style="max-width:900px;margin:0 auto;">
                <div class="section-heading reveal">
                    <div>
                        <p class="eyebrow">Manifesto</p>
                    </div>
                </div>
                <div class="manifesto-content" style="font-size:1.18rem;line-height:1.7;color:var(--muted);background:var(--panel);border-radius:1.5rem;padding:2.2rem 2.5rem 2.1rem 2.5rem;border:1px solid var(--line);box-shadow:var(--shadow);">
                    {manifesto_html}
                </div>
            </div>
        </section>
    '''


def build_header() -> str:
    return """
        <header class=\"topbar\">
            <a class=\"wordmark\" href=\"#top\">
                <img src=\"icon.png\" alt=\"Site icon\">
                <span>Joshua Szepietowski</span>
            </a>
            <button class=\"theme-toggle\" type=\"button\" aria-label=\"Toggle color theme\">Theme</button>
        </header>
    """.strip()


def build_hero_section(introduction: str) -> str:
    return f"""
        <section class=\"hero\">
            <div class=\"hero-visual reveal\"></div>
            <div class=\"hero-copy reveal\">
                <p>{escape(introduction)}</p>
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


def build_site_styles() -> str:
    return """
        :root {
            color-scheme: dark light;
            --bg: #000000;
            --fg: #f5f1e8;
            --muted: rgba(245, 241, 232, 0.7);
            --line: rgba(245, 241, 232, 0.12);
            --panel: rgba(245, 241, 232, 0.04);
            --panel-strong: rgba(245, 241, 232, 0.08);
            --shadow: 0 24px 80px rgba(0, 0, 0, 0.38);
            --accent: #d4b483;
            --accent-soft: rgba(212, 180, 131, 0.16);
            --hero-image: url('hero-dark.png');
        }

        :root[data-theme=\"light\"] {
            --bg: #ffffff;
            --fg: #141414;
            --muted: rgba(20, 20, 20, 0.64);
            --line: rgba(20, 20, 20, 0.1);
            --panel: rgba(20, 20, 20, 0.03);
            --panel-strong: rgba(20, 20, 20, 0.06);
            --shadow: 0 24px 80px rgba(20, 20, 20, 0.08);
            --accent: #7a4b22;
            --accent-soft: rgba(122, 75, 34, 0.1);
            --hero-image: url('hero-light.png');
        }

        * { box-sizing: border-box; }

        html { scroll-behavior: smooth; }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: \"Avenir Next\", Avenir, \"Segoe UI\", sans-serif;
            background: var(--bg);
            color: var(--fg);
            line-height: 1.6;
            transition: background-color 180ms ease, color 180ms ease;
        }

        a {
            color: inherit;
            text-decoration: none;
        }

        img {
            display: block;
            max-width: 100%;
        }

        .page-shell {
            position: relative;
            overflow: hidden;
        }

        .page-shell::before {
            content: \"\";
            position: fixed;
            inset: -12rem auto auto -12rem;
            width: 28rem;
            height: 28rem;
            border-radius: 999px;
            background: radial-gradient(circle, var(--accent-soft), transparent 68%);
            pointer-events: none;
            filter: blur(10px);
        }

        .page-shell::after {
            content: \"\";
            position: fixed;
            inset: auto -10rem 10rem auto;
            width: 26rem;
            height: 26rem;
            border-radius: 999px;
            background: radial-gradient(circle, var(--panel-strong), transparent 70%);
            pointer-events: none;
            filter: blur(10px);
        }

        .container {
            width: min(1120px, calc(100vw - 2rem));
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }

        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 0 0;
        }

        .wordmark {
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.82rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--muted);
        }

        .wordmark img {
            width: 1.6rem;
            height: 1.6rem;
            border-radius: 0.45rem;
        }

        .theme-toggle {
            border: 1px solid var(--line);
            background: var(--panel);
            color: var(--fg);
            border-radius: 999px;
            padding: 0.65rem 0.9rem;
            font: inherit;
            cursor: pointer;
            transition: transform 140ms ease, background-color 140ms ease, border-color 140ms ease;
        }

        .theme-toggle:hover {
            transform: translateY(-1px);
            background: var(--panel-strong);
        }

        section {
            padding: 4.5rem 0;
        }

        .hero {
            padding-top: 2rem;
        }

        .eyebrow {
            margin: 0 0 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.75rem;
            color: var(--muted);
        }

        h1, h2, h3 {
            margin: 0;
            font-family: \"Iowan Old Style\", \"Palatino Linotype\", \"Book Antiqua\", Georgia, serif;
            font-weight: 600;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: clamp(3.3rem, 8vw, 6.8rem);
            line-height: 0.96;
            max-width: 11ch;
        }

        .hero-copy {
            margin-top: 1.5rem;
            text-align: center;
        }

        .hero-copy > p {
            margin: 0;
            font-size: clamp(1.15rem, 2vw, 1.4rem);
            color: var(--muted);
        }

        .hero-visual {
            position: relative;
            min-height: clamp(20rem, 52vw, 42rem);
            border-radius: 2rem;
            background: linear-gradient(145deg, var(--panel), transparent 70%);
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
            overflow: hidden;
            isolation: isolate;
        }

        .hero-visual::before {
            content: \"\";
            position: absolute;
            inset: 0;
            background-image: var(--hero-image);
            background-size: cover;
            background-position: center;
            opacity: 0.92;
            transition: opacity 180ms ease;
        }

        .hero-visual::after {
            content: \"\";
            position: absolute;
            inset: auto 0 0;
            height: 20%;
            background: linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.06) 100%);
            mix-blend-mode: multiply;
        }

        .section-heading {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 1.5rem;
            align-items: end;
            margin-bottom: 2rem;
        }

        .section-heading p {
            margin: 0.8rem 0 0;
            max-width: 40rem;
            color: var(--muted);
        }

        .book-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.2rem;
        }

        .book-card {
            display: grid;
            grid-template-columns: 124px minmax(0, 1fr);
            gap: 1rem;
            padding: 1rem;
            border-radius: 1.5rem;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, var(--panel), transparent 140%);
            box-shadow: var(--shadow);
        }

        .cover-shell {
            border-radius: 1rem;
            overflow: hidden;
            background: var(--panel-strong);
        }

        .cover-shell img {
            width: 100%;
            aspect-ratio: 2 / 3;
            object-fit: cover;
        }

        .book-meta {
            display: flex;
            flex-direction: column;
        }

        .book-meta-top {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: start;
        }

        .section-kicker {
            margin: 0;
            color: var(--muted);
            font-size: 0.92rem;
        }

        .book-card h3 {
            margin-top: 0.25rem;
            font-size: 1.45rem;
        }

        .book-description {
            margin: 0.65rem 0 1rem;
            color: var(--muted);
            flex: 1;
        }

        .book-link {
            align-self: start;
            padding: 0.7rem 0.9rem;
            border-radius: 999px;
            background: var(--accent-soft);
            color: var(--fg);
            border: 1px solid transparent;
        }

        .book-link.muted {
            background: var(--panel);
            border-color: var(--line);
            color: var(--muted);
        }

        .profile-panel {
            display: grid;
            grid-template-columns: minmax(240px, 300px) minmax(0, 1fr);
            gap: 2rem;
            padding: 1.5rem;
            border-radius: 2rem;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, var(--panel), transparent 150%);
            box-shadow: var(--shadow);
        }

        .profile-aside {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .portrait-frame {
            border-radius: 1.5rem;
            overflow: hidden;
            border: 1px solid var(--line);
            background: var(--panel-strong);
        }

        .portrait-frame img {
            width: 100%;
            aspect-ratio: 4 / 5;
            object-fit: cover;
        }

        .profile-note {
            padding: 1rem 1.1rem;
            border-radius: 1.25rem;
            background: var(--panel);
            border: 1px solid var(--line);
            color: var(--muted);
        }

        .profile-content {
            min-width: 0;
        }

        .profile-content h1,
        .profile-content h2,
        .profile-content h3,
        .profile-content h4 {
            font-size: clamp(1.15rem, 2vw, 1.8rem);
            margin: 2rem 0 0.8rem;
            line-height: 1.2;
        }

        .profile-content h1:first-child,
        .profile-content h2:first-child,
        .profile-content h3:first-child {
            margin-top: 0;
        }

        .profile-content p {
            margin: 0 0 1rem;
        }

        .profile-content ul {
            margin: 0 0 1.15rem;
            padding-left: 1.2rem;
        }

        .profile-content li {
            margin-bottom: 0.45rem;
        }

        .profile-content strong {
            color: var(--fg);
        }

        .profile-content a {
            color: var(--accent);
        }

        .link-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }

        .link-card {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            padding: 1.2rem;
            border-radius: 1.35rem;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, var(--panel), transparent 140%);
            min-height: 8.5rem;
        }

        .link-card-title {
            font-family: \"Iowan Old Style\", \"Palatino Linotype\", \"Book Antiqua\", Georgia, serif;
            font-size: 1.35rem;
        }

        .link-card-description {
            color: var(--muted);
        }

        .footer {
            padding: 1rem 0 3rem;
            color: var(--muted);
            font-size: 0.9rem;
        }

        .reveal {
            opacity: 0;
            transform: translateY(16px);
            transition: opacity 500ms ease, transform 500ms ease;
        }

        .reveal.is-visible {
            opacity: 1;
            transform: translateY(0);
        }

        @media (max-width: 960px) {
            .profile-panel {
                grid-template-columns: 1fr;
            }

            .book-grid {
                grid-template-columns: 1fr;
            }

            .hero {
                min-height: auto;
                padding-top: 2rem;
            }
        }

        @media (max-width: 720px) {
            section {
                padding: 3.5rem 0;
            }

            .topbar {
                padding-top: 0.75rem;
            }

            .section-heading {
                grid-template-columns: 1fr;
            }

            .book-card {
                grid-template-columns: 1fr;
            }

            .hero-visual {
                min-height: 22rem;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            html { scroll-behavior: auto; }

            *, *::before, *::after {
                transition: none !important;
                animation: none !important;
            }

            .reveal {
                opacity: 1;
                transform: none;
            }
        }
    """.strip()


def build_site_script() -> str:
    return """
        const storageKey = \"joshszep-theme\";
        const root = document.documentElement;
        const themeToggle = document.querySelector(\".theme-toggle\");
        const prefersLight = window.matchMedia(\"(prefers-color-scheme: light)\");

        function setTheme(theme) {
            root.dataset.theme = theme;
            themeToggle.textContent = theme === \"light\" ? \"Light\" : \"Dark\";
            themeToggle.setAttribute(\"aria-pressed\", String(theme === \"light\"));
        }

        const storedTheme = localStorage.getItem(storageKey);
        setTheme(storedTheme || (prefersLight.matches ? \"light\" : \"dark\"));

        themeToggle.addEventListener(\"click\", () => {
            const nextTheme = root.dataset.theme === \"light\" ? \"dark\" : \"light\";
            setTheme(nextTheme);
            localStorage.setItem(storageKey, nextTheme);
        });

        prefersLight.addEventListener(\"change\", event => {
            if (!localStorage.getItem(storageKey)) {
                setTheme(event.matches ? \"light\" : \"dark\");
            }
        });

        const observer = new IntersectionObserver(entries => {
            for (const entry of entries) {
                if (entry.isIntersecting) {
                    entry.target.classList.add(\"is-visible\");
                    observer.unobserve(entry.target);
                }
            }
        }, { threshold: 0.16 });

        document.querySelectorAll(\".reveal\").forEach((element, index) => {
            element.style.transitionDelay = `${index * 70}ms`;
            observer.observe(element);
        });
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
    styles = build_site_styles()
    script = build_site_script()
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Joshua Szepietowski</title>
    <meta name=\"description\" content=\"{escape(metadata.introduction)}\">
    <link rel=\"icon\" href=\"icon.png\">
    <style>
        {styles}
    </style>
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
    <script>
        {script}
    </script>
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
