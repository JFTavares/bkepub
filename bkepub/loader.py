# bkepub/loader.py
import zipfile
import os
from lxml import etree
from io import BytesIO

from .builder import EpubBuilder # Import the main builder class
from .item import (ManifestItem, HtmlContentItem, CssStyleItem, ImageItem,
                   NavigationItem, NcxItem, FontItem, JavaScriptItem) # Import item types
from .metadata import MetadataManager
from . import constants
from .exceptions import EpubParseError, ItemNotFoundError
from .utils import get_relative_path, sanitize_href

# XML parser that recovers from errors and removes comments/processing instructions
PARSER = etree.XMLParser(recover=True, remove_comments=True, remove_pis=True)

def load_epub(epub_path: str) -> EpubBuilder:
    """
    Loads an existing EPUB file and parses its structure.

    Args:
        epub_path: Path to the .epub file.

    Returns:
        An EpubBuilder instance populated with the EPUB's content and metadata.

    Raises:
        FileNotFoundError: If the epub_path does not exist.
        EpubParseError: If the EPUB structure is invalid or parsing fails.
    """
    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")

    builder = EpubBuilder() # Create a new builder instance to populate
    opf_path = None
    opf_dir = ""
    items_by_href = {} # Helper map: { 'OEBPS/chapter1.xhtml': ManifestItem }

    try:
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            # 1. Check mimetype
            try:
                mimetype = epub_zip.read('mimetype').decode('ascii').strip()
                if mimetype != constants.MEDIA_TYPE_EPUB:
                    # Tolerate XHTML mimetype for very old/broken EPUBs? Maybe not.
                    raise EpubParseError(f"Invalid mimetype: expected '{constants.MEDIA_TYPE_EPUB}', found '{mimetype}'")
            except KeyError:
                raise EpubParseError("Mimetype file missing.")
            except Exception as e:
                 raise EpubParseError(f"Error reading mimetype: {e}")

            # 2. Find OPF path from container.xml
            try:
                container_content = epub_zip.read('META-INF/container.xml')
                container_root = etree.fromstring(container_content, parser=PARSER)
                # Use XPath with namespaces to find the rootfile element
                opf_element = container_root.find('.//container:rootfile[@media-type="%s"]' % constants.MEDIA_TYPE_OPF,
                                                 namespaces={'container': constants.NSMAP['container']})
                if opf_element is None or 'full-path' not in opf_element.attrib:
                    raise EpubParseError("Could not find valid rootfile entry in container.xml")
                opf_path = opf_element.attrib['full-path']
                # Determine the directory containing the OPF file (relative to zip root)
                opf_dir = os.path.dirname(opf_path).replace("\\", "/")
                builder.opf_file_name = os.path.basename(opf_path)
                builder.oebps_dir = opf_dir # Assume OPF dir is the main content dir

            except KeyError:
                raise EpubParseError("META-INF/container.xml missing.")
            except etree.XMLSyntaxError as e:
                 raise EpubParseError(f"Error parsing container.xml: {e}")
            except Exception as e:
                 raise EpubParseError(f"Error processing container.xml: {e}")

            if not opf_path:
                 raise EpubParseError("OPF file path could not be determined.")

            # 3. Parse OPF file
            try:
                opf_content = epub_zip.read(opf_path)
                opf_root = etree.fromstring(opf_content, parser=PARSER)

                # 3a. Parse Metadata
                metadata_node = opf_root.find('.//opf:metadata', namespaces=constants.NSMAP)
                if metadata_node is None:
                    raise EpubParseError("OPF file missing required <metadata> section.")
                parse_metadata(metadata_node, builder.metadata)

                # Set the unique ID ref on the builder
                builder._book_id_ref = opf_root.get('unique-identifier')
                if not builder._book_id_ref:
                     raise EpubParseError("OPF <package> missing required 'unique-identifier' attribute.")
                # Ensure the metadata manager also knows the ref (if not set via attributes)
                if not builder.metadata.get_unique_identifier_ref():
                    builder.metadata._unique_id_ref = builder._book_id_ref


                # 3b. Parse Manifest
                manifest_node = opf_root.find('.//opf:manifest', namespaces=constants.NSMAP)
                if manifest_node is None:
                    raise EpubParseError("OPF file missing required <manifest> section.")
                parse_manifest(manifest_node, epub_zip, opf_dir, builder, items_by_href)


                # 3c. Parse Spine
                spine_node = opf_root.find('.//opf:spine', namespaces=constants.NSMAP)
                if spine_node is None:
                     raise EpubParseError("OPF file missing required <spine> section.")
                parse_spine(spine_node, builder)
                builder._ncx_id = spine_node.get('toc') # Get NCX reference if present

            except KeyError:
                raise EpubParseError(f"OPF file '{opf_path}' not found in archive.")
            except etree.XMLSyntaxError as e:
                 raise EpubParseError(f"Error parsing OPF file '{opf_path}': {e}")
            except Exception as e:
                 raise EpubParseError(f"Error processing OPF file '{opf_path}': {e}")


            # 4. Find and Parse Navigation Document (if specified in manifest)
            nav_item = builder.get_item_by_property(constants.PROPERTY_NAV)
            if nav_item:
                 try:
                     nav_content = nav_item.content # Content was loaded during manifest parse
                     nav_root = etree.fromstring(nav_content, parser=etree.HTMLParser(encoding='utf-8')) # Use HTML parser for nav
                     parse_navigation_toc(nav_root, builder)
                     parse_navigation_landmarks(nav_root, builder)
                     # Ensure the NavigationItem instance in the builder has the parsed content
                     nav_instance = builder.get_item(nav_item.id)
                     if nav_instance and isinstance(nav_instance, NavigationItem):
                          nav_instance.content = nav_content # Update content just in case

                 except etree.XMLSyntaxError as e:
                      print(f"Warning: Could not parse Navigation Document ({nav_item.href}): {e}. TOC/Landmarks may be incomplete.")
                 except Exception as e:
                      print(f"Warning: Error processing Navigation Document ({nav_item.href}): {e}")
            else:
                 print("Warning: No EPUB 3 Navigation Document found in manifest (missing item with property='nav').")
                 # Optionally: Try to parse NCX if present for basic TOC
                 if builder._ncx_id:
                     ncx_item = builder.get_item(builder._ncx_id)
                     if ncx_item and isinstance(ncx_item, NcxItem):
                         try:
                             print(f"Attempting to parse NCX for TOC: {ncx_item.href}")
                             ncx_root = etree.fromstring(ncx_item.content, parser=PARSER)
                             parse_ncx_toc(ncx_root, builder, opf_dir) # Pass opf_dir for relative paths
                         except Exception as e:
                             print(f"Warning: Could not parse NCX file ({ncx_item.href}): {e}")
                     else:
                          print(f"Warning: Spine references TOC item '{builder._ncx_id}' but item not found or not NCX type in manifest.")


    except zipfile.BadZipFile:
        raise EpubParseError(f"File is not a valid ZIP archive: {epub_path}")
    except Exception as e:
        # Catch any other unexpected errors during loading
        raise EpubParseError(f"Failed to load EPUB '{epub_path}': {e}")

    return builder


