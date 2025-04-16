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
    # New folder structure constants
    SUBDIR_TEXT, SUBDIR_STYLES, SUBDIR_IMAGES, SUBDIR_FONTS,
    SUBDIR_AUDIO, SUBDIR_VIDEO, SUBDIR_MISC
)
from .toc_generator import extract_headings_from_html, build_hierarchical_toc

__version__ = "0.3.0"  # Incremented version for folder structure support

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
    # Folder structure constants
    "SUBDIR_TEXT", "SUBDIR_STYLES", "SUBDIR_IMAGES", "SUBDIR_FONTS",
    "SUBDIR_AUDIO", "SUBDIR_VIDEO", "SUBDIR_MISC",
]


def load(epub_path: str, reconfigure_structure: bool = False):
    """
    Loads an existing EPUB file and returns a populated EpubBuilder instance.

    Args:
        epub_path: Path to the EPUB file
        reconfigure_structure: If True, reorganizes the content into folder structure
    """
    from .loader import load_epub
    return load_epub(epub_path, reconfigure_structure)