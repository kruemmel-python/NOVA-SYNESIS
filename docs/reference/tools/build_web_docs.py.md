# `tools/build_web_docs.py`

- Quellpfad: [tools/build_web_docs.py](../../../tools/build_web_docs.py)
- Kategorie: `Werkzeug`

## Aufgabe der Datei

Generiert aus dem docs-Ordner eine statische HTML-Dokumentationsseite mit Navigation, Suche und Source-Ansichten.

## Wann du diese Datei bearbeitest

Wenn Layout, Suchlogik, Seitenrouting oder die statische Web-Doku erweitert werden sollen.

## Klassen

### `Page`

Klasse `Page` dieses Moduls.

### `RepoSourcePage`

Klasse `RepoSourcePage` dieses Moduls.

## Funktionen

- `slugify(value)`: Funktion oder Definition `slugify` dieses Moduls.
- `strip_markdown(text)`: Funktion oder Definition `strip_markdown` dieses Moduls.
- `first_paragraph(markdown_text)`: Funktion oder Definition `first_paragraph` dieses Moduls.
- `read_text(path)`: Funktion oder Definition `read_text` dieses Moduls.
- `markdown_output_path(docs_relative)`: Funktion oder Definition `markdown_output_path` dieses Moduls.
- `relative_href(current_output, target_url)`: Funktion oder Definition `relative_href` dieses Moduls.
- `resolve_local_target(current_source, raw_target)`: Funktion oder Definition `resolve_local_target` dieses Moduls.
- `is_binary_asset(path)`: Funktion oder Definition `is_binary_asset` dieses Moduls.
- `page_title(markdown_text, fallback)`: Funktion oder Definition `page_title` dieses Moduls.
- `toc_to_flat_tokens(tokens)`: Funktion oder Definition `toc_to_flat_tokens` dieses Moduls.
- `parse_ordered_links(markdown_text)`: Funktion oder Definition `parse_ordered_links` dieses Moduls.
- `escape_script_json(payload)`: Funktion oder Definition `escape_script_json` dieses Moduls.
- `inject_heading_anchors(content)`: Funktion oder Definition `inject_heading_anchors` dieses Moduls.
- `build_markdown_page(page, page_map, repo_file_pages, repo_dir_pages, doc_assets, repo_assets)`: Funktion oder Definition `build_markdown_page` dieses Moduls.
- `rewrite_html_links(html_fragment, current_page, page_map, repo_file_pages, repo_dir_pages, doc_assets, repo_assets)`: Funktion oder Definition `rewrite_html_links` dieses Moduls.
- `rewrite_link_value(raw_value, current_page, attribute, page_map, repo_file_pages, repo_dir_pages, doc_assets, repo_assets)`: Funktion oder Definition `rewrite_link_value` dieses Moduls.
- `build_navigation(page_map)`: Funktion oder Definition `build_navigation` dieses Moduls.
- `build_reference_tree(page_map)`: Funktion oder Definition `build_reference_tree` dieses Moduls.
- `humanize_segment(value)`: Funktion oder Definition `humanize_segment` dieses Moduls.
- `docs_filename_label(docs_relative)`: Funktion oder Definition `docs_filename_label` dieses Moduls.
- `render_sidebar(groups, current_url)`: Funktion oder Definition `render_sidebar` dieses Moduls.
- `render_nav_items(items, current_url)`: Funktion oder Definition `render_nav_items` dieses Moduls.
- `contains_active(items, current_url)`: Funktion oder Definition `contains_active` dieses Moduls.
- `render_toc(headings, current_url)`: Funktion oder Definition `render_toc` dieses Moduls.
- `render_breadcrumbs(source_relative, current_url, current_title)`: Funktion oder Definition `render_breadcrumbs` dieses Moduls.
- `build_page_document(*, page_title, description, current_url, sidebar_html, toc_html, breadcrumbs_html, content_html, generated_at)`: Funktion oder Definition `build_page_document` dieses Moduls.
- `code_language_for(path)`: Funktion oder Definition `code_language_for` dieses Moduls.
- `build_source_file_content(target_path)`: Funktion oder Definition `build_source_file_content` dieses Moduls.
- `build_source_directory_content(target_path, current_url)`: Funktion oder Definition `build_source_directory_content` dieses Moduls.
- `write_page(output_path, document)`: Funktion oder Definition `write_page` dieses Moduls.
- `build_search_index(pages)`: Funktion oder Definition `build_search_index` dieses Moduls.
- `write_static_assets(search_index, nav_groups)`: Funktion oder Definition `write_static_assets` dieses Moduls.
- `collect_pages()`: Funktion oder Definition `collect_pages` dieses Moduls.
- `copy_doc_assets(doc_assets)`: Funktion oder Definition `copy_doc_assets` dieses Moduls.
- `copy_repo_assets(repo_assets)`: Funktion oder Definition `copy_repo_assets` dieses Moduls.
- `build_repo_pages(repo_file_pages, repo_dir_pages, search_index, nav_groups, generated_at)`: Funktion oder Definition `build_repo_pages` dieses Moduls.
- `build_web_docs()`: Funktion oder Definition `build_web_docs` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import html`
- `import json`
- `import mimetypes`
- `import posixpath`
- `import re`
- `import shutil`
- `from dataclasses import dataclass, field`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import Any`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [docs/README.md](../docs/README.md.md)
- [README.md](../README.md.md)
- [web/index.html](../web/index.html.md)
