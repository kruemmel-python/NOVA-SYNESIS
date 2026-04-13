from __future__ import annotations

import html
import json
import mimetypes
import posixpath
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import markdown
except ImportError as exc:  # pragma: no cover - operator guidance
    raise SystemExit(
        "The web docs builder requires the 'markdown' package. "
        "Install it with 'pip install -e .[dev]' or 'pip install markdown'."
    ) from exc

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "dokumentation"
WEB = ROOT / "docs"
ASSETS = WEB / "assets"
REPO_VIEW = WEB / "repo"
REPO_ASSETS = WEB / "repo-assets"

SKIP_DOC_FILES = {"docs.md"}
WEB_GUIDE_ORDER = [
    "getting-started.md",
    "system-overview.md",
    "backend-runtime.md",
    "frontend-editor.md",
    "planner-and-lit.md",
    "security-and-policy.md",
    "handler-trust-and-approval.md",
    "failure-playbook.md",
    "real-world-scenarios.md",
]
WEB_ALLOWED_GUIDES = {Path(name) for name in WEB_GUIDE_ORDER}
WEB_BANNED_REPO_FILENAMES = {
    "README.md",
    "Whitepaper.md",
    "Fachartikel_NOVA-SYNESIS.md",
    "fazit.md",
    "Schnellstart.md",
    "LICENSE",
    "uml_V3.mmd",
    "uml.html",
}
WEB_ALLOWED_ROOT_REPO_FILES = {
    ".env.example",
    "Dockerfile",
    "pyproject.toml",
    "run-backend.ps1",
    "run-backend.cmd",
}
WEB_ALLOWED_FRONTEND_FILES = {
    "index.html",
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "tsconfig.app.json",
    "tsconfig.node.json",
    "vite.config.ts",
    "vite.config.js",
    "vite.config.d.ts",
    ".env.example",
}
ASSET_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".avif",
    ".ico",
    ".bmp",
}
TEXT_EXTENSIONS = {
    ".py",
    ".pyi",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".css",
    ".scss",
    ".html",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".ps1",
    ".cmd",
    ".mmd",
    ".txt",
    ".env",
    ".example",
    ".lock",
    ".gitignore",
    ".d.ts",
}
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:")
SPECIAL_BRANCH_LABELS = {
    "api": "API",
    "frontend": "Frontend",
    "lit": "LIT",
    "nova_synesis": "NOVA-SYNESIS",
    "reference": "Reference",
    "src": "Source",
    "use_cases": "Use Cases",
}
ACRONYM_SEGMENTS = {
    "api",
    "cli",
    "css",
    "html",
    "http",
    "json",
    "lit",
    "llm",
    "toml",
    "ts",
    "tsx",
    "ui",
    "uml",
    "url",
    "ws",
    "xml",
    "yaml",
    "yml",
}


@dataclass(slots=True)
class Page:
    source_path: Path
    docs_relative_path: Path
    output_relative_path: Path
    output_path: Path
    url: str
    title: str
    description: str
    group: str
    html_content: str = ""
    plain_text: str = ""
    headings: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class RepoSourcePage:
    target_path: Path
    output_relative_path: Path
    output_path: Path
    url: str
    title: str
    kind: str


def reference_docs_relative_to_repo_relative(docs_relative: Path) -> Path | None:
    if not docs_relative.parts or docs_relative.parts[0] != "reference":
        return None
    if docs_relative == Path("reference/index.md"):
        return None
    inner = Path(*docs_relative.parts[1:])
    inner_text = inner.as_posix()
    if not inner_text.endswith(".md"):
        return None
    return Path(inner_text[:-3])


def is_allowed_repo_relative(relative: Path) -> bool:
    relative_text = relative.as_posix()
    if relative.name in WEB_BANNED_REPO_FILENAMES:
        return False
    if any(part in {"dokumentation", "docs", "data", "release", "billing", ".git", "__pycache__"} for part in relative.parts):
        return False
    if relative.parts and relative.parts[0] == "Use_Cases":
        return relative.name != "README.md"
    if relative.parts and relative.parts[0] == "src":
        return True
    if relative.parts[:2] == ("frontend", "src"):
        return True
    if relative.parts and relative.parts[0] in {"tests", "tools"}:
        return True
    if relative.parts and relative.parts[0] == "frontend":
        return relative.name in WEB_ALLOWED_FRONTEND_FILES
    return relative_text in WEB_ALLOWED_ROOT_REPO_FILES


def is_allowed_repo_target(target: Path) -> bool:
    try:
        relative = target.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return False
    return is_allowed_repo_relative(relative)


def should_include_doc_page(docs_relative: Path) -> bool:
    if docs_relative.name in SKIP_DOC_FILES:
        return False
    if docs_relative == Path("README.md"):
        return True
    if not docs_relative.parts:
        return False
    if docs_relative.parts[0] != "reference":
        return docs_relative in WEB_ALLOWED_GUIDES
    if docs_relative == Path("reference/index.md"):
        return True
    repo_relative = reference_docs_relative_to_repo_relative(docs_relative)
    return repo_relative is not None and is_allowed_repo_relative(repo_relative)


def slugify(value: str) -> str:
    normalized = re.sub(r"<[^>]+>", "", value)
    normalized = html.unescape(normalized)
    normalized = normalized.strip().casefold()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or "section"


def strip_markdown(text: str) -> str:
    cleaned = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"(?<!\w)\*\*([^*]+)\*\*(?!\w)", r"\1", cleaned)
    cleaned = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"\1", cleaned)
    cleaned = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def first_paragraph(markdown_text: str) -> str:
    paragraphs = [chunk.strip() for chunk in re.split(r"\n\s*\n", markdown_text) if chunk.strip()]
    for paragraph in paragraphs:
        if paragraph.startswith("#"):
            continue
        if paragraph.startswith("```"):
            continue
        return strip_markdown(paragraph)
    return ""


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def markdown_output_path(docs_relative: Path) -> Path:
    if docs_relative == Path("README.md"):
        return Path("index.html")
    return docs_relative.with_suffix(".html")


def relative_href(current_output: Path, target_url: str) -> str:
    rel = posixpath.relpath(target_url, start=current_output.parent.as_posix())
    return rel if rel != "." else "index.html"


