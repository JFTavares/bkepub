# bkepub/item.py
import os
from pathlib import Path
from . import constants
from . import utils
from .exceptions import InvalidArgumentError


class ManifestItem:
    """Base class for items included in the EPUB manifest."""

    def __init__(self, item_id: str, file_name: str, media_type: str, content: bytes = b''):
        if not item_id:
            raise InvalidArgumentError("ManifestItem must have an item_id.")
        if not file_name:
            raise InvalidArgumentError("ManifestItem must have a file_name.")
        if not media_type:
            raise InvalidArgumentError("ManifestItem must have a media_type.")

        self.id = item_id
        # Store original file_name (before applying folder structure)
        self.original_file_name = utils.sanitize_href(file_name)
        # Store file_name relative to the OEBPS/content directory root
        self.file_name = self.original_file_name
        self.media_type = media_type
        self._content = utils.ensure_bytes(content)  # Always store content as bytes
        self.properties = set()  # EPUB 3 properties (e.g., 'nav', 'cover-image', 'scripted')
        self.is_spine_candidate = False  # Can this item typically go in the spine?
        self.is_linear = True  # For spine items: 'yes' (True) or 'no' (False)
        self.nav_title = None  # Title used for Navigation Document (TOC)

    def apply_folder_structure(self):
        """
        Applies the folder structure based on the media type.
        Should be called after the item is created if folder structure is enabled.
        """
        # Skip organization for NCX and OPF files - they should stay in the root
        if self.media_type == constants.MEDIA_TYPE_NCX or self.original_file_name.endswith(constants.OPF_FILE_NAME):
            self.file_name = self.original_file_name
            return

        # Get the appropriate subdirectory based on media type
        subdir = constants.MEDIA_TYPE_TO_SUBDIR.get(self.media_type, constants.SUBDIR_MISC)

        # Extract just the filename part
        base_name = os.path.basename(self.original_file_name)

        # Create the new path with subdirectory
        self.file_name = f"{subdir}/{base_name}"

    @property
    def content(self) -> bytes:
        """Gets the content of the item as bytes."""
        return self._content

    @content.setter
    def content(self, value: str | bytes):
        """Sets the content, ensuring it's stored as bytes."""
        self._content = utils.ensure_bytes(value)

    @property
    def href(self) -> str:
        """Returns the sanitized relative path for use in OPF/NAV."""
        # Ensure forward slashes for EPUB specification
        return self.file_name.replace("\\", "/")

    @property
    def full_path_in_zip(self) -> str:
        """Calculates the full path within the EPUB zip file (assuming standard OEBPS)."""
        # This might need adjustment if OEBPS directory name is configurable
        return f"{constants.OEBPS_DIR_NAME}/{self.href}".replace("\\", "/")

    def __repr__(self):
        props = f" properties={{{', '.join(sorted(self.properties))}}}" if self.properties else ""
        return f"<{self.__class__.__name__} id='{self.id}' href='{self.href}' media_type='{self.media_type}'{props}>"

class HtmlContentItem(ManifestItem):
    """Represents an XHTML content document."""

    def __init__(self, item_id: str, file_name: str, content: bytes, nav_title: str | None = None,
                 language: str | None = None):
        # Check if content is already a complete XHTML document
        content_str = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else content

        # If it doesn't start with XML declaration or DOCTYPE, wrap it
        if not content_str.strip().startswith(('<?xml', '<!DOCTYPE')):
            title = nav_title or Path(file_name).stem
            lang = language or constants.DEFAULT_LANG
            template = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="{constants.NSMAP['xhtml']}" xmlns:epub="{constants.NSMAP['epub']}">
<head>
  <title>{title}</title>
</head>
<body>
{content_str}
</body>
</html>"""
            content = template.encode('utf-8')

        super().__init__(item_id, file_name, constants.MEDIA_TYPE_XHTML, content)
        self.is_spine_candidate = True  # HTML usually goes in the spine
        self.nav_title = nav_title or Path(file_name).stem  # Use filename stem if no title provided
        self.language = language

class CssStyleItem(ManifestItem):
    """Represents a CSS stylesheet."""
    def __init__(self, item_id: str, file_name: str, content: bytes):
        super().__init__(item_id, file_name, constants.MEDIA_TYPE_CSS, content)

class ImageItem(ManifestItem):
    """Represents an image."""
    def __init__(self, item_id: str, file_name: str, content: bytes, media_type: str | None = None):
        guessed_media_type = media_type or utils.get_media_type(file_name)
        if not guessed_media_type.startswith('image/'):
            raise InvalidArgumentError(f"Invalid media type for image item: {guessed_media_type}")
        super().__init__(item_id, file_name, guessed_media_type, content)

    def set_as_cover(self):
        """Marks this image as the cover image."""
        self.properties.add(constants.PROPERTY_COVER_IMAGE)

class NavigationItem(HtmlContentItem):
    """Represents the EPUB 3 Navigation Document (nav.xhtml)."""
    def __init__(self, item_id: str = "nav", file_name: str = constants.NAV_FILE_NAME, content: bytes = b''):
        super().__init__(item_id, file_name, content, nav_title="Table of Contents") # Nav title usually fixed
        self.properties.add(constants.PROPERTY_NAV)
        self.is_spine_candidate = False # Nav doc usually not part of linear reading order


class NcxItem(ManifestItem):
    """Represents the NCX Table of Contents (for EPUB 2 compatibility)."""

    def __init__(self, item_id: str = "ncx", file_name: str = constants.TOC_NCX_FILE_NAME, content: bytes = b''):
        super().__init__(item_id, file_name, constants.MEDIA_TYPE_NCX, content)
        self.is_spine_candidate = False

    def apply_folder_structure(self):
        """Override to ensure NCX always stays in the root directory"""
        # NCX file must remain in the root of OEBPS
        self.file_name = os.path.basename(self.original_file_name)

class FontItem(ManifestItem):
    """Represents a font resource."""
    def __init__(self, item_id: str, file_name: str, content: bytes, media_type: str | None = None):
        guessed_media_type = media_type or utils.get_media_type(file_name)
        if not guessed_media_type.startswith(('application/', 'font/')): # Basic check
             raise InvalidArgumentError(f"Invalid media type for font item: {guessed_media_type}")
        super().__init__(item_id, file_name, guessed_media_type, content)

class JavaScriptItem(ManifestItem):
    """Represents a JavaScript file."""
    def __init__(self, item_id: str, file_name: str, content: bytes):
        super().__init__(item_id, file_name, constants.MEDIA_TYPE_JAVASCRIPT, content)
        self.properties.add(constants.PROPERTY_SCRIPTED) # Automatically add 'scripted' property


# Add other item types as needed (e.g., AudioItem, VideoItem)