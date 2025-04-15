# bkepub/exceptions.py
class BkEpubError(Exception):
    """Base class for exceptions in the bkepub library."""
    pass

class ItemNotFoundError(BkEpubError):
    """Raised when an item ID is not found in the manifest."""
    pass

class DuplicateItemError(BkEpubError):
    """Raised when attempting to add an item with an existing ID."""
    pass

class MissingMetadataError(BkEpubError):
    """Raised when required metadata is missing during validation or saving."""
    pass

class InvalidArgumentError(BkEpubError):
    """Raised for invalid arguments to functions/methods."""
    pass

class EpubParseError(BkEpubError):
    """Raised when parsing an existing EPUB file fails."""
    pass

class EpubWriteError(BkEpubError):
    """Raised when writing the EPUB file fails."""
    pass