def resolve_local_target(current_source: Path, raw_target: str) -> Path | None:
    target = raw_target.replace("\\", "/")
    if re.match(r"^/?[A-Za-z]:/", target):
        normalized = target.lstrip("/")
        return Path(normalized)
    if target.startswith("/"):
        absolute = Path(target)
        if absolute.exists():
            return absolute
        repo_candidate = ROOT / target.lstrip("/")
        if repo_candidate.exists():
            return repo_candidate.resolve()
        return None
    return (current_source.parent / target).resolve()


def is_binary_asset(path: Path) -> bool:
    suffix = path.suffix.casefold()
    name = path.name.casefold()
    if suffix in ASSET_EXTENSIONS:
        return True
    if suffix in {".exe", ".zip", ".db", ".pdf", ".litertlm"}:
        return True
    return name.endswith(".xnnpack_cache") or ".xnnpack_cache." in name


def page_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            return strip_markdown(line[2:].strip()) or fallback
    return fallback


def toc_to_flat_tokens(tokens: list[dict[str, Any]]) -> list[dict[str, str]]:
    flattened: list[dict[str, str]] = []
    for token in tokens:
        flattened.append(
            {
                "id": str(token.get("id", "")),
                "name": str(token.get("name", "")),
                "level": str(token.get("level", "2")),
            }
        )
        children = token.get("children", [])
        if isinstance(children, list):
            flattened.extend(toc_to_flat_tokens(children))
    return flattened


def parse_ordered_links(markdown_text: str) -> list[str]:
    links: list[str] = []
    for _, href in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", markdown_text):
        if href.startswith(EXTERNAL_PREFIXES):
            continue
        if href.endswith(".md") and href not in links:
            links.append(href)
    return links


def escape_script_json(payload: Any) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return serialized.replace("</", "<\\/")


def inject_heading_anchors(content: str) -> str:
    heading_pattern = re.compile(r"<h([1-6]) id=\"([^\"]+)\">(.*?)</h\1>")

    def replace(match: re.Match[str]) -> str:
        level = match.group(1)
        heading_id = match.group(2)
        inner = match.group(3)
        return (
            f"<h{level} id=\"{heading_id}\">"
            f"<a class=\"heading-anchor\" href=\"#{heading_id}\">{inner}</a>"
            f"</h{level}>"
        )

    return heading_pattern.sub(replace, content)


def build_markdown_page(
    page: Page,
    page_map: dict[Path, Page],
    repo_file_pages: dict[Path, RepoSourcePage],
    repo_dir_pages: dict[Path, RepoSourcePage],
    doc_assets: set[Path],
    repo_assets: set[Path],
) -> None:
    if page.docs_relative_path == Path("README.md"):
        markdown_text = build_site_home_markdown(page_map)
    elif page.docs_relative_path == Path("reference/index.md"):
        markdown_text = build_filtered_reference_index_markdown(page_map)
    else:
        markdown_text = read_text(page.source_path)
    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "sane_lists", "toc", "attr_list"],
        extension_configs={"toc": {"permalink": False}},
    )
    converted = md.convert(markdown_text)
    rewritten = rewrite_html_links(
        html_fragment=converted,
        current_page=page,
        page_map=page_map,
        repo_file_pages=repo_file_pages,
        repo_dir_pages=repo_dir_pages,
        doc_assets=doc_assets,
        repo_assets=repo_assets,
    )
    page.html_content = inject_heading_anchors(rewritten)
    page.plain_text = strip_markdown(markdown_text)
    page.headings = toc_to_flat_tokens(getattr(md, "toc_tokens", []))


def rewrite_html_links(
    html_fragment: str,
    current_page: Page,
    page_map: dict[Path, Page],
    repo_file_pages: dict[Path, RepoSourcePage],
    repo_dir_pages: dict[Path, RepoSourcePage],
    doc_assets: set[Path],
    repo_assets: set[Path],
) -> str:
    attribute_pattern = re.compile(r"(?P<attr>href|src)=\"(?P<value>[^\"]+)\"")

    def replace(match: re.Match[str]) -> str:
        attribute = match.group("attr")
        value = match.group("value")
        rewritten = rewrite_link_value(
            raw_value=value,
            current_page=current_page,
            attribute=attribute,
            page_map=page_map,
            repo_file_pages=repo_file_pages,
            repo_dir_pages=repo_dir_pages,
            doc_assets=doc_assets,
            repo_assets=repo_assets,
        )
        return f'{attribute}="{html.escape(rewritten, quote=True)}"'

    return attribute_pattern.sub(replace, html_fragment)


def rewrite_link_value(
    raw_value: str,
    current_page: Page,
    attribute: str,
    page_map: dict[Path, Page],
    repo_file_pages: dict[Path, RepoSourcePage],
    repo_dir_pages: dict[Path, RepoSourcePage],
    doc_assets: set[Path],
    repo_assets: set[Path],
) -> str:
    if raw_value.startswith(EXTERNAL_PREFIXES) or raw_value.startswith("#"):
        return raw_value

    anchor = ""
    if "#" in raw_value:
        path_part, anchor_fragment = raw_value.split("#", 1)
        anchor = f"#{slugify(anchor_fragment)}" if anchor_fragment else ""
    else:
        path_part = raw_value

    if not path_part:
        return anchor or "#"

    resolved_target = resolve_local_target(current_page.source_path, path_part)
    if resolved_target is None:
        return raw_value

    if DOCS.resolve() in resolved_target.parents or resolved_target == DOCS.resolve():
        if resolved_target.is_dir():
            candidate = resolved_target / "README.md"
            if candidate in {page.source_path for page in page_map.values()}:
                target_page = page_map[candidate.relative_to(DOCS)]
                return relative_href(current_page.output_relative_path, target_page.url) + anchor
            return "#"

        if resolved_target.suffix.casefold() == ".md":
            docs_relative = resolved_target.relative_to(DOCS)
            target_page = page_map.get(docs_relative)
            if target_page is None:
                return "#"
            return relative_href(current_page.output_relative_path, target_page.url) + anchor

        doc_assets.add(resolved_target)
        asset_url = resolved_target.relative_to(DOCS).as_posix()
        return relative_href(current_page.output_relative_path, asset_url)

    if ROOT.resolve() in resolved_target.parents or resolved_target == ROOT.resolve():
        if not is_allowed_repo_target(resolved_target):
            return "#"
        if resolved_target.is_dir():
            page = repo_dir_pages.setdefault(
                resolved_target,
                RepoSourcePage(
                    target_path=resolved_target,
                    output_relative_path=Path("repo") / resolved_target.relative_to(ROOT) / "index.html",
                    output_path=REPO_VIEW / resolved_target.relative_to(ROOT) / "index.html",
                    url=(Path("repo") / resolved_target.relative_to(ROOT) / "index.html").as_posix(),
                    title=f"Repository: {resolved_target.relative_to(ROOT).as_posix()}",
                    kind="directory",
                ),
            )
            return relative_href(current_page.output_relative_path, page.url)

        if is_binary_asset(resolved_target):
            repo_assets.add(resolved_target)
            asset_url = (Path("repo-assets") / resolved_target.relative_to(ROOT)).as_posix()
            return relative_href(current_page.output_relative_path, asset_url)

        page = repo_file_pages.setdefault(
            resolved_target,
            RepoSourcePage(
                target_path=resolved_target,
                output_relative_path=Path("repo") / resolved_target.relative_to(ROOT).with_suffix(
                    resolved_target.suffix + ".html"
                ),
                output_path=REPO_VIEW / resolved_target.relative_to(ROOT).with_suffix(
                    resolved_target.suffix + ".html"
                ),
                url=(Path("repo") / resolved_target.relative_to(ROOT).with_suffix(
                    resolved_target.suffix + ".html"
                )).as_posix(),
                title=f"Repository: {resolved_target.relative_to(ROOT).as_posix()}",
                kind="file",
            ),
        )
        return relative_href(current_page.output_relative_path, page.url)

    return raw_value