def parse_metadata(metadata_node: etree._Element, manager: MetadataManager):
    """Parses the <metadata> node and populates the MetadataManager."""
    # Iterate through all direct children of the metadata node
    for element in metadata_node:
        # Use lxml's QName helper to easily get URI and localname
        qname = etree.QName(element.tag)
        ns_uri = qname.namespace
        local_name = qname.localname
        text = element.text.strip() if element.text else None

        # Convert lxml attribute dict ({QName(...)}: value) to simple {name: value}
        # Handle potential qualified names like opf:scheme correctly
        attrs = {}
        for k, v in element.attrib.items():
             # Check if key is a QName object (lxml does this for namespaced attrs)
             if isinstance(k, etree.QName):
                  # Find a known prefix for the namespace, otherwise use {uri}local
                  prefix = next((p for p, u in constants.NSMAP.items() if u == k.namespace), None)
                  attr_name = f"{prefix}:{k.localname}" if prefix else f"{{{k.namespace}}}{k.localname}"
                  attrs[attr_name] = v
             else: # Unnamespaced attribute
                  attrs[str(k)] = v


        # Add to manager based on type (could refine this logic)
        if ns_uri == constants.NSMAP['dc']:
            manager.add_dc(f"dc:{local_name}", text or '', attrs) # Ensure text is not None
        elif ns_uri == constants.NSMAP['opf'] and local_name == 'meta':
            prop = attrs.get('property')
            refines = attrs.get('refines')
            meta_id = attrs.get('id')
            scheme = attrs.get('scheme')
            # Need to reconstruct the arguments for add_meta
            manager.add_meta(property_attr=prop or '', value=text or '', refines=refines, meta_id=meta_id, scheme=scheme)
            # Special handling for dcterms:modified? Already handled by add_meta
        elif ns_uri == constants.NSMAP['opf'] and local_name == 'link':
            href = attrs.get('href')
            rel = attrs.get('rel')
            link_id = attrs.get('id')
            media_type = attrs.get('media-type')
            if href and rel:
                 manager.add_link(href=href, rel=rel, link_id=link_id, media_type=media_type)
        else:
            # Store unknown/other metadata elements?
            # print(f"Debug: Storing generic metadata element: {ns_uri} {local_name} {text} {attrs}")
            manager._elements.append((ns_uri, local_name, text, attrs)) # Store raw tuple

        # Check if this element is the unique identifier and store its ID ref
        if ns_uri == constants.NSMAP['dc'] and local_name == 'identifier':
            id_attr = attrs.get('id')
            if id_attr and id_attr == manager.get_unique_identifier_ref(): # Check against package unique-id ref
                 pass # Already set via package attribute


