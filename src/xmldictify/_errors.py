"""Exception hierarchy for xmldictify."""

from __future__ import annotations


class XMLToDictError(Exception):
    """Base class for all errors raised by xmldictify."""


class ParsingInterrupted(XMLToDictError):
    """Raised when a streaming item_callback returns False."""


class EntitiesForbidden(XMLToDictError, ValueError):
    """The document declared/used an entity while disable_entities=True."""


class MultipleRootsError(XMLToDictError, ValueError):
    """unparse() was given a dict without exactly one top-level key."""


class InvalidRootValueError(XMLToDictError, ValueError):
    """unparse() was given a root value that cannot be a single XML element."""


class InvalidXMLNameError(XMLToDictError, ValueError):
    """A dict key is not a valid XML element/attribute name."""