def build_navigation(page_map: dict[Path, Page]) -> list[dict[str, Any]]:
    home_page = page_map[Path("README.md")]
    guide_items = []
    for path_text in WEB_GUIDE_ORDER:
        path = Path(path_text)
        page = page_map.get(path)
        if page is not None:
            guide_items.append({"label": page.title, "url": page.url})
    reference_items = build_reference_tree(page_map)
    return [
        {"label": "Projekt", "items": guide_items or [{"label": home_page.title, "url": home_page.url}]},
        {"label": "Code & Flows", "items": reference_items},
    ]


def build_reference_tree(page_map: dict[Path, Page]) -> list[dict[str, Any]]:
    reference_pages = {
        path: page for path, page in page_map.items() if path.parts and path.parts[0] == "reference"
    }
    items: list[dict[str, Any]] = []
    index_page = reference_pages.get(Path("reference/index.md"))
    if index_page is not None:
        items.append({"label": index_page.title, "url": index_page.url})

    tree: dict[str, Any] = {}
    for path, page in reference_pages.items():
        if path == Path("reference/index.md"):
            continue
        cursor = tree
        parts = list(path.parts[1:])
        for segment in parts[:-1]:
            cursor = cursor.setdefault(segment, {})
        cursor[parts[-1]] = page

    def render_branch(branch: dict[str, Any]) -> list[dict[str, Any]]:
        rendered: list[dict[str, Any]] = []
        for key in sorted(branch.keys(), key=lambda value: value.casefold()):
            value = branch[key]
            if isinstance(value, Page):
                rendered.append({"label": docs_filename_label(value.docs_relative_path), "url": value.url})
                continue
            rendered.append(
                {
                    "label": humanize_segment(key),
                    "children": render_branch(value),
                }
            )
        return rendered

    items.extend(render_branch(tree))
    return items


def humanize_segment(value: str) -> str:
    stripped = value[:-3] if value.endswith(".md") else value
    special = SPECIAL_BRANCH_LABELS.get(stripped.casefold())
    if special is not None:
        return special
    if stripped.isupper():
        return stripped

    words = [word for word in re.split(r"[-_]+", stripped) if word]
    if not words:
        return stripped

    converted: list[str] = []
    for word in words:
        lowered = word.casefold()
        if lowered in ACRONYM_SEGMENTS:
            converted.append(word.upper())
        elif word.isupper():
            converted.append(word)
        elif word.islower():
            converted.append(word.capitalize())
        else:
            converted.append(word)
    return " ".join(converted)


def docs_filename_label(docs_relative: Path) -> str:
    name = docs_relative.name
    return name[:-3] if name.endswith(".md") else name


def render_sidebar(groups: list[dict[str, Any]], current_url: str) -> str:
    sections = [f"<a class=\"brand__home\" href=\"{relative_href(Path(current_url), 'index.html')}\">Documentation Home</a>"]
    for group in groups:
        sections.append(
            "<section class=\"sidebar__group\">"
            f"<h2>{html.escape(group['label'])}</h2>"
            f"{render_nav_items(group['items'], current_url)}"
            "</section>"
        )
    sections.append(
        "<section class=\"sidebar__group sidebar__group--meta\">"
        "<h2>Search</h2>"
        "<p>Use <kbd>/</kbd> to focus the search field and jump across guides, references and scenarios.</p>"
        "</section>"
    )
    return "".join(sections)


def render_nav_items(items: list[dict[str, Any]], current_url: str) -> str:
    rendered = ["<ul class=\"nav-list\">"]
    for item in items:
        children = item.get("children")
        url = item.get("url")
        label = html.escape(str(item["label"]))
        if children:
            is_open = contains_active(children, current_url)
            rendered.append(
                f"<li class=\"nav-list__branch\"><details {'open' if is_open else ''}>"
                f"<summary>{label}</summary>"
                f"{render_nav_items(children, current_url)}"
                "</details></li>"
            )
            continue
        active = " nav-list__link--active" if url == current_url else ""
        rendered.append(
            "<li>"
            f"<a class=\"nav-list__link{active}\" href=\"{html.escape(relative_href(Path(current_url), str(url)))}\">{label}</a>"
            "</li>"
        )
    rendered.append("</ul>")
    return "".join(rendered)


def contains_active(items: list[dict[str, Any]], current_url: str) -> bool:
    for item in items:
        if item.get("url") == current_url:
            return True
        children = item.get("children")
        if children and contains_active(children, current_url):
            return True
    return False


def render_toc(headings: list[dict[str, Any]], current_url: str) -> str:
    if not headings:
        return "<p class=\"toc__empty\">No section map for this page.</p>"

    links: list[str] = ["<ul class=\"toc-list\">"]
    for heading in headings:
        heading_id = html.escape(str(heading["id"]))
        name = html.escape(str(heading["name"]))
        level = int(heading.get("level", "2"))
        indent_class = f" toc-list__item--level-{min(level, 4)}"
        links.append(
            "<li class=\"toc-list__item"
            f"{indent_class}\"><a href=\"#{heading_id}\">{name}</a></li>"
        )
    links.append("</ul>")
    return "".join(links)


