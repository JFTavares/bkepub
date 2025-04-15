# bkepub/templates.py
from lxml import etree
from . import constants
from . import utils
from .item import ManifestItem # Import base class for type hinting

def _set_attrs(element, attrs):
    """Helper to set attributes on an lxml element."""
    for k, v in attrs.items():
        if v is not None: # Only set non-None attributes
            element.set(k, str(v))

def generate_container_xml(opf_path: str) -> bytes:
    """Generates the META-INF/container.xml content using lxml."""
    root = etree.Element("container", version="1.0", nsmap={None: constants.NSMAP['container']})
    rootfiles = etree.SubElement(root, "rootfiles")
    etree.SubElement(rootfiles, "rootfile", attrib={
        "full-path": opf_path,
        "media-type": constants.MEDIA_TYPE_OPF
    })
    return etree.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=True)

def generate_opf(
    unique_identifier_ref: str,
    metadata_elements: list[tuple],
    manifest_items: list[ManifestItem],
    spine_items: list[dict], # [{'idref': str, 'linear': bool}]
    spine_toc_ref: str | None = None # ID of the NCX item, if present
) -> bytes:
    """Generates the content.opf file content using lxml."""
    # Determine primary language from metadata for xml:lang attribute
    primary_lang = constants.DEFAULT_LANG
    for ns_uri, tag, text, attrs in metadata_elements:
        if ns_uri == constants.NSMAP['dc'] and tag == 'language':
            primary_lang = text
            break

    root = etree.Element("package",
                         version=constants.DEFAULT_EPUB_VERSION,
                         attrib={etree.QName(constants.NSMAP['xml'], 'lang'): primary_lang},
                         unique_identifier=unique_identifier_ref,
                         nsmap=constants.NSMAP) # Include all known namespaces

    # --- METADATA ---
    metadata_el = etree.SubElement(root, etree.QName(constants.NSMAP['opf'], "metadata"))
    for ns_uri, tag, text, attrs in metadata_elements:
        # Need to handle qualified attribute names (like opf:scheme)
        clean_attrs = {}
        for k, v in attrs.items():
            if k.startswith('{') and '}' in k: # Already qualified name {uri}local
                clean_attrs[k] = v
            elif ':' in k: # Convert prefix:local to {uri}local
                prefix, local = k.split(':', 1)
                uri = constants.NSMAP.get(prefix)
                if uri:
                    clean_attrs[etree.QName(uri, local)] = v
                else: # Keep unqualified if namespace unknown (warning?)
                    clean_attrs[k] = v
            else: # Unqualified attribute
                clean_attrs[k] = v

        el = etree.SubElement(metadata_el, etree.QName(ns_uri, tag), attrib=clean_attrs)
        if text:
            el.text = text

    # --- MANIFEST ---
    manifest_el = etree.SubElement(root, etree.QName(constants.NSMAP['opf'], "manifest"))
    for item in manifest_items:
        item_attrs = {
            "id": item.id,
            "href": item.href, # Already sanitized and relative
            "media-type": item.media_type
        }
        if item.properties:
            item_attrs["properties"] = " ".join(sorted(list(item.properties)))
        etree.SubElement(manifest_el, etree.QName(constants.NSMAP['opf'], "item"), attrib=item_attrs)

    # --- SPINE ---
    spine_attrs = {}
    if spine_toc_ref:
        spine_attrs["toc"] = spine_toc_ref
    spine_el = etree.SubElement(root, etree.QName(constants.NSMAP['opf'], "spine"), attrib=spine_attrs)
    for spine_ref in spine_items:
        itemref_attrs = {"idref": spine_ref['idref']}
        if not spine_ref.get('linear', True): # Default linear=yes (True)
            itemref_attrs['linear'] = 'no'
        etree.SubElement(spine_el, etree.QName(constants.NSMAP['opf'], "itemref"), attrib=itemref_attrs)

    return etree.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=True)


