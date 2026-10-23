"""dict -> XML unparsing: a hand-rolled recursive writer."""

from __future__ import annotations

from typing import Any, Optional

from ._errors import InvalidRootValueError, InvalidXMLNameError, MultipleRootsError
from ._names import is_valid_xml_name


def _escape_text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr(value: str) -> str:
    value = value.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
    return (
        value.replace("\t", "&#9;")
        .replace("\n", "&#10;")
        .replace("\r", "&#13;")
    )


def _check_name(name: str) -> str:
    if not is_valid_xml_name(name):
        raise InvalidXMLNameError(f"{name!r} is not a valid XML element/attribute name")
    return name


class _Writer:
    def __init__(
        self,
        *,
        attr_prefix: str,
        cdata_key: str,
        short_empty_elements: bool,
        pretty: bool,
        indent,
        newl: str,
        expand_iter: Optional[str],
    ):
        self.attr_prefix = attr_prefix
        self.cdata_key = cdata_key
        self.short_empty_elements = short_empty_elements
        self.pretty = pretty
        self.indent_unit = " " * indent if isinstance(indent, int) else indent
        self.newl = newl
        self.expand_iter = expand_iter

    def _indent(self, depth: int) -> str:
        return self.indent_unit * depth if self.pretty else ""

    def _nl(self) -> str:
        return self.newl if self.pretty else ""

    # -- attribute/text splitting -------------------------------------------

    def _split(self, value: dict):
        attrs: list[tuple[str, Any]] = []
        children: list[tuple[str, Any]] = []
        text = None
        prefix = self.attr_prefix
        plen = len(prefix)
        for key, val in value.items():
            if prefix and key.startswith(prefix) and key != self.cdata_key:
                attrs.append((key[plen:], val))
            elif key == self.cdata_key:
                text = val
            else:
                children.append((key, val))
        return attrs, text, children

    def _attr_string(self, attrs) -> str:
        parts = []
        for name, val in attrs:
            _check_name(name)
            parts.append(f' {name}="{_escape_attr(str(val))}"')
        return "".join(parts)

    # -- element emission ------------------------------------------------------

    def emit_element(self, buf: list, tag: str, value: Any, depth: int) -> None:
        _check_name(tag)
        indent = self._indent(depth)

        if value is None:
            self._emit_empty(buf, tag, "", indent)
            return

        if isinstance(value, dict):
            attrs, text, children = self._split(value)
            attr_str = self._attr_string(attrs)

            if not children and text is None:
                self._emit_empty(buf, tag, attr_str, indent)
                return

            if text is not None and not children:
                buf.append(f"{indent}<{tag}{attr_str}>{_escape_text(str(text))}</{tag}>{self._nl()}")
                return

            buf.append(f"{indent}<{tag}{attr_str}>{self._nl()}")
            if text is not None:
                buf.append(f"{self._indent(depth + 1)}{_escape_text(str(text))}{self._nl()}")
            for key, val in children:
                self._emit_child(buf, key, val, depth + 1)
            buf.append(f"{indent}</{tag}>{self._nl()}")
            return

        if isinstance(value, list):
            # A bare list only reaches here for the document root, which is
            # rejected up front in unparse(); treat defensively anyway.
            raise InvalidRootValueError(f"element {tag!r} cannot hold a list directly")

        buf.append(f"{indent}<{tag}>{_escape_text(str(value))}</{tag}>{self._nl()}")

    def _emit_empty(self, buf: list, tag: str, attr_str: str, indent: str) -> None:
        if self.short_empty_elements:
            buf.append(f"{indent}<{tag}{attr_str}/>{self._nl()}")
        else:
            buf.append(f"{indent}<{tag}{attr_str}></{tag}>{self._nl()}")

    def _emit_child(self, buf: list, key: str, value: Any, depth: int) -> None:
        if not isinstance(value, list):
            self.emit_element(buf, key, value, depth)
            return

        if not value:
            return  # empty list -> no element emitted (use [''] to force one)

        for item in value:
            if isinstance(item, list):
                self._emit_nested_list(buf, key, item, depth)
            else:
                self.emit_element(buf, key, item, depth)

    def _emit_nested_list(self, buf: list, key: str, inner: list, depth: int) -> None:
        _check_name(key)
        indent = self._indent(depth)
        if not self.expand_iter:
            buf.append(f"{indent}<{key}>{_escape_text(str(inner))}</{key}>{self._nl()}")
            return
        buf.append(f"{indent}<{key}>{self._nl()}")
        for sub in inner:
            self.emit_element(buf, self.expand_iter, sub, depth + 1)
        buf.append(f"{indent}</{key}>{self._nl()}")


def unparse(
    input_dict: dict,
    output=None,
    *,
    encoding: str = "utf-8",
    bytes_errors: str = "replace",
    full_document: bool = True,
    short_empty_elements: bool = False,
    attr_prefix: str = "@",
    cdata_key: str = "#text",
    pretty: bool = False,
    indent="\t",
    newl: str = "\n",
    expand_iter: Optional[str] = None,
):
    """Convert a dict (as produced by :func:`parse`) back into XML text.

    ``input_dict`` must have exactly one top-level key; its value becomes
    the document's root element. Pass ``output`` (a file-like object) to
    stream the result instead of returning a string.
    """
    if not isinstance(input_dict, dict) or len(input_dict) != 1:
        raise MultipleRootsError(
            "unparse() requires a dict with exactly one top-level root key, "
            f"got {len(input_dict) if isinstance(input_dict, dict) else 'non-dict'}"
        )
    ((root_tag, root_value),) = input_dict.items()
    if isinstance(root_value, list):
        raise InvalidRootValueError(
            "the root value cannot be a list; XML documents have exactly one root element"
        )

    writer = _Writer(
        attr_prefix=attr_prefix,
        cdata_key=cdata_key,
        short_empty_elements=short_empty_elements,
        pretty=pretty,
        indent=indent,
        newl=newl,
        expand_iter=expand_iter,
    )

    buf: list[str] = []
    if full_document:
        buf.append(f'<?xml version="1.0" encoding="{encoding}"?>{writer._nl()}')
    writer.emit_element(buf, root_tag, root_value, depth=0)
    text = "".join(buf)

    if output is None:
        return text

    try:
        output.write(text)
    except TypeError:
        output.write(text.encode(encoding, errors=bytes_errors))
    return None