def render_breadcrumbs(source_relative: Path, current_url: str, current_title: str) -> str:
    crumbs = [{"label": "Docs", "url": "index.html"}]
    parts = list(source_relative.parts)
    for index, part in enumerate(parts[:-1], start=1):
        partial = Path(*parts[:index])
        if partial == Path("reference"):
            target = "reference/index.html"
        else:
            target = None
        crumbs.append({"label": humanize_segment(part), "url": target})
    if source_relative.parts and source_relative.parts[0] == "reference":
        current_label = docs_filename_label(source_relative)
    else:
        current_label = current_title
    crumbs.append({"label": current_label, "url": None})

    rendered = ["<nav class=\"breadcrumbs\" aria-label=\"Breadcrumb\">"]
    for crumb in crumbs[:-1]:
        label = html.escape(str(crumb["label"]))
        target = crumb["url"]
        if target:
            href = html.escape(relative_href(Path(current_url), target))
            rendered.append(f"<a href=\"{href}\">{label}</a>")
        else:
            rendered.append(f"<span>{label}</span>")
    rendered.append(f"<span aria-current=\"page\">{html.escape(str(crumbs[-1]['label']))}</span>")
    rendered.append("</nav>")
    return "".join(rendered)


def build_page_document(
    *,
    page_title: str,
    description: str,
    current_url: str,
    sidebar_html: str,
    toc_html: str,
    breadcrumbs_html: str,
    content_html: str,
    generated_at: str,
) -> str:
    assets_prefix = html.escape(relative_href(Path(current_url), "assets/site.css"))
    data_prefix = html.escape(relative_href(Path(current_url), "assets/site-data.js"))
    script_prefix = html.escape(relative_href(Path(current_url), "assets/site.js"))
    icon_prefix = html.escape(relative_href(Path(current_url), "assets/favicon.svg"))
    safe_title = html.escape(page_title)
    safe_description = html.escape(description)
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} | NOVA-SYNESIS Docs</title>
  <meta name="description" content="{safe_description}">
  <link rel="icon" type="image/svg+xml" href="{icon_prefix}">
  <link rel="stylesheet" href="{assets_prefix}">
</head>
<body data-page-url="{html.escape(current_url)}">
  <div class="site-shell">
    <aside class="site-sidebar" id="site-sidebar">
      <div class="brand">
        <p class="brand__eyebrow">Neural Orchestration Visual Autonomy</p>
        <h1>NOVA-SYNESIS</h1>
        <p class="brand__subtitle">Stateful Yielding Node-based Execution Semantic Integrated Surface</p>
      </div>
      <label class="search-box">
        <span class="search-box__label">Search docs</span>
        <input id="docs-search" type="search" placeholder="Search guides, files, handlers, policies">
      </label>
      <div class="search-results" id="search-results" hidden></div>
      <div class="sidebar-scroll">
        {sidebar_html}
      </div>
    </aside>

    <div class="site-main">
      <header class="site-header">
        <button class="site-header__toggle" type="button" id="sidebar-toggle" aria-controls="site-sidebar" aria-expanded="false">
          Menu
        </button>
        <div class="site-header__meta">
          <p class="site-header__eyebrow">Generated documentation surface</p>
          <h2>{safe_title}</h2>
        </div>
        <div class="site-header__status">
          <span class="status-chip">HTML docs</span>
          <span class="status-chip status-chip--accent">{generated_at}</span>
        </div>
      </header>

      <main class="content-shell">
        <article class="doc-article">
          {breadcrumbs_html}
          <section class="doc-hero">
            <p class="doc-hero__eyebrow">Documentation</p>
            <h1>{safe_title}</h1>
            <p>{safe_description}</p>
          </section>
          <section class="doc-content">
            {content_html}
          </section>
        </article>
        <aside class="doc-toc">
          <div class="doc-toc__card">
            <p class="doc-toc__eyebrow">On this page</p>
            {toc_html}
          </div>
        </aside>
      </main>
    </div>
  </div>
  <script src="{data_prefix}"></script>
  <script src="{script_prefix}"></script>