def parse_manifest(manifest_node: etree._Element, epub_zip: zipfile.ZipFile, opf_dir: str, builder: EpubBuilder, items_by_href: dict):
    """Parses the <manifest> node, reads item content, and adds items to the builder."""
    zip_infolist = {info.filename.replace("\\", "/"): info for info in epub_zip.infolist()}

    for item_el in manifest_node.findall('.//opf:item', namespaces=constants.NSMAP):
        item_id = item_el.get('id')
        href = item_el.get('href')
        media_type = item_el.get('media-type')
        properties = item_el.get('properties', '').split()

        if not all([item_id, href, media_type]):
            print(f"Warning: Skipping manifest item with missing id, href, or media-type: {etree.tostring(item_el)}")
            continue

        # Construct the full path within the zip archive relative to the root
        # Href is relative to the OPF file. Need path relative to zip root.
        full_zip_path = os.path.join(opf_dir, href).replace("\\", "/")
        # Normalize path (resolve . and ..) - though .. should ideally not be used in hrefs
        full_zip_path = os.path.normpath(full_zip_path).replace("\\", "/")


        try:
            # Read content directly from zip - crucial to read here!
            # Need to handle potential encoding issues if reading as text later
            item_content = epub_zip.read(full_zip_path)

        except KeyError:
            # Try case-insensitive matching as fallback for broken EPUBs
            found_path = None
            href_lower = full_zip_path.lower()
            for zip_path_key in zip_infolist.keys():
                if zip_path_key.lower() == href_lower:
                    found_path = zip_path_key
                    break
            if found_path:
                 print(f"Warning: Case mismatch for manifest item '{href}'. Found '{found_path}'. Reading content.")
                 item_content = epub_zip.read(found_path)
            else:
                 print(f"Warning: Manifest item '{href}' (path: '{full_zip_path}') not found in EPUB archive. Skipping item '{item_id}'.")
                 continue # Skip this item if content not found
        except Exception as e:
            print(f"Warning: Error reading content for manifest item '{href}' (path: '{full_zip_path}'): {e}. Skipping item '{item_id}'.")
            continue

        # Determine item type based on media type or properties
        # Note: file_name for item should be relative to OEBPS/content dir (which we assume is opf_dir)
        item_file_name = href # Keep the original href as the file_name relative to OPF dir

        item = None
        if constants.PROPERTY_NAV in properties:
            item = NavigationItem(item_id=item_id, file_name=item_file_name, content=item_content)
        elif media_type == constants.MEDIA_TYPE_NCX:
            item = NcxItem(item_id=item_id, file_name=item_file_name, content=item_content)
        elif media_type == constants.MEDIA_TYPE_XHTML:
             item = HtmlContentItem(item_id=item_id, file_name=item_file_name, content=item_content)
             # Try to extract title from HTML? Might be slow. Do later if needed.
        elif media_type == constants.MEDIA_TYPE_CSS:
            item = CssStyleItem(item_id=item_id, file_name=item_file_name, content=item_content)
        elif media_type.startswith('image/'):
             item = ImageItem(item_id=item_id, file_name=item_file_name, content=item_content, media_type=media_type)
        elif media_type.startswith(('application/font', 'application/vnd.ms-opentype', 'font/')):
             item = FontItem(item_id=item_id, file_name=item_file_name, content=item_content, media_type=media_type)
        elif media_type == constants.MEDIA_TYPE_JAVASCRIPT:
             item = JavaScriptItem(item_id=item_id, file_name=item_file_name, content=item_content)
        else:
            # Default fallback
            item = ManifestItem(item_id=item_id, file_name=item_file_name, media_type=media_type, content=item_content)

        # Assign properties
        item.properties.update(properties)
        # Set spine candidacy based on type (rough guess)
        if isinstance(item, (HtmlContentItem)) and constants.PROPERTY_NAV not in properties:
             item.is_spine_candidate = True


        # Register the item with the builder
        try:
            builder.register_item(item, overwrite=True) # Allow overwrite during load
            items_by_href[item.full_path_in_zip] = item # Map full zip path to item
        except Exception as e:
            print(f"Warning: Failed to register item '{item_id}': {e}")


