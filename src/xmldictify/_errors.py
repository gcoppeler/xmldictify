"""Exception hierarchy for xmldictify."""

from __future__ import annotations


class XMLToDictError(Exception):
    """Base class for all errors raised by xmldictify."""


class XMLParseError(XMLToDictError):
    """The input could not be parsed as well-formed XML."""


class EntitiesForbidden(XMLParseError):
    """The document declared a DOCTYPE/entity while disable_entities=True."""


class MultipleRootsError(XMLToDictError, ValueError):
    """unparse() was given a dict without exactly one top-level key."""


class InvalidRootValueError(XMLToDictError, ValueError):
    """unparse() was given a root value that cannot be a single XML element."""


class InvalidXMLNameError(XMLToDictError, ValueError):
    """A dict key is not a valid XML element/attribute name."""
