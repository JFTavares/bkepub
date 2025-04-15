# bkepub/__init__.py
"""
BkEpub: A Python library for creating and manipulating EPUB 3 files.
"""

from .builder import EpubBuilder
from .item import (ManifestItem, HtmlContentItem, CssStyleItem, ImageItem,
                   NavigationItem, NcxItem, FontItem, JavaScriptItem)
from .exceptions import BkEpubError, ItemNotFoundError, MissingMetadataError, EpubParseError, EpubWriteError
from .constants import (
    # Common roles can be exposed for convenience
    ROLE_AUTHOR, ROLE_EDITOR, ROLE_ILLUSTRATOR,
    # Common landmark types
    LANDMARK_TOC, LANDMARK_COVER, LANDMARK_BODMATTER, LANDMARK_TITLEPAGE,
)

__version__ = "0.2.0" # Incremented version for new features

__all__ = [
    # Core class
    "EpubBuilder",
    # Item types
    "ManifestItem",
    "HtmlContentItem",
    "CssStyleItem",
    "ImageItem",
    "NavigationItem",
    "NcxItem",
    "FontItem",
    "JavaScriptItem",
    # Exceptions
    "BkEpubError",
    "ItemNotFoundError",
    "MissingMetadataError",
    "EpubParseError",
    "EpubWriteError",
    # Constants (optional export)
    "ROLE_AUTHOR", "ROLE_EDITOR", "ROLE_ILLUSTRATOR",
    "LANDMARK_TOC", "LANDMARK_COVER", "LANDMARK_BODMATTER", "LANDMARK_TITLEPAGE",
]

# Expose the load function directly from the package
load = EpubBuilder.load