</body>
</html>
"""


def code_language_for(path: Path) -> str:
    mapping = {
        ".py": "python",
        ".ps1": "powershell",
        ".cmd": "batch",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "jsx",
        ".css": "css",
        ".html": "html",
        ".json": "json",
        ".md": "markdown",
        ".toml": "toml",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".mmd": "mermaid",
    }
    return mapping.get(path.suffix.casefold(), "text")


def build_source_file_content(target_path: Path) -> tuple[str, str]:
    relative = target_path.relative_to(ROOT).as_posix()
    content = read_text(target_path)
    line_count = len(content.splitlines())
    language = code_language_for(target_path)
    html_content = (
        "<section class=\"source-meta\">"
        f"<p class=\"doc-hero__eyebrow\">Repository file</p><h1>{html.escape(relative)}</h1>"
        f"<p>Rendered source view for the repository file. {line_count} lines.</p>"
        "</section>"
        "<pre class=\"source-block\"><code class=\"language-"
        f"{html.escape(language)}\">{html.escape(content)}</code></pre>"
    )
    description = f"Repository file view for {relative}"
    return html_content, description


def build_source_directory_content(target_path: Path, current_url: str) -> tuple[str, str]:
    relative = target_path.relative_to(ROOT).as_posix()
    rows = []
    for child in sorted(target_path.iterdir(), key=lambda item: (item.is_file(), item.name.casefold())):
        if child.name.startswith(".git"):
            continue
        child_rel = child.relative_to(ROOT)
        if child.is_dir():
            child_url = (Path("repo") / child_rel / "index.html").as_posix()
            kind = "Directory"
        elif is_binary_asset(child):
            child_url = (Path("repo-assets") / child_rel).as_posix()
            kind = "Asset"
        else:
            child_url = (Path("repo") / child_rel.with_suffix(child.suffix + ".html")).as_posix()
            kind = "File"
        rows.append(
            "<li>"
            f"<a href=\"{html.escape(relative_href(Path(current_url), child_url))}\">{html.escape(child.name)}</a>"
            f"<span>{kind}</span>"
            "</li>"
        )
    html_content = (
        "<section class=\"source-meta\">"
        f"<p class=\"doc-hero__eyebrow\">Repository directory</p><h1>{html.escape(relative)}</h1>"
        "<p>Directory listing generated for local file references used in the documentation.</p>"
        "</section>"
        "<ul class=\"directory-list\">"
        f"{''.join(rows)}"
        "</ul>"
    )
    description = f"Repository directory view for {relative}"
    return html_content, description


def write_page(output_path: Path, document: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")


def build_search_index(pages: list[Page]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for page in pages:
        entries.append(
            {
                "title": page.title,
                "url": page.url,
                "group": page.group,
                "description": page.description,
                "headings": [heading["name"] for heading in page.headings],
                "body": page.plain_text[:4000],
            }
        )
    return entries


def build_site_home_markdown(page_map: dict[Path, Page]) -> str:
    lines = [
        "# Projekt- und Flow-Dokumentation",
        "",
        "Diese HTML-Seite ist bewusst auf technische Projektdokumentation und Beispiel-Flows reduziert.",
        "Nicht enthalten sind Whitepaper, Fachartikel, README-artige Uebersichten oder sonstige Begleittexte.",
        "",
        "## Technische Bereiche",
        "",
    ]
    for path_text in WEB_GUIDE_ORDER:
        path = Path(path_text)
        page = page_map.get(path)
        if page is None:
            continue
        lines.append(f"- [{page.title}]({page.docs_relative_path.as_posix()})")
    lines += [
        "",
        "## Beispielprojekte und Beispiel-Flows",
        "",
        "- [Referenzindex](reference/index.md)",
    ]
    for candidate in (
        Path("reference/Use_Cases/accounts_receivable_reminder/AUSFUEHRLICHE_DOKUMENTATION.md.md"),
        Path("reference/Use_Cases/accounts_receivable_reminder/flow.web_ui.orders_csv.json.md"),
        Path("reference/Use_Cases/accounts_receivable_reminder/flow.web_ui.orders_db.json.md"),
        Path("reference/Use_Cases/platform_health_snapshot/flow.json.md"),
        Path("reference/Use_Cases/semantic_ticket_triage/flow.json.md"),
        Path("reference/Use_Cases/LLM_Planer/prompt_05_accounts_receivable_csv.txt.md"),
        Path("reference/Use_Cases/LLM_Planer/prompt_06_accounts_receivable_db.txt.md"),
    ):
        page = page_map.get(candidate)
        if page is not None:
            lines.append(f"- [{page.title}]({candidate.as_posix()})")
    lines += [
        "",
        "## Fokus der HTML-Seite",
        "",
        "- Projektcode, technische Referenz und echte Beispiel-Flows",
        "- Use-Case-Dateien, Prompt-Beispiele, Setup- und Run-Skripte",
        "- keine Whitepaper-, Fachartikel- oder README-Sammlungen",
        "",
    ]
    return "\n".join(lines)


def build_filtered_reference_index_markdown(page_map: dict[Path, Page]) -> str:
    lines = [
        "# Referenzindex",
        "",
        "Dieser HTML-Index zeigt nur technischen Projektcode und Beispiel-Flows, die fuer die Web-Dokumentation freigegeben sind.",
        "",
    ]
    grouped: dict[str, list[Path]] = {}
    for docs_relative in sorted(page_map):
        if not docs_relative.parts or docs_relative.parts[0] != "reference" or docs_relative == Path("reference/index.md"):
            continue
        repo_relative = reference_docs_relative_to_repo_relative(docs_relative)
        if repo_relative is None:
            continue
        group_name = repo_relative.parts[0] if repo_relative.parts else "Sonstiges"
        grouped.setdefault(group_name, []).append(docs_relative)

    for group_name in sorted(grouped.keys(), key=str.casefold):
        lines += [f"## {humanize_segment(group_name)}", ""]
        for docs_relative in grouped[group_name]:
            page = page_map[docs_relative]
            lines.append(f"- [{page.title}]({docs_relative.as_posix()})")
        lines.append("")

    return "\n".join(lines)


def write_static_assets(search_index: list[dict[str, Any]], nav_groups: list[dict[str, Any]]) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "site.css").write_text(SITE_CSS, encoding="utf-8")
    (ASSETS / "site-data.js").write_text(
        "window.NOVA_SYNESIS_SEARCH_INDEX = "
        + escape_script_json(search_index)
        + ";\nwindow.NOVA_SYNESIS_NAVIGATION = "
        + escape_script_json(nav_groups)
        + ";\n",
        encoding="utf-8",
    )
    (ASSETS / "site.js").write_text(SITE_JS, encoding="utf-8")
    (ASSETS / "favicon.svg").write_text(FAVICON_SVG, encoding="utf-8")


def collect_pages() -> dict[Path, Page]:
    pages: dict[Path, Page] = {}
    for source_path in sorted(DOCS.rglob("*.md")):
        docs_relative = source_path.relative_to(DOCS)
        if not should_include_doc_page(docs_relative):
            continue
        output_relative = markdown_output_path(docs_relative)
        if docs_relative == Path("README.md"):
            markdown_text = "# Projekt- und Flow-Dokumentation"
            title = "Projekt- und Flow-Dokumentation"
            description = "Technische HTML-Dokumentation fuer Projektcode und Beispiel-Flows."
        elif docs_relative == Path("reference/index.md"):
            markdown_text = "# Referenzindex"
            title = "Referenzindex"
            description = "Gefilterte Referenz auf Projektcode, Konfiguration und Beispiel-Flows."
        else:
            markdown_text = read_text(source_path)
            title = page_title(markdown_text, fallback=humanize_segment(docs_relative.stem))
            description = first_paragraph(markdown_text) or title
        group = "Reference" if docs_relative.parts and docs_relative.parts[0] == "reference" else "Guide"
        pages[docs_relative] = Page(
            source_path=source_path,
            docs_relative_path=docs_relative,
            output_relative_path=output_relative,
            output_path=WEB / output_relative,
            url=output_relative.as_posix(),
            title=title,
            description=description,
            group=group,
        )
    return pages


def copy_doc_assets(doc_assets: set[Path]) -> None:
    for asset_path in sorted(doc_assets):
        relative = asset_path.relative_to(DOCS)
        destination = WEB / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset_path, destination)


def copy_repo_assets(repo_assets: set[Path]) -> None:
    for asset_path in sorted(repo_assets):
        relative = asset_path.relative_to(ROOT)
        destination = REPO_ASSETS / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset_path, destination)


def build_repo_pages(
    repo_file_pages: dict[Path, RepoSourcePage],
    repo_dir_pages: dict[Path, RepoSourcePage],
    search_index: list[dict[str, Any]],
    nav_groups: list[dict[str, Any]],
    generated_at: str,
) -> None:
    for page in repo_file_pages.values():
        content_html, description = build_source_file_content(page.target_path)
        document = build_page_document(
            page_title=page.title,
            description=description,
            current_url=page.url,
            sidebar_html=render_sidebar(nav_groups, page.url),
            toc_html="<p class=\"toc__empty\">Repository view</p>",
            breadcrumbs_html=render_breadcrumbs(Path("reference"), page.url, page.title),
            content_html=content_html,
            generated_at=generated_at,
        )
        write_page(page.output_path, document)

    for page in repo_dir_pages.values():
        content_html, description = build_source_directory_content(page.target_path, page.url)
        document = build_page_document(
            page_title=page.title,
            description=description,
            current_url=page.url,
            sidebar_html=render_sidebar(nav_groups, page.url),
            toc_html="<p class=\"toc__empty\">Directory listing</p>",
            breadcrumbs_html=render_breadcrumbs(Path("reference"), page.url, page.title),
            content_html=content_html,
            generated_at=generated_at,
        )
        write_page(page.output_path, document)


def build_web_docs() -> None:
    if WEB.exists():
        shutil.rmtree(WEB)
    WEB.mkdir(parents=True, exist_ok=True)

    pages = collect_pages()
    repo_file_pages: dict[Path, RepoSourcePage] = {}
    repo_dir_pages: dict[Path, RepoSourcePage] = {}
    doc_assets: set[Path] = set()
    repo_assets: set[Path] = set()

    for page in pages.values():
        build_markdown_page(
            page=page,
            page_map=pages,
            repo_file_pages=repo_file_pages,
            repo_dir_pages=repo_dir_pages,
            doc_assets=doc_assets,
            repo_assets=repo_assets,
        )

    nav_groups = build_navigation(pages)
    search_index = build_search_index(list(pages.values()))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    write_static_assets(search_index, nav_groups)

    for page in pages.values():
        document = build_page_document(
            page_title=page.title,
            description=page.description,
            current_url=page.url,
            sidebar_html=render_sidebar(nav_groups, page.url),
            toc_html=render_toc(page.headings, page.url),
            breadcrumbs_html=render_breadcrumbs(page.docs_relative_path, page.url, page.title),
            content_html=page.html_content,
            generated_at=generated_at,
        )
        write_page(page.output_path, document)

    copy_doc_assets(doc_assets)
    copy_repo_assets(repo_assets)
    build_repo_pages(repo_file_pages, repo_dir_pages, search_index, nav_groups, generated_at)

    print(
        f"Built NOVA-SYNESIS HTML docs from {DOCS.name} with {len(pages)} documentation pages, "
        f"{len(repo_file_pages)} repository file views and {len(repo_dir_pages)} directory views in {WEB}"
    )


SITE_CSS = """
:root {
  --bg: #07111f;
  --panel: rgba(11, 24, 39, 0.88);
  --surface-border: rgba(125, 166, 214, 0.18);
  --text: #e9f2ff;
  --text-muted: #9db1c9;
  --text-dim: #74879f;
  --accent: #f3c969;
  --cyan: #73dfd2;
  --shadow: 0 22px 60px rgba(0, 0, 0, 0.32);
  --radius: 24px;
  --font-body: "Sora", "Segoe UI Variable", "Segoe UI", sans-serif;
  --font-code: "IBM Plex Mono", "Cascadia Code", "Consolas", monospace;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }

