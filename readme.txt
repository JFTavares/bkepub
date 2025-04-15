# BkEpub

[![PyPI version](https://badge.fury.io/py/bkepub.svg)](https://badge.fury.io/py/bkepub) <!-- Adicionar após publicar -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Atualizar se licença for diferente -->

**BkEpub** is a Python library designed for easy creation and manipulation of EPUB 3 files. It provides an object-oriented interface to manage metadata, content (XHTML, CSS, images), reading order, table of contents, and also supports converting Markdown content and loading existing EPUB files.

## Features

*   **Create EPUB 3:** Build valid EPUB 3 files from scratch.
*   **Load & Modify EPUB:** Load existing `.epub` files, inspect their structure, modify them (basic support), and save changes.
*   **Object-Oriented:** Intuitive classes (`EpubBuilder`, `ManifestItem`, `MetadataManager`, etc.).
*   **Metadata Management:** Set standard Dublin Core (DC) and DCTerms metadata, including creators with roles, modification dates, etc.
*   **Content Types:** Add XHTML, CSS, Images (JPG, PNG, GIF, SVG), Fonts (OTF, TTF, WOFF), and JavaScript.
*   **Markdown Conversion:** Add content directly from Markdown strings – BkEpub handles the conversion to XHTML.
*   **HTML Fragment Wrapping:** Automatically wraps simple HTML snippets in the required full XHTML structure.
*   **Spine Control:** Define the linear reading order of your content.
*   **Navigation:**
    *   Generate EPUB 3 Navigation Document (`nav.xhtml`) from TOC entries.
    *   Define structural landmarks (cover, TOC, body matter, etc.).
    *   Optionally generate `toc.ncx` for EPUB 2 compatibility.
*   **Cover Image:** Easily designate an image as the book cover.
*   **Dependencies:** Uses `lxml` for robust XML/HTML processing and `markdown` for Markdown conversion.

## Installation

```bash
pip install bkepub