def parse_spine(spine_node: etree._Element, builder: EpubBuilder):
    """Parses the <spine> node and populates the builder's spine."""
    builder._spine_item_refs = [] # Clear any default spine
    for itemref_el in spine_node.findall('.//opf:itemref', namespaces=constants.NSMAP):
        idref = itemref_el.get('idref')
        linear_attr = itemref_el.get('linear', 'yes') # Default is 'yes'
        is_linear = linear_attr.lower() != 'no'

        if not idref:
            print("Warning: Skipping spine itemref with missing idref.")
            continue

        # Check if the item exists in the manifest
        if idref not in builder._manifest_items:
            print(f"Warning: Spine references item '{idref}', which is not found in the manifest. Skipping.")
            continue

        builder.add_spine_item(idref, is_linear)


def parse_navigation_toc(nav_root: etree._Element, builder: EpubBuilder):
    """Parses the TOC <nav> element in the Navigation Document."""
    # Find the <nav> element with epub:type="toc"
    toc_nav = nav_root.find('.//xhtml:nav[@epub:type="%s"]' % constants.LANDMARK_TOC, namespaces=constants.NSMAP)
    if toc_nav is None:
        print("Warning: No <nav epub:type='toc'> found in Navigation Document.")
        return

    # Find the main <ol> within the TOC nav
    toc_ol = toc_nav.find('./xhtml:ol', namespaces=constants.NSMAP)
    if toc_ol is None:
         print("Warning: No <ol> found inside <nav epub:type='toc'>.")
         return

    nav_item_href = builder.get_item_by_property(constants.PROPERTY_NAV).href

    def extract_toc_entries(parent_ol) -> list[dict]:
        entries = []
        # Iterate over direct children 'li' elements
        for li in parent_ol.xpath('./xhtml:li', namespaces=constants.NSMAP):
             # Find the first 'a' element directly under 'li' or nested in 'span' etc.
             a_tag = li.find('.//xhtml:a[@href]', namespaces=constants.NSMAP)
             if a_tag is not None:
                 label = "".join(a_tag.itertext()).strip() or "Untitled"
                 href = a_tag.get('href', '')

                 # Resolve relative hrefs against the NAV doc itself
                 # Href should be relative to OPF dir for internal use
                 full_target_path = os.path.normpath(os.path.join(os.path.dirname(nav_item_href), href)).replace("\\", "/")
                 # Make it relative to the builder's oebps_dir
                 href_relative_to_oebps = os.path.relpath(full_target_path, ".").replace("\\","/") # Assuming opf_dir is '.' relative to itself


                 entry = {'label': label, 'href': href_relative_to_oebps, 'children': []}

                 # Check for nested <ol> for children
                 nested_ol = li.find('./xhtml:ol', namespaces=constants.NSMAP)
                 if nested_ol is not None:
                     entry['children'] = extract_toc_entries(nested_ol)
                 entries.append(entry)
        return entries

    builder._toc_entries = extract_toc_entries(toc_ol)

