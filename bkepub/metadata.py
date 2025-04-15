# bkepub/metadata.py
from collections import defaultdict
from . import constants
from . import utils
from .exceptions import InvalidArgumentError, MissingMetadataError

class MetadataManager:
    """
    Manages EPUB metadata (DC, DCTerms, meta, link elements).
    """
    def __init__(self):
        # Stores metadata as tuples: (ns_uri, tag, text, attrs_dict)
        self._elements = []
        # Stores the ID attribute value of the dc:identifier designated as the unique identifier
        self._unique_id_ref = None
        # Keep track of added element IDs to prevent duplicates
        self._element_ids = set()
        # Keep track of unique identifier value to avoid duplicates
        self._unique_identifier_value = None

    def _add_element(self, ns_uri: str, tag: str, text: str | None, attrs: dict) -> str | None:
        """Internal helper to add elements, handling potential IDs."""
        element_id = attrs.get('id')
        if element_id:
            if element_id in self._element_ids:
                # Allow refinement metas to share IDs implicitly through refines
                if not (tag == 'meta' and attrs.get('refines')):
                    # Simple approach: skip adding duplicate ID. Could also raise error.
                    print(f"Warning: Duplicate metadata element ID '{element_id}'. Skipping.")
                    return None
            self._element_ids.add(element_id)

        # Add the element to the list
        self._elements.append((ns_uri, tag, text, attrs))
        return element_id # Return the ID if it was added

    def add_dc(self, qualified_tag: str, value: str, attributes: dict | None = None):
        """
        Adds a Dublin Core (DC) metadata element.

        Args:
            qualified_tag: The tag name including prefix (e.g., 'dc:title', 'dc:creator').
            value: The text content of the element.
            attributes: Optional dictionary of attributes for the element (e.g., {'id': 'pub-id', 'xml:lang': 'en'}).
        """
        if not qualified_tag.startswith('dc:'):
            raise InvalidArgumentError("DC tag must start with 'dc:' prefix.")
        if value is None: # Ensure value is at least an empty string
             value = ''

        prefix, tag = qualified_tag.split(':', 1)
        ns_uri = constants.NSMAP.get(prefix)
        if not ns_uri:
            raise InvalidArgumentError(f"Unknown namespace prefix: {prefix}")

        attrs = attributes or {}
        self._add_element(ns_uri, tag, value, attrs)

    def add_meta(self, property_attr: str, value: str, refines: str | None = None,
                 meta_id: str | None = None, scheme: str | None = None, **other_attrs):
        """
        Adds a generic <meta> element, typically used for EPUB 3 properties.

        Args:
            property_attr: The value for the 'property' attribute (e.g., 'dcterms:modified', 'role').
            value: The text content of the meta element.
            refines: Optional ID reference (prefixed with #) for refining another element.
            meta_id: Optional 'id' attribute for this meta element.
            scheme: Optional 'scheme' attribute (e.g., 'marc:relators').
            other_attrs: Additional attributes for the meta element.
        """
        if not property_attr:
            raise InvalidArgumentError("Meta element requires a 'property' attribute.")
        if value is None: value = ''

        ns_uri = constants.NSMAP['opf'] # Meta tags live in the OPF namespace usually
        tag = 'meta'
        attrs = {'property': property_attr}
        if meta_id:
            attrs['id'] = meta_id
        if refines:
            attrs['refines'] = refines if refines.startswith('#') else f"#{refines}"
        if scheme:
            attrs['scheme'] = scheme
        attrs.update(other_attrs)

        # Handle dcterms:modified automatically
        if property_attr == f"{{{constants.NSMAP['dcterms']}}}modified" or property_attr == "dcterms:modified":
            # Find and remove existing dcterms:modified meta tags by property
            self._elements = [
                el for el in self._elements
                if not (el[1] == 'meta' and el[3].get('property') == property_attr)
            ]
            # Add the new one (value should ideally be pre-formatted)
            self._add_element(ns_uri, tag, value, attrs)
        else:
            self._add_element(ns_uri, tag, value, attrs)


    def add_link(self, href: str, rel: str, link_id: str | None = None, media_type: str | None = None):
        """Adds a <link> element to the metadata (e.g., for record links)."""
        if not href or not rel:
             raise InvalidArgumentError("Link element requires 'href' and 'rel' attributes.")

        ns_uri = constants.NSMAP['opf'] # Link tags also in OPF namespace
        tag = 'link'
        attrs = {'href': href, 'rel': rel}
        if link_id:
            attrs['id'] = link_id
        if media_type:
            attrs['media-type'] = media_type

        self._add_element(ns_uri, tag, None, attrs) # Link elements have no text content


    def set_unique_identifier(self, value: str, identifier_id: str = "book-id"):
        """
        Sets the primary unique identifier (dc:identifier).
        This identifier MUST have an 'id' attribute matching the package's unique-identifier.

        Args:
            value: The identifier string (e.g., UUID, ISBN).
            identifier_id: The XML ID to assign to this dc:identifier element.
                           This ID will be used as the package's unique-identifier reference.
        """
        if not value:
            raise InvalidArgumentError("Unique identifier value cannot be empty.")
        if self._unique_identifier_value and self._unique_identifier_value != value:
             print(f"Warning: Changing unique identifier from '{self._unique_identifier_value}' to '{value}'.")
        if self._unique_id_ref and self._unique_id_ref != identifier_id:
             print(f"Warning: Changing unique identifier reference ID from '{self._unique_id_ref}' to '{identifier_id}'.")


        # Remove any existing dc:identifier with the *same ID*
        self._elements = [el for el in self._elements if not (el[0] == constants.NSMAP['dc'] and el[1] == 'identifier' and el[3].get('id') == identifier_id)]
        self._element_ids.discard(identifier_id) # Remove from tracked IDs

        # Add the new dc:identifier with the specified ID
        attrs = {'id': identifier_id}
        self.add_dc('dc:identifier', value, attributes=attrs)

        # Store the reference ID and value
        self._unique_id_ref = identifier_id
        self._unique_identifier_value = value

    def set_title(self, value: str, title_id: str | None = None, title_type: str = "main"):
        """
        Sets the primary dc:title. Removes previous main titles.

        Args:
             value: The book title.
             title_id: Optional ID for the title element.
             title_type: Type of title (e.g., 'main', 'subtitle'). Used for refinement if needed.
        """
        if not value: raise InvalidArgumentError("Title cannot be empty.")

        # Simple approach: remove all existing main dc:title elements before adding new one
        # A more complex approach would use title-type meta property
        if title_type == "main":
            self._elements = [el for el in self._elements if not (el[0] == constants.NSMAP['dc'] and el[1] == 'title')] # Simplistic removal
            attrs = {'id': title_id} if title_id else {}
            self.add_dc('dc:title', value, attributes=attrs)
        else:
            # Handle subtitles etc. potentially using meta refinement later
            attrs = {'id': title_id} if title_id else {}
            self.add_dc('dc:title', value, attributes=attrs)


    def set_language(self, value: str):
        """Sets the primary dc:language. Removes previous languages."""
        if not value: raise InvalidArgumentError("Language cannot be empty.")
        # Remove existing dc:language elements
        self._elements = [el for el in self._elements if not (el[0] == constants.NSMAP['dc'] and el[1] == 'language')]
        self.add_dc('dc:language', value)

    def add_creator(self, name: str, role: str | None = None, file_as: str | None = None, creator_id: str | None = None):
        """
        Adds a dc:creator and optionally associated role/file-as metadata.

        Args:
            name: Name of the creator.
            role: Role code (e.g., constants.ROLE_AUTHOR, 'edt').
            file_as: Sorting name (e.g., "Author, Awesome").
            creator_id: Optional explicit ID for the dc:creator element. If None, generated.
        """
        if not name: raise InvalidArgumentError("Creator name cannot be empty.")

        # Generate ID if needed
        current_id = creator_id or utils.generate_unique_id(prefix="creator")

        # Add dc:creator element
        self.add_dc('dc:creator', name, attributes={'id': current_id})

        # Add refinement meta for role if provided
        if role:
            self.add_meta(
                property_attr="role",
                value=role,
                refines=f"#{current_id}",
                scheme=constants.MARC_RELATORS_SCHEME
            )

        # Add refinement meta for file-as if provided
        if file_as:
             self.add_meta(
                 property_attr="file-as",
                 value=file_as,
                 refines=f"#{current_id}"
             )

    def find_dc(self, qualified_tag: str, attribute_filter: dict | None = None) -> str | None:
         """Finds the first matching DC element's text value."""
         prefix, tag = qualified_tag.split(':', 1)
         ns_uri = constants.NSMAP.get(prefix)
         if not ns_uri: return None

         for el_ns, el_tag, el_text, el_attrs in self._elements:
             if el_ns == ns_uri and el_tag == tag:
                 if attribute_filter:
                     match = all(el_attrs.get(k) == v for k, v in attribute_filter.items())
                     if not match: continue
                 return el_text
         return None

    def find_all_dc(self, qualified_tag: str) -> list[tuple[str | None, dict]]:
        """Finds all matching DC elements, returning (text, attributes) tuples."""
        prefix, tag = qualified_tag.split(':', 1)
        ns_uri = constants.NSMAP.get(prefix)
        if not ns_uri: return []

        results = []
        for el_ns, el_tag, el_text, el_attrs in self._elements:
            if el_ns == ns_uri and el_tag == tag:
                results.append((el_text, el_attrs))
        return results

    def get_metadata_elements(self) -> list[tuple]:
        """Returns the list of metadata elements for OPF generation."""
        # Ensure dcterms:modified is present/updated before returning
        self._ensure_modified_date()
        return self._elements

    def get_unique_identifier_ref(self) -> str | None:
        """Gets the ID reference for the unique identifier."""
        if not self._unique_id_ref:
             # Try to find it if not explicitly set (e.g., during load)
             for ns, tag, text, attrs in self._elements:
                 if ns == constants.NSMAP['dc'] and tag == 'identifier' and attrs.get('id'):
                     # Simple guess: first identifier with an ID
                     self._unique_id_ref = attrs.get('id')
                     break
        return self._unique_id_ref

    def _ensure_modified_date(self):
        """Adds or updates the dcterms:modified meta tag."""
        mod_prop = f"dcterms:modified" # Use prefix for simplicity here
        # Check if already exists
        exists = any(el[1] == 'meta' and el[3].get('property') == mod_prop for el in self._elements)
        if not exists:
            # If it doesn't exist, add it.
             self.add_meta(property_attr=mod_prop, value=utils.get_formatted_date())
        else:
             # If it exists, update its value (handled by add_meta logic)
             self.add_meta(property_attr=mod_prop, value=utils.get_formatted_date())


    def validate_required(self):
        """Checks if required metadata elements are present."""
        found = {
            constants.DC_IDENTIFIER: False,
            constants.DC_TITLE: False,
            constants.DC_LANGUAGE: False,
        }
        unique_id_ref = self.get_unique_identifier_ref()
        found_unique_id_element = False

        if not unique_id_ref:
            raise MissingMetadataError("Package unique-identifier reference is not set.")

        for ns_uri, tag, text, attrs in self._elements:
            qname = f"{{{ns_uri}}}{tag}"
            if qname == constants.DC_IDENTIFIER:
                found[constants.DC_IDENTIFIER] = True
                # Check if the specific identifier referenced exists
                if attrs.get('id') == unique_id_ref:
                    found_unique_id_element = True
            elif qname == constants.DC_TITLE:
                 found[constants.DC_TITLE] = True
            elif qname == constants.DC_LANGUAGE:
                found[constants.DC_LANGUAGE] = True

        missing = [key.split('}')[-1] for key, is_found in found.items() if not is_found]
        if missing:
            raise MissingMetadataError(f"Missing required metadata elements: {', '.join(missing)}")

        if not found_unique_id_element:
            raise MissingMetadataError(f"The unique identifier element (dc:identifier) with id='{unique_id_ref}' was not found in metadata.")