body {
  margin: 0;
  min-height: 100vh;
  font-family: var(--font-body);
  color: var(--text);
  background:
    radial-gradient(circle at top left, rgba(115, 223, 210, 0.14), transparent 26%),
    radial-gradient(circle at top right, rgba(243, 201, 105, 0.16), transparent 22%),
    linear-gradient(180deg, #08101b 0%, #0a1623 45%, #08111d 100%);
}

a { color: inherit; text-decoration: none; }
code, pre, kbd { font-family: var(--font-code); }

.site-shell {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  min-height: 100vh;
}

.site-sidebar {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  height: 100vh;
  padding: 1.4rem 1.2rem 1.2rem;
  background: linear-gradient(180deg, rgba(6, 15, 27, 0.97), rgba(8, 17, 29, 0.93));
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(18px);
  z-index: 20;
}

.brand {
  padding: 1.1rem 1rem;
  border-radius: var(--radius);
  background: linear-gradient(135deg, rgba(11, 25, 42, 0.92), rgba(9, 18, 31, 0.72));
  border: 1px solid rgba(243, 201, 105, 0.18);
  box-shadow: var(--shadow);
}

.brand h1 { margin: 0.3rem 0 0; font-size: 2rem; letter-spacing: -0.04em; }

.brand__eyebrow,
.site-header__eyebrow,
.doc-hero__eyebrow,
.doc-toc__eyebrow,
.search-box__label {
  margin: 0;
  font-size: 0.73rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--accent);
}

.brand__subtitle {
  margin: 0.7rem 0 0;
  color: var(--text-muted);
  line-height: 1.55;
}

.brand__home {
  display: inline-flex;
  align-items: center;
  padding: 0.75rem 0.95rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-muted);
}

.brand__home:hover { background: rgba(255, 255, 255, 0.08); color: var(--text); }
.sidebar-scroll { overflow: auto; padding-right: 0.3rem; }
.sidebar-scroll::-webkit-scrollbar, .doc-content::-webkit-scrollbar { width: 10px; }
.sidebar-scroll::-webkit-scrollbar-thumb, .doc-content::-webkit-scrollbar-thumb {
  background: rgba(117, 148, 186, 0.25);
  border-radius: 999px;
}

.search-box {
  display: grid;
  gap: 0.55rem;
  padding: 0.9rem 1rem;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.search-box input {
  width: 100%;
  padding: 0.95rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  background: rgba(8, 16, 29, 0.95);
  color: var(--text);
  outline: none;
}

.search-box input:focus {
  border-color: rgba(115, 223, 210, 0.55);
  box-shadow: 0 0 0 4px rgba(115, 223, 210, 0.1);
}

.search-results {
  max-height: 320px;
  overflow: auto;
  border-radius: 18px;
  background: rgba(8, 16, 29, 0.97);
  border: 1px solid rgba(115, 223, 210, 0.18);
  box-shadow: var(--shadow);
}

.search-results__item {
  display: grid;
  gap: 0.3rem;
  padding: 0.95rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.search-results__item:last-child { border-bottom: none; }
.search-results__item:hover { background: rgba(255, 255, 255, 0.04); }
.search-results__path {
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--cyan);
}

.search-results__title { font-weight: 600; }
.search-results__excerpt { color: var(--text-muted); font-size: 0.95rem; line-height: 1.55; }
.sidebar__group { margin-top: 1.2rem; }
.sidebar__group h2 {
  margin: 0 0 0.8rem;
  font-size: 0.82rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-dim);
}

