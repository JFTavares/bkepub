# bkepub/utils.py
import uuid
import datetime
import re
import os
from urllib.parse import unquote
from pathlib import Path
from . import constants

def generate_unique_id(prefix="id"):
    """Generates a unique ID string suitable for XML IDs."""
    return f"{prefix}-{uuid.uuid4()}"

def get_formatted_date():
    """Returns the current UTC date formatted for EPUB metadata."""
    return datetime.datetime.now(datetime.timezone.utc).strftime(constants.MODIFIED_DATE_FORMAT)

def sanitize_href(href: str) -> str:
    """
    Sanitizes a string to be used as an href/filename within the EPUB.
    Replaces spaces, handles URL encoding, and ensures relative path.
    """
    # Decode URL-encoded characters (e.g., %20 -> space)
    decoded_href = unquote(href)
    # Replace common problematic characters (spaces, etc.) with underscores
    safe_href = re.sub(r'[\\/*?"<>|\s]+', '_', decoded_href)
    # Remove leading/trailing underscores/slashes that might result
    safe_href = safe_href.strip('_/')
    # Ensure it doesn't try to go up directories (basic protection)
    safe_href = safe_href.replace('../', '')
    # Normalize path separators to forward slash (for OPF/zip)
    safe_href = safe_href.replace('\\', '/')
    # Ensure it's not empty after sanitization
    if not safe_href:
        return f"file_{generate_unique_id()}"
    return safe_href

def get_media_type(filename: str) -> str:
    """Guesses media type from filename extension (case-insensitive)."""
    ext = Path(filename).suffix.lower().lstrip('.')
    if ext in ['xhtml', 'html', 'htm']:
        return constants.MEDIA_TYPE_XHTML
    elif ext == 'css':
        return constants.MEDIA_TYPE_CSS
    elif ext == 'jpg' or ext == 'jpeg':
        return constants.MEDIA_TYPE_JPEG
    elif ext == 'png':
        return constants.MEDIA_TYPE_PNG
    elif ext == 'gif':
        return constants.MEDIA_TYPE_GIF
    elif ext == 'svg':
        return constants.MEDIA_TYPE_SVG
    elif ext == 'js':
        return constants.MEDIA_TYPE_JAVASCRIPT
    elif ext == 'otf':
        return constants.MEDIA_TYPE_OTF
    elif ext == 'ttf':
        return constants.MEDIA_TYPE_TTF
    elif ext == 'woff':
        return constants.MEDIA_TYPE_WOFF
    elif ext == 'woff2':
        return constants.MEDIA_TYPE_WOFF2
    elif ext == 'ncx':
        return constants.MEDIA_TYPE_NCX
    else:
        # Fallback, consider using python's `mimetypes` for more accuracy
        import mimetypes
        mtype, _ = mimetypes.guess_type(filename)
        return mtype or 'application/octet-stream'

def wrap_html_fragment(fragment: str, title: str, lang: str = constants.DEFAULT_LANG) -> str:
    """Wraps an HTML fragment in a complete, valid XHTML structure."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="{constants.NSMAP['xhtml']}" xmlns:epub="{constants.NSMAP['epub']}" xml:lang="{lang}" lang="{lang}">
<head>
  <meta charset="UTF-8"/>
  <title>{title or 'Content Document'}</title>
  {'''<!-- Add links to CSS here if needed -->''' }
</head>
<body>
{fragment}
</body>
</html>
"""

def is_full_xhtml(content: bytes) -> bool:
    """Checks if byte content looks like a full XHTML document."""
    # Simple check for doctype or html tag at the beginning, case-insensitive
    content_start = content[:100].decode('utf-8', errors='ignore').strip().lower()
    return content_start.startswith('<?xml') or \
           content_start.startswith('<!doctype html>') or \
           content_start.startswith('<html')

def ensure_bytes(content: str | bytes, encoding: str = 'utf-8') -> bytes:
    """Ensures the content is bytes, encoding if necessary."""
    if isinstance(content, str):
        return content.encode(encoding)
    elif isinstance(content, bytes):
        return content
    else:
        raise TypeError(f"Content must be str or bytes, not {type(content)}")

def get_relative_path(target_path: str, start_path: str) -> str:
    """Calculates the relative path from start_path to target_path using forward slashes."""
    try:
        # Use pathlib for robust relative path calculation
        target = Path(target_path)
        start = Path(os.path.dirname(start_path)) # Relative from the *directory* of the start file
        relative = os.path.relpath(target, start).replace("\\", "/")
        return relative
    except ValueError:
        # Happens if paths are on different drives on Windows
        return target_path.replace("\\", "/") # Fallback to absolute-like path within zip