def parse_navigation_landmarks(nav_root: etree._Element, builder: EpubBuilder):
    """Parses the Landmarks <nav> element in the Navigation Document."""
    landmarks_nav = nav_root.find('.//xhtml:nav[@epub:type="landmarks"]', namespaces=constants.NSMAP)
    if landmarks_nav is None:
        return # Landmarks are optional

    landmarks_ol = landmarks_nav.find('./xhtml:ol', namespaces=constants.NSMAP)
    if landmarks_ol is None:
        return

    nav_item_href = builder.get_item_by_property(constants.PROPERTY_NAV).href

    landmarks_list = []
    for li in landmarks_ol.xpath('./xhtml:li', namespaces=constants.NSMAP):
         a_tag = li.find('.//xhtml:a[@href]', namespaces=constants.NSMAP)
         if a_tag is not None:
             label = "".join(a_tag.itertext()).strip() or "Unnamed Landmark"
             href = a_tag.get('href', '')
             landmark_type = a_tag.get(etree.QName(constants.NSMAP['epub'], 'type'), '') # Get epub:type attribute

             # Resolve href relative to NAV doc -> relative to OEBPS dir
             full_target_path = os.path.normpath(os.path.join(os.path.dirname(nav_item_href), href)).replace("\\", "/")
             href_relative_to_oebps = os.path.relpath(full_target_path, ".").replace("\\","/")

             if landmark_type: # Only add if type is specified
                  landmarks_list.append({'label': label, 'href': href_relative_to_oebps, 'type': landmark_type})

    builder._landmarks = landmarks_list


def parse_ncx_toc(ncx_root: etree._Element, builder: EpubBuilder, opf_dir: str):
    """Parses the NCX navMap and populates the builder's TOC if NavDoc TOC is empty."""
    if builder._toc_entries:
        print("Info: EPUB3 Navigation Document TOC already parsed. Skipping NCX TOC.")
        return # Prefer EPUB 3 Nav Doc

    nav_map = ncx_root.find('.//ncx:navMap', namespaces={'ncx': constants.NSMAP['opf']}) # Adjust namespace URI if needed for NCX
    if nav_map is None:
        print("Warning: NCX file missing navMap.")
        return

    def extract_ncx_entries(parent_navpoint) -> list[dict]:
        entries = []
        # Find direct child navPoint elements
        for np in parent_navpoint.xpath('./ncx:navPoint', namespaces={'ncx': constants.NSMAP['opf']}): # Adjust NS
             label_text = np.xpath('.//ncx:navLabel/ncx:text/text()', namespaces={'ncx': constants.NSMAP['opf']}) # Adjust NS
             label = label_text[0].strip() if label_text else "Untitled"

             content_tag = np.find('.//ncx:content', namespaces={'ncx': constants.NSMAP['opf']}) # Adjust NS
             if content_tag is not None:
                 src = content_tag.get('src', '')
                 if src:
                      # NCX src is relative to the NCX file itself (usually). Need path relative to OPF dir.
                      # Find NCX item href first
                      ncx_item = builder.get_item(builder._ncx_id)
                      if ncx_item:
                           full_target_path = os.path.normpath(os.path.join(os.path.dirname(ncx_item.href), src)).replace("\\", "/")
                           href_relative_to_oebps = os.path.relpath(full_target_path, ".").replace("\\","/")
                      else: # Fallback if NCX item somehow missing?
                           href_relative_to_oebps = sanitize_href(src)


                      entry = {'label': label, 'href': href_relative_to_oebps, 'children': []}
                      # Recursive call for nested navPoints
                      entry['children'] = extract_ncx_entries(np)
                      entries.append(entry)
        return entries

    builder._toc_entries = extract_ncx_entries(nav_map)
    if builder._toc_entries:
        print("Info: Populated TOC from NCX file.")