.sidebar__group--meta p { margin: 0; color: var(--text-muted); line-height: 1.6; font-size: 0.95rem; }
.nav-list { display: grid; gap: 0.25rem; margin: 0; padding: 0; list-style: none; }
.nav-list__link, .nav-list summary {
  display: block;
  padding: 0.7rem 0.85rem;
  border-radius: 12px;
  color: var(--text-muted);
}

.nav-list__link:hover, .nav-list summary:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text);
  transform: translateX(2px);
}

.nav-list__link--active {
  background: linear-gradient(135deg, rgba(243, 201, 105, 0.18), rgba(115, 223, 210, 0.12));
  color: var(--text);
  border: 1px solid rgba(243, 201, 105, 0.15);
}

.nav-list__branch summary { cursor: pointer; list-style: none; }
.nav-list__branch summary::-webkit-details-marker { display: none; }
.nav-list__branch .nav-list {
  margin-left: 0.55rem;
  padding-left: 0.55rem;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
}

.site-main { min-width: 0; }
.site-header {
  position: sticky;
  top: 0;
  z-index: 12;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.2rem 2rem;
  background: rgba(6, 14, 25, 0.76);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(18px);
}

.site-header__meta h2 { margin: 0.25rem 0 0; font-size: 1.15rem; }
.site-header__toggle {
  display: none;
  padding: 0.75rem 1rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text);
}

