"""dict -> XML unparsing: a hand-rolled recursive writer."""

from __future__ import annotations

from typing import Any, Optional

from ._errors import InvalidRootValueError, InvalidXMLNameError, MultipleRootsError
from ._names import is_valid_xml_name


def _escape_text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr(value: str) -> str:
    value = (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return value.replace("\t", "&#9;").replace("\n", "&#10;").replace("\r", "&#13;")


def _check_name(name: Any, *, allow_empty: bool = False) -> str:
    if allow_empty and name == "":
        return name
    if not is_valid_xml_name(name):
        raise InvalidXMLNameError(f"{name!r} is not a valid XML element/attribute name")
    return name


def _check_comment_text(text: str) -> str:
    if "--" in text:
        raise ValueError("XML comment text cannot contain '--'")
    if text.endswith("-"):
        raise ValueError("XML comment text cannot end with '-'")
    return text


class _Writer:
    def __init__(
        self,
        *,
        attr_prefix: str,
        cdata_key: str,
        comment_key: str,
        short_empty_elements: bool,
        pretty: bool,
        indent,
        newl: str,
        expand_iter: Optional[str],
        encoding: str,
        bytes_errors: str,
        namespaces: Optional[dict],
        preprocessor,
    ):
        self.attr_prefix = attr_prefix
        self.cdata_key = cdata_key
        self.comment_key = comment_key
        self.short_empty_elements = short_empty_elements
        self.pretty = pretty
        self.indent_unit = " " * indent if isinstance(indent, int) else indent
        self.newl = newl
        self.expand_iter = expand_iter
        self.encoding = encoding
        self.bytes_errors = bytes_errors
        self.namespaces = namespaces or {}
        self.preprocessor = preprocessor

    def _indent(self, depth: int) -> str:
        return self.indent_unit * depth if self.pretty else ""

    def _nl(self) -> str:
        return self.newl if self.pretty else ""

    def _coerce(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, bytes):
            try:
                return value.decode(self.encoding, errors=self.bytes_errors)
            except LookupError as exc:
                raise ValueError(
                    f"Invalid bytes_errors handler: {self.bytes_errors}"
                ) from exc
        return str(value)

    def _resolve_name(self, name: str) -> str:
        if not self.namespaces or not isinstance(name, str) or ":" not in name:
            return name
        uri, local = name.rsplit(":", 1)
        try:
            prefix = self.namespaces[uri]
        except KeyError:
            return name
        return local if not prefix else f"{prefix}:{local}"

    def _preprocess(self, key, value):
        if self.preprocessor is None:
            return key, value
        return self.preprocessor(key, value)

    # -- body classification ----------------------------------------------------

    def _classify_body(self, body: dict):
        """Yield (kind, key, value) for each item, after preprocessing.

        kind is one of 'attr', 'text', 'comment', 'child'. Non-list
        iterables (generators, tuples) given as a 'child' value are
        materialized into plain lists here, so downstream code only ever
        sees list or non-list child values.
        """
        for raw_key, raw_val in body.items():
            result = self._preprocess(raw_key, raw_val)
            if result is None:
                continue
            key, val = result
            if isinstance(key, str) and key == self.cdata_key:
                yield ("text", key, val)
            elif isinstance(key, str) and key == self.comment_key:
                yield ("comment", key, val)
            elif (
                isinstance(key, str)
                and self.attr_prefix
                and key.startswith(self.attr_prefix)
                and key != self.attr_prefix
            ):
                yield ("attr", key[len(self.attr_prefix):], val)
            else:
                if (
                    not isinstance(val, (str, bytes, dict))
                    and not isinstance(val, list)
                    and hasattr(val, "__iter__")
                ):
                    val = list(val)
                yield ("child", key, val)

    # -- comments ----------------------------------------------------------------

    def _comment_texts(self, value) -> list:
        items = value if isinstance(value, list) else [value]
        texts = []
        for item in items:
            if item is None:
                continue
            text = self._coerce(item)
            if text == "":
                continue
            texts.append(_check_comment_text(text))
        return texts

    def _emit_comments(self, buf: list, value, depth: int) -> None:
        indent = self._indent(depth)
        for text in self._comment_texts(value):
            buf.append(f"{indent}<!--{text}-->{self._nl()}")

    # -- attributes ----------------------------------------------------------------

    def _render_attrs(self, attrs: list) -> str:
        parts = []
        for name, val in attrs:
            if name == "xmlns" and isinstance(val, dict):
                for prefix, uri in val.items():
                    _check_name(prefix, allow_empty=True)
                    rendered = "xmlns" if prefix == "" else f"xmlns:{prefix}"
                    parts.append(f' {rendered}="{_escape_attr(self._coerce(uri))}"')
                continue
            resolved = self._resolve_name(name)
            _check_name(resolved)
            parts.append(f' {resolved}="{_escape_attr(self._coerce(val))}"')
        return "".join(parts)

    # -- element emission ------------------------------------------------------

    @staticmethod
    def _child_would_emit(value) -> bool:
        if isinstance(value, list):
            return len(value) > 0
        return True

    def emit_element(self, buf: list, tag: str, value: Any, depth: int) -> None:
        resolved_tag = self._resolve_name(tag)
        _check_name(resolved_tag)
        indent = self._indent(depth)

        if value is None:
            self._emit_empty(buf, resolved_tag, "", indent)
            return

        if isinstance(value, dict):
            attrs = []
            text_value = None
            has_text_key = False
            body_items = []  # (kind, key, value) for comment/child, in order
            has_other_body = False

            for kind, key, val in self._classify_body(value):
                if kind == "attr":
                    attrs.append((key, val))
                elif kind == "text":
                    text_value = val
                    has_text_key = True
                elif kind == "comment":
                    if self._comment_texts(val):
                        has_other_body = True
                    body_items.append((kind, key, val))
                else:  # child
                    if self._child_would_emit(val):
                        has_other_body = True
                    body_items.append((kind, key, val))

            attr_str = self._render_attrs(attrs)
            text_present = has_text_key and text_value is not None

            if not has_other_body and not text_present:
                self._emit_empty(buf, resolved_tag, attr_str, indent)
                return

            if text_present and not has_other_body:
                buf.append(
                    f"{indent}<{resolved_tag}{attr_str}>"
                    f"{_escape_text(self._coerce(text_value))}</{resolved_tag}>{self._nl()}"
                )
                return

            buf.append(f"{indent}<{resolved_tag}{attr_str}>{self._nl()}")
            for kind, key, val in body_items:
                if kind == "comment":
                    self._emit_comments(buf, val, depth + 1)
                else:
                    self._emit_child(buf, key, val, depth + 1)
            if text_present:
                buf.append(
                    f"{self._indent(depth + 1)}{_escape_text(self._coerce(text_value))}{self._nl()}"
                )
            buf.append(f"{indent}</{resolved_tag}>{self._nl()}")
            return

        if isinstance(value, list):
            raise InvalidRootValueError(f"element {tag!r} cannot hold a list directly")

        buf.append(
            f"{indent}<{resolved_tag}>{_escape_text(self._coerce(value))}</{resolved_tag}>{self._nl()}"
        )

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
        resolved_key = self._resolve_name(key)
        _check_name(resolved_key)
        indent = self._indent(depth)
        if not self.expand_iter:
            buf.append(
                f"{indent}<{resolved_key}>{_escape_text(self._coerce(inner))}</{resolved_key}>{self._nl()}"
            )
            return
        buf.append(f"{indent}<{resolved_key}>{self._nl()}")
        for sub in inner:
            self.emit_element(buf, self.expand_iter, sub, depth + 1)
        buf.append(f"{indent}</{resolved_key}>{self._nl()}")


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
    comment_key: str = "#comment",
    pretty: bool = False,
    indent="\t",
    newl: str = "\n",
    expand_iter: Optional[str] = None,
    namespaces: Optional[dict] = None,
    preprocessor=None,
):
    """Convert a dict (as produced by :func:`parse`) back into XML text.

    When ``full_document`` is True (the default), ``input_dict`` must have
    exactly one top-level key (aside from any ``comment_key`` entry); its
    value becomes the document's root element. When ``full_document`` is
    False, every top-level entry (any number, including zero) is emitted
    as its own sibling, with no enclosing tag or XML declaration -- a
    list value at the top level then simply repeats that element, the
    same as it would for a nested child.

    Pass ``output`` (a file-like object) to stream the result instead of
    returning a string. ``preprocessor(key, value)`` is called for every
    key/value pair as it is encountered (attributes, ``cdata_key`` text,
    ``comment_key`` entries, and children alike); returning ``None`` drops
    that entry.
    """
    if not isinstance(input_dict, dict):
        raise MultipleRootsError(
            f"unparse() requires a dict, got {type(input_dict).__name__}"
        )

    writer = _Writer(
        attr_prefix=attr_prefix,
        cdata_key=cdata_key,
        comment_key=comment_key,
        short_empty_elements=short_empty_elements,
        pretty=pretty,
        indent=indent,
        newl=newl,
        expand_iter=expand_iter,
        encoding=encoding,
        bytes_errors=bytes_errors,
        namespaces=namespaces,
        preprocessor=preprocessor,
    )

    processed = []
    for raw_key, raw_val in input_dict.items():
        result = writer._preprocess(raw_key, raw_val)
        if result is None:
            continue
        processed.append(result)

    real_roots = [(k, v) for k, v in processed if k != comment_key]

    if full_document:
        if len(real_roots) != 1:
            raise MultipleRootsError(
                "unparse() requires exactly one root element when full_document=True, "
                f"got {len(real_roots)}"
            )
        _, root_value = real_roots[0]
        if isinstance(root_value, list):
            raise InvalidRootValueError(
                "the root value cannot be a list; XML documents have exactly one root element"
            )

    buf: list = []
    if full_document:
        # The declaration is always followed by a literal newline,
        # independent of pretty/newl.
        buf.append(f'<?xml version="1.0" encoding="{encoding}"?>\n')

    for key, val in processed:
        if key == comment_key:
            writer._emit_comments(buf, val, 0)
        else:
            writer._emit_child(buf, key, val, 0)

    text = "".join(buf)
    if pretty and newl and text.endswith(newl):
        text = text[: -len(newl)]

    if output is None:
        return text

    try:
        output.write(text)
    except TypeError:
        output.write(text.encode(encoding, errors=bytes_errors))
    return None
