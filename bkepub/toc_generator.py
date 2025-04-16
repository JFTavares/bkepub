# bkepub/toc_generator.py
import re
from lxml import etree
from lxml import html
from . import constants
from .exceptions import BkEpubError


def extract_headings_from_html(html_content: bytes, max_level: int = 3) -> list[dict]:
    """
    Extract headings (h1-h6) from HTML content to generate TOC entries.

    Args:
        html_content: HTML content as bytes
        max_level: Maximum heading level to include (1-6)

    Returns:
        List of dicts with keys: {'level': int, 'text': str, 'id': str}
    """
    try:
        root = html.fromstring(html_content)
        headings = []

        # Find all heading elements
        for level in range(1, min(max_level + 1, 7)):
            for h_elem in root.xpath(f'//h{level}'):
                heading_text = "".join(h_elem.xpath('.//text()'))
                heading_text = heading_text.strip()

                # Skip empty headings
                if not heading_text:
                    continue

                # Check if heading already has an id
                heading_id = h_elem.get('id')

                # If no id exists, generate one from text
                if not heading_id:
                    # Create an id from the heading text
                    heading_id = f"heading-{len(headings) + 1}"
                    h_elem.set('id', heading_id)

                headings.append({
                    'level': level,
                    'text': heading_text,
                    'id': heading_id
                })

        # If we made changes to the HTML by adding IDs, return the modified content
        if headings:
            modified_content = etree.tostring(root, encoding='utf-8', method='xml')
            return headings, modified_content

        return headings, html_content

    except Exception as e:
        raise BkEpubError(f"Failed to extract headings from HTML: {e}")


def build_hierarchical_toc(heading_list: list[dict]) -> list[dict]:
    """
    Convert flat heading list to a hierarchical TOC structure.

    Args:
        heading_list: List of heading dicts from extract_headings_from_html

    Returns:
        Hierarchical TOC entries suitable for EpubBuilder.set_toc()
    """
    if not heading_list:
        return []

    # Sort headings by position in document (assuming they are in order)
    sorted_headings = list(enumerate(heading_list))

    def _build_subtree(current_level, start_idx):
        entries = []
        i = start_idx

        while i < len(sorted_headings):
            idx, heading = sorted_headings[i]

            if heading['level'] < current_level:
                # We've moved up a level, exit this subtree
                break

            if heading['level'] == current_level:
                # Create entry at this level
                entry = {
                    'label': heading['text'],
                    'href': f"#{heading['id']}",
                    'children': []
                }

                # Process any children (deeper levels)
                j = i + 1
                if j < len(sorted_headings) and sorted_headings[j][1]['level'] > current_level:
                    children, new_i = _build_subtree(current_level + 1, j)
                    entry['children'] = children
                    i = new_i
                else:
                    i += 1

                entries.append(entry)
            else:
                # Skip levels that are deeper than what we're currently processing
                i += 1

        return entries, i

    # Start building from the top level (assume it's the minimum level in the list)
    min_level = min(h['level'] for h in heading_list)
    toc_entries, _ = _build_subtree(min_level, 0)

    return toc_entries