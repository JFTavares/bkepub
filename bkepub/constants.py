# bkepub/constants.py
import datetime

# Namespaces (using common prefixes)
NSMAP = {
    'container': "urn:oasis:names:tc:opendocument:xmlns:container",
    'opf': "http://www.idpf.org/2007/opf",
    'dc': "http://purl.org/dc/elements/1.1/",
    'dcterms': "http://purl.org/dc/terms/",
    'xhtml': "http://www.w3.org/1999/xhtml",
    'epub': "http://www.idpf.org/2007/ops",
    'xml': "http://www.w3.org/XML/1998/namespace" # For xml:lang
}

# Subdirectory structure within OEBPS
SUBDIR_TEXT = "Text"
SUBDIR_STYLES = "Styles"
SUBDIR_IMAGES = "Images"
SUBDIR_FONTS = "Fonts"
SUBDIR_AUDIO = "Audio"
SUBDIR_VIDEO = "Video"
SUBDIR_MISC = "Misc"



# Media Types
MEDIA_TYPE_EPUB = 'application/epub+zip'
MEDIA_TYPE_XHTML = 'application/xhtml+xml'
MEDIA_TYPE_CSS = 'text/css'
MEDIA_TYPE_JPEG = 'image/jpeg'
MEDIA_TYPE_PNG = 'image/png'
MEDIA_TYPE_GIF = 'image/gif'
MEDIA_TYPE_SVG = 'image/svg+xml'
MEDIA_TYPE_OPF = 'application/oebps-package+xml'
MEDIA_TYPE_NCX = 'application/x-dtbncx+xml'
MEDIA_TYPE_OTF = 'application/vnd.ms-opentype'
MEDIA_TYPE_TTF = 'application/font-sfnt'
MEDIA_TYPE_WOFF = 'application/font-woff'
MEDIA_TYPE_WOFF2 = 'font/woff2'
MEDIA_TYPE_JAVASCRIPT = 'text/javascript' # Ou application/javascript


# Mapping of media types to appropriate subdirectories
MEDIA_TYPE_TO_SUBDIR = {
    MEDIA_TYPE_XHTML: SUBDIR_TEXT,
    MEDIA_TYPE_CSS: SUBDIR_STYLES,
    MEDIA_TYPE_JPEG: SUBDIR_IMAGES,
    MEDIA_TYPE_PNG: SUBDIR_IMAGES,
    MEDIA_TYPE_GIF: SUBDIR_IMAGES,
    MEDIA_TYPE_SVG: SUBDIR_IMAGES,
    MEDIA_TYPE_OTF: SUBDIR_FONTS,
    MEDIA_TYPE_TTF: SUBDIR_FONTS,
    MEDIA_TYPE_WOFF: SUBDIR_FONTS,
    MEDIA_TYPE_WOFF2: SUBDIR_FONTS,
    MEDIA_TYPE_JAVASCRIPT: SUBDIR_MISC,
    # Additional media types can be added here
}

# Audio/Video media types
MEDIA_TYPE_MP3 = 'audio/mpeg'
MEDIA_TYPE_MP4_AUDIO = 'audio/mp4'
MEDIA_TYPE_OGG_AUDIO = 'audio/ogg'
MEDIA_TYPE_MP4_VIDEO = 'video/mp4'
MEDIA_TYPE_WEBM = 'video/webm'

# Add audio/video mappings
MEDIA_TYPE_TO_SUBDIR.update({
    MEDIA_TYPE_MP3: SUBDIR_AUDIO,
    MEDIA_TYPE_MP4_AUDIO: SUBDIR_AUDIO,
    MEDIA_TYPE_OGG_AUDIO: SUBDIR_AUDIO,
    MEDIA_TYPE_MP4_VIDEO: SUBDIR_VIDEO,
    MEDIA_TYPE_WEBM: SUBDIR_VIDEO,
})

# Default values
DEFAULT_LANG = "pt-br"
DEFAULT_EPUB_VERSION = "3.0"
OPF_FILE_NAME = "content.opf"
NAV_FILE_NAME = "nav.xhtml"
TOC_NCX_FILE_NAME = "toc.ncx"
OEBPS_DIR_NAME = "OEBPS" # Common directory name for content within EPUB zip

# Metadata keys (Dublin Core simplified + common dcterms)
DC_IDENTIFIER = "{%s}identifier" % NSMAP['dc']
DC_TITLE = "{%s}title" % NSMAP['dc']
DC_LANGUAGE = "{%s}language" % NSMAP['dc']
DC_CREATOR = "{%s}creator" % NSMAP['dc']
DC_PUBLISHER = "{%s}publisher" % NSMAP['dc']
DC_DATE = "{%s}date" % NSMAP['dc'] # Publication date
DC_SUBJECT = "{%s}subject" % NSMAP['dc']
DC_DESCRIPTION = "{%s}description" % NSMAP['dc']
DC_RIGHTS = "{%s}rights" % NSMAP['dc']
DC_CONTRIBUTOR = "{%s}contributor" % NSMAP['dc']
# ... add others if needed

DCTERMS_MODIFIED = "{%s}modified" % NSMAP['dcterms']

# Required metadata elements for a valid EPUB 3 (using namespaced keys)
REQUIRED_METADATA = [DC_IDENTIFIER, DC_TITLE, DC_LANGUAGE]

# Default modification date format (ISO 8601 Zulu)
MODIFIED_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Common EPUB roles for creators/contributors
MARC_RELATORS_SCHEME = "marc:relators"
ROLE_AUTHOR = "aut"
ROLE_EDITOR = "edt"
ROLE_ILLUSTRATOR = "ill"
# ... add more roles: https://www.loc.gov/marc/relators/relaterm.html

# EPUB specific item properties
PROPERTY_NAV = 'nav'
PROPERTY_COVER_IMAGE = 'cover-image'
PROPERTY_SCRIPTED = 'scripted'
PROPERTY_MATHML = 'mathml'
PROPERTY_SVG = 'svg'
PROPERTY_REMOTE = 'remote-resources'

# Landmarks types
LANDMARK_TOC = 'toc'
LANDMARK_COVER = 'cover'
LANDMARK_BODMATTER = 'bodymatter'
LANDMARK_TITLEPAGE = 'titlepage'
# ... add more: https://w3c.github.io/epub-specs/epub33/structure/#sec-landmarks-nav-def