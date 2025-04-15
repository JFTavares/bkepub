# bkepub/conversion.py
from markdown import markdown as md_converter
from .exceptions import BkEpubError
from .utils import wrap_html_fragment

def markdown_to_xhtml(markdown_content: str, title: str, lang: str) -> str:
    """Converts Markdown string to a full XHTML document string."""
    try:
        # Convert markdown to HTML fragment with XHTML output format
        html_fragment = md_converter(
            markdown_content,
            output_format='xhtml',
            extensions=['extra', 'nl2br', 'sane_lists', 'toc'] # Common extensions
        )
        # Wrap the fragment in a full XHTML structure
        full_xhtml = wrap_html_fragment(html_fragment, title=title, lang=lang)
        return full_xhtml
    except Exception as e:
        raise BkEpubError(f"Markdown conversion failed: {e}")