"""xmldictify: convert XML to Python dicts and back again."""

from ._errors import (
    EntitiesForbidden,
    InvalidRootValueError,
    InvalidXMLNameError,
    MultipleRootsError,
    XMLParseError,
    XMLToDictError,
)
from ._parsing import parse
from ._unparsing import unparse

__version__ = "0.1.0"

__all__ = [
    "parse",
    "unparse",
    "XMLToDictError",
    "XMLParseError",
    "EntitiesForbidden",
    "MultipleRootsError",
    "InvalidRootValueError",
    "InvalidXMLNameError",
    "__version__",
]