.site-header__status { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.status-chip {
  padding: 0.55rem 0.85rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
  font-size: 0.84rem;
}

.status-chip--accent { background: rgba(243, 201, 105, 0.12); color: var(--accent); }
.content-shell { display: grid; grid-template-columns: minmax(0, 1fr) 280px; gap: 2rem; padding: 2rem; }
.doc-article { min-width: 0; }
.breadcrumbs { display: flex; flex-wrap: wrap; gap: 0.55rem; margin-bottom: 1rem; color: var(--text-dim); font-size: 0.92rem; }
.breadcrumbs a::after, .breadcrumbs span:not(:last-child)::after { content: "/"; margin-left: 0.55rem; color: rgba(255, 255, 255, 0.18); }
.doc-hero, .doc-content, .doc-toc__card {
  border-radius: var(--radius);
  border: 1px solid var(--surface-border);
  background: linear-gradient(180deg, rgba(13, 25, 40, 0.94), rgba(9, 18, 30, 0.92));
  box-shadow: var(--shadow);
}

.doc-hero { padding: 1.7rem 1.8rem; margin-bottom: 1.4rem; }
.doc-hero h1 { margin: 0.5rem 0 0.7rem; font-size: clamp(2rem, 4vw, 3.2rem); letter-spacing: -0.05em; }
.doc-hero p { margin: 0; max-width: 58rem; color: var(--text-muted); line-height: 1.7; }
.doc-content { padding: 2rem 2.15rem; line-height: 1.8; }
.doc-content > *:first-child { margin-top: 0; }
.doc-content h1, .doc-content h2, .doc-content h3, .doc-content h4 { margin-top: 2rem; margin-bottom: 0.7rem; letter-spacing: -0.03em; scroll-margin-top: 7rem; }
.doc-content h2 { font-size: 1.7rem; }
.doc-content h3 { font-size: 1.25rem; }
.heading-anchor { color: inherit; text-decoration: none; }
.heading-anchor:hover { color: var(--accent); }
.doc-content p, .doc-content li { color: var(--text-muted); }
.doc-content strong, .doc-content b { color: var(--text); }
.doc-content a { color: var(--cyan); text-decoration: underline; text-decoration-color: rgba(115, 223, 210, 0.35); }
.doc-content pre {
  overflow: auto;
  padding: 1rem 1.1rem;
  border-radius: 18px;
  background: rgba(5, 11, 20, 0.98);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.doc-content code { padding: 0.18rem 0.35rem; border-radius: 7px; background: rgba(255, 255, 255, 0.07); color: #f7d98f; }
.doc-content pre code { padding: 0; background: transparent; color: #dce9ff; }
.doc-content blockquote { margin: 1.4rem 0; padding: 0.9rem 1rem; border-left: 3px solid rgba(115, 223, 210, 0.55); background: rgba(255, 255, 255, 0.03); color: var(--text-muted); }
.doc-content table { width: 100%; border-collapse: collapse; margin: 1.3rem 0; overflow: hidden; border-radius: 18px; background: rgba(255, 255, 255, 0.03); }
.doc-content th, .doc-content td { padding: 0.95rem 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.08); text-align: left; }
.doc-content th { color: var(--text); background: rgba(255, 255, 255, 0.04); }
.doc-content hr { border: none; height: 1px; background: rgba(255, 255, 255, 0.08); margin: 2rem 0; }
.doc-content img { display: block; max-width: 100%; border-radius: 18px; border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: var(--shadow); }
.doc-toc { position: sticky; top: 6.8rem; align-self: start; }
.doc-toc__card { padding: 1.25rem 1.1rem; }
.toc-list { margin: 0; padding: 0; list-style: none; display: grid; gap: 0.4rem; }
.toc-list__item a { display: block; padding: 0.5rem 0.65rem; border-radius: 10px; color: var(--text-muted); }
.toc-list__item a:hover { background: rgba(255, 255, 255, 0.05); color: var(--text); }
.toc-list__item--level-3 { margin-left: 0.7rem; }
.toc-list__item--level-4 { margin-left: 1.2rem; }
.toc__empty { margin: 0; color: var(--text-dim); }
.source-meta { margin-bottom: 1.4rem; }
.source-block { padding: 1.1rem 1.15rem; border-radius: 20px; background: rgba(5, 11, 20, 0.98); border: 1px solid rgba(255, 255, 255, 0.07); overflow: auto; }
.directory-list { display: grid; gap: 0.65rem; padding: 0; margin: 0; list-style: none; }
.directory-list li { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: 0.85rem 1rem; border-radius: 16px; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.06); }
.directory-list span { color: var(--text-dim); font-size: 0.88rem; }
kbd { padding: 0.18rem 0.38rem; border-radius: 7px; border: 1px solid rgba(255, 255, 255, 0.15); background: rgba(255, 255, 255, 0.04); color: var(--text); }

@media (max-width: 1320px) {
  .content-shell { grid-template-columns: minmax(0, 1fr); }
  .doc-toc { display: none; }
}

@media (max-width: 1040px) {
  .site-shell { grid-template-columns: 1fr; }
  .site-sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: min(88vw, 340px);
    transform: translateX(-100%);
    transition: transform 180ms ease;
  }
  .site-sidebar.site-sidebar--open { transform: translateX(0); }
  .site-header__toggle { display: inline-flex; }
}

@media (max-width: 760px) {
  .site-header, .content-shell { padding-left: 1rem; padding-right: 1rem; }
  .doc-content, .doc-hero { padding: 1.35rem; }
  .site-header { flex-wrap: wrap; }
}
"""


SITE_JS = """
(() => {
  const pageUrl = document.body.dataset.pageUrl || "index.html";
  const sidebar = document.getElementById("site-sidebar");
  const toggle = document.getElementById("sidebar-toggle");
  const searchInput = document.getElementById("docs-search");
  const searchResults = document.getElementById("search-results");
  const searchIndex = Array.isArray(window.NOVA_SYNESIS_SEARCH_INDEX) ? window.NOVA_SYNESIS_SEARCH_INDEX : [];

  if (toggle && sidebar) {
    toggle.addEventListener("click", () => {
      const open = sidebar.classList.toggle("site-sidebar--open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement !== searchInput) {
      event.preventDefault();
      searchInput?.focus();
      searchInput?.select();
    }
    if (event.key === "Escape") {
      searchResults?.setAttribute("hidden", "");
      if (document.activeElement === searchInput) {
        searchInput.blur();
      }
      sidebar?.classList.remove("site-sidebar--open");
      toggle?.setAttribute("aria-expanded", "false");
    }
  });

  function tokenize(query) {
    return query.toLowerCase().split(/\\s+/).map((token) => token.trim()).filter(Boolean);
  }

  function toRelativeUrl(targetUrl) {
    const fromParts = pageUrl.split("/").slice(0, -1);
    const toParts = String(targetUrl).split("/");

    while (fromParts.length && toParts.length && fromParts[0] === toParts[0]) {
      fromParts.shift();
      toParts.shift();
    }

    const prefix = fromParts.map(() => "..");
    const joined = [...prefix, ...toParts].join("/");
    return joined || "index.html";
  }

  function scoreEntry(entry, tokens, rawQuery) {
    const title = String(entry.title || "").toLowerCase();
    const description = String(entry.description || "").toLowerCase();
    const headings = Array.isArray(entry.headings) ? entry.headings.join(" ").toLowerCase() : "";
    const body = String(entry.body || "").toLowerCase();
    let score = 0;

    for (const token of tokens) {
      if (title.includes(token)) score += 60;
      else if (headings.includes(token)) score += 28;
      else if (description.includes(token)) score += 18;
      else if (body.includes(token)) score += 8;
      else return 0;
    }

    if (title.includes(rawQuery)) score += 40;
    if (entry.url === pageUrl) score += 4;
    return score;
  }

  function buildExcerpt(entry, query) {
    const haystack = `${entry.description || ""} ${entry.body || ""}`.replace(/\\s+/g, " ").trim();
    if (!haystack) return "";
    const lower = haystack.toLowerCase();
    const index = lower.indexOf(query);
    if (index === -1) return haystack.slice(0, 160);
    const start = Math.max(0, index - 50);
    const end = Math.min(haystack.length, index + 110);
    const prefix = start > 0 ? "…" : "";
    const suffix = end < haystack.length ? "…" : "";
    return `${prefix}${haystack.slice(start, end)}${suffix}`;
  }

  function renderResults(results, rawQuery) {
    if (!searchResults) return;
    if (!rawQuery) {
      searchResults.innerHTML = "";
      searchResults.setAttribute("hidden", "");
      return;
    }

    if (!results.length) {
      searchResults.innerHTML = `<div class="search-results__item"><div class="search-results__title">No results</div><div class="search-results__excerpt">No documentation page matches "${rawQuery}".</div></div>`;
      searchResults.removeAttribute("hidden");
      return;
    }

    searchResults.innerHTML = results.map((entry) => `
      <a class="search-results__item" href="${toRelativeUrl(entry.url)}">
        <span class="search-results__path">${entry.group || "Docs"}</span>
        <span class="search-results__title">${entry.title}</span>
        <span class="search-results__excerpt">${buildExcerpt(entry, rawQuery.toLowerCase())}</span>
      </a>
    `).join("");
    searchResults.removeAttribute("hidden");
  }

  searchInput?.addEventListener("input", (event) => {
    const rawQuery = String(event.target.value || "").trim();
    const tokens = tokenize(rawQuery);
    if (!tokens.length) {
      renderResults([], "");
      return;
    }

    const results = searchIndex
      .map((entry) => ({ ...entry, _score: scoreEntry(entry, tokens, rawQuery.toLowerCase()) }))
      .filter((entry) => entry._score > 0)
      .sort((left, right) => right._score - left._score)
      .slice(0, 12);

    renderResults(results, rawQuery);
  });

  document.addEventListener("click", (event) => {
    if (!searchResults || !searchInput) return;
    const target = event.target;
    if (target instanceof Node && (searchResults.contains(target) || searchInput.contains(target))) return;
    searchResults.setAttribute("hidden", "");
  });
})();
"""


FAVICON_SVG = """
<svg width="128" height="128" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="nova-core" x1="18" y1="18" x2="110" y2="110" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#73DFD2"/>
      <stop offset="1" stop-color="#F3C969"/>
    </linearGradient>
  </defs>
  <rect x="10" y="10" width="108" height="108" rx="28" fill="#08111D" stroke="url(#nova-core)" stroke-width="4"/>
  <path d="M34 88V40L64 68L94 40V88" stroke="url(#nova-core)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="34" cy="88" r="7" fill="#73DFD2"/>
  <circle cx="94" cy="88" r="7" fill="#F3C969"/>
</svg>
"""


if __name__ == "__main__":
    build_web_docs()