def generate_nav_xhtml(
    book_title: str,
    toc_entries: list[dict], # [{'label': str, 'href': str, 'children': [...]}]
    landmarks: list[dict], # [{'label': str, 'href': str, 'type': str (epub:type)}]
    language: str = constants.DEFAULT_LANG
) -> bytes:
    """Generates the nav.xhtml content using lxml."""
    # Basic HTML structure with namespaces
    html = etree.Element(etree.QName(constants.NSMAP['xhtml'], "html"),
                         nsmap={None: constants.NSMAP['xhtml'], 'epub': constants.NSMAP['epub']},
                         attrib={
                             etree.QName(constants.NSMAP['xml'], 'lang'): language,
                             'lang': language # Non-namespaced lang too
                         })

    head = etree.SubElement(html, "head")
    etree.SubElement(head, "meta", charset="utf-8")
    title_el = etree.SubElement(head, "title")
    title_el.text = f"Table of Contents: {book_title}"

    body = etree.SubElement(html, "body")

    # --- TOC Navigation ---
    nav_toc = etree.SubElement(body, "nav",
                               attrib={etree.QName(constants.NSMAP['epub'], "type"): constants.LANDMARK_TOC, "id": "toc"})
    toc_h = etree.SubElement(nav_toc, "h1") # Or h2
    toc_h.text = "Table of Contents"
    toc_ol = etree.SubElement(nav_toc, "ol")

    def build_toc_list(parent_ol, entries):
        for entry in entries:
            li = etree.SubElement(parent_ol, "li")
            # Ensure href is correctly relative if needed (templates don't know context, assume pre-calculated)
            a = etree.SubElement(li, "a", href=entry['href'])
            a.text = entry['label']
            if entry.get('children'):
                child_ol = etree.SubElement(li, "ol")
                build_toc_list(child_ol, entry['children'])

    build_toc_list(toc_ol, toc_entries)

    # --- Landmarks Navigation ---
    if landmarks:
        nav_landmarks = etree.SubElement(body, "nav",
                                         attrib={etree.QName(constants.NSMAP['epub'], "type"): "landmarks"},
                                         hidden="hidden") # Usually hidden
        landmarks_h = etree.SubElement(nav_landmarks, "h1")
        landmarks_h.text = "Landmarks"
        landmarks_ol = etree.SubElement(nav_landmarks, "ol")
        for landmark in landmarks:
            li = etree.SubElement(landmarks_ol, "li")
            # Ensure epub:type attribute is correctly namespaced
            lm_attrs = {
                'href': landmark['href'],
                etree.QName(constants.NSMAP['epub'], "type"): landmark['type']
            }
            a = etree.SubElement(li, "a", attrib=lm_attrs)
            a.text = landmark['label']

    # Use method='xml' for correct self-closing tags like <meta/>
    return etree.tostring(html, encoding='utf-8', xml_declaration=True, pretty_print=True, method='xml')

# --- Optional: NCX Generation (for EPUB 2 compatibility) ---
def generate_ncx(
    book_uid: str,
    book_title: str,
    toc_entries: list[dict] # Same structure as for nav
) -> bytes:
    """Generates the toc.ncx file content using lxml."""
    # Create the root element with namespaces
    ncx_ns = "http://www.daisy.org/z3986/2005/ncx/"
    root = etree.Element("ncx", version="2005-1",
                         nsmap={None: ncx_ns, 'xml': constants.NSMAP['xml']}) # Default NS

    head = etree.SubElement(root, "head")
    # Required meta tags for NCX
    etree.SubElement(head, "meta", name="dtb:uid", content=book_uid)
    etree.SubElement(head, "meta", name="dtb:depth", content="1") # Calculate depth later if needed
    etree.SubElement(head, "meta", name="dtb:totalPageCount", content="0") # Required, but usually 0
    etree.SubElement(head, "meta", name="dtb:maxPageNumber", content="0") # Required, but usually 0

    doc_title = etree.SubElement(root, "docTitle")
    etree.SubElement(doc_title, "text").text = book_title

    nav_map = etree.SubElement(root, "navMap")

    play_order_counter = 1
    def build_navpoint(parent_np, entries):
        nonlocal play_order_counter
        for entry in entries:
            nav_point = etree.SubElement(parent_np, "navPoint",
                                        id=f"navpoint-{play_order_counter}",
                                        playOrder=str(play_order_counter))
            play_order_counter += 1

            nav_label = etree.SubElement(nav_point, "navLabel")
            etree.SubElement(nav_label, "text").text = entry['label']

            # Assume href is already relative to content root (OEBPS)
            etree.SubElement(nav_point, "content", src=entry['href'])

            if entry.get('children'):
                build_navpoint(nav_point, entry['children']) # Recursive call

    build_navpoint(nav_map, toc_entries)

    # Calculate depth
    max_depth = 0
    def find_depth(entries, current_depth):
        nonlocal max_depth
        max_depth = max(max_depth, current_depth)
        for entry in entries:
            if entry.get('children'):
                find_depth(entry.get('children'), current_depth + 1)
    find_depth(toc_entries, 1)
    depth_meta = root.find('.//head/meta[@name="dtb:depth"]', namespaces={'': ncx_ns})
    if depth_meta is not None: depth_meta.set("content", str(max_depth))


    return etree.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=True)