"""Validation of strings as XML Names (element/attribute names).

This is a pragmatic approximation of the XML 1.0 Name production, not a
character-for-character implementation of the full Unicode NameStartChar /
NameChar grammar. It is deliberately conservative: it accepts the names
people actually use (letters, digits, '_', '-', '.', ':', and most non-ASCII
letters) and rejects anything that would produce unsafe or malformed XML
(leading digits/punctuation, whitespace, '<', '>', '&', '"', "'", '/', '=').
"""

from __future__ import annotations

import re

# NameStartChar: letter, underscore, or colon (colon is allowed here even
# though it is namespace syntax, since callers may legitimately emit
# pre-namespaced tag text themselves).
_NAME_START = r"[^\d\W]|[_:]"
_NAME_CHAR = r"[^\W]|[_:.\-]"

_NAME_RE = re.compile(rf"^(?:{_NAME_START})(?:{_NAME_CHAR})*$", re.UNICODE)


def is_valid_xml_name(name: str) -> bool:
    """Return True if `name` is safe to emit as an XML element/attribute name."""
    if not isinstance(name, str) or not name:
        return False
    return bool(_NAME_RE.match(name))
