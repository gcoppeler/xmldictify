"""XML -> dict parsing, built directly on xml.parsers.expat.

Depth and path conventions (our own design, verified against the
documented/tested behavior of comparable libraries):

* The root element is depth 1; each nested level adds 1.
* ``path`` arguments are lists of ``(tag, attrs_or_None)`` tuples, where
  ``attrs_or_None`` is a plain dict of raw (unprefixed) attribute names to
  string values, or ``None`` if the element had no attributes.
* For ``force_list``/``force_cdata`` and the "attach this child to its
  parent" postprocessor call, ``path`` is the *container's own* chain
  (ancestors of the container, plus the container itself as the last
  entry) -- i.e. it does not include the child's own tag, since the
  child's tag is already passed separately as ``key``.
* For the per-attribute and per-text-key (``cdata_key``) postprocessor
  calls, and for ``item_callback``, ``path`` includes the current
  element's own tag as the last entry (it *is* the container for its own
  attributes/text, or the subject being reported).
"""

from __future__ import annotations

import xml.parsers.expat as _default_expat
from typing import Any, Callable, Iterable, Optional, Union

from ._errors import EntitiesForbidden, ParsingInterrupted

_CHUNK_SIZE = 64 * 1024

Predicate = Callable[[list, str, Any], bool]
PathKeyValue = Union[bool, Iterable[str], Predicate, None]


def _make_predicate(spec: PathKeyValue) -> Predicate:
    if spec is None or spec is False:
        return lambda path, key, value: False
    if spec is True:
        return lambda path, key, value: True
    if callable(spec):
        return spec
    names = frozenset(spec)
    return lambda path, key, value: key in names


class _Frame:
    __slots__ = ("tag", "path", "raw_attrs", "data", "text_parts")

    def __init__(self, tag: str, path: list, dict_constructor):
        self.tag = tag
        self.path = path
        self.raw_attrs: Optional[dict] = None
        self.data = dict_constructor()
        self.text_parts: list = []


class _SaxToDict:
    def __init__(
        self,
        *,
        xml_attribs: bool,
        attr_prefix: str,
        cdata_key: str,
        force_cdata: Predicate,
        cdata_separator: str,
        strip_whitespace: bool,
        process_comments: bool,
        comment_key: str,
        force_list: Predicate,
        item_depth: int,
        item_callback,
        postprocessor,
        dict_constructor,
        process_namespaces: bool,
        namespace_separator: str,
        namespaces: Optional[dict],
    ):
        self.xml_attribs = xml_attribs
        self.attr_prefix = attr_prefix
        self.cdata_key = cdata_key
        self.force_cdata = force_cdata
        self.cdata_separator = cdata_separator
        self.strip_whitespace = strip_whitespace
        self.process_comments = process_comments
        self.comment_key = comment_key
        self.force_list = force_list
        self.item_depth = item_depth
        self.item_callback = item_callback
        self.postprocessor = postprocessor
        self.dict_constructor = dict_constructor
        self.process_namespaces = process_namespaces
        self.namespace_separator = namespace_separator
        self.namespaces = namespaces if namespaces is not None else {}

        self.stack: list[_Frame] = []
        self.result = None
        self._pending_ns: dict = {}
        self._toplevel_comments: list = []

    # -- namespace resolution -------------------------------------------------

    def _resolve_name(self, raw_name: str) -> str:
        if not self.process_namespaces:
            return raw_name
        sep = self.namespace_separator
        if sep not in raw_name:
            return raw_name
        uri, local = raw_name.rsplit(sep, 1)
        try:
            prefix = self.namespaces[uri]
        except KeyError:
            return raw_name
        return local if not prefix else f"{prefix}:{local}"

    # -- postprocessor helper ---------------------------------------------------

    def _pp(self, path: list, key: str, value: Any):
        if self.postprocessor is None:
            return key, value
        return self.postprocessor(path, key, value)

    # -- list/child attachment -------------------------------------------------

    def _add_child(self, container, path: list, key: str, value: Any) -> None:
        if key in container:
            existing = container[key]
            if isinstance(existing, list):
                existing.append(value)
            else:
                container[key] = [existing, value]
        elif self.force_list(path, key, value):
            container[key] = [value]
        else:
            container[key] = value

    # -- expat handlers ---------------------------------------------------------

    def start_ns(self, prefix: Optional[str], uri: str) -> None:
        self._pending_ns[prefix or ""] = uri

    def start_element(self, raw_name: str, raw_attrs: dict) -> None:
        tag = self._resolve_name(raw_name)
        path = [(f.tag, f.raw_attrs) for f in self.stack]
        frame = _Frame(tag, path, self.dict_constructor)

        raw_attrs_dict = {}
        if self.xml_attribs:
            for raw_key, value in raw_attrs.items():
                raw_attrs_dict[self._resolve_name(raw_key)] = value
        frame.raw_attrs = raw_attrs_dict or None

        if self.xml_attribs and raw_attrs_dict:
            self_chain = path + [(tag, frame.raw_attrs)]
            for name, value in raw_attrs_dict.items():
                result = self._pp(self_chain, self.attr_prefix + name, value)
                if result is None:
                    continue
                key, value = result
                frame.data[key] = value

        if self._pending_ns:
            if self.xml_attribs:
                frame.data[self.attr_prefix + "xmlns"] = dict(self._pending_ns)
            self._pending_ns = {}

        self.stack.append(frame)

    def char_data(self, data: str) -> None:
        if self.stack:
            self.stack[-1].text_parts.append(data)

    def comment(self, data: str) -> None:
        if not self.process_comments:
            return
        text = data.strip() if self.strip_whitespace else data
        if not self.stack:
            self._toplevel_comments.append(text)
            return
        frame = self.stack[-1]
        self._add_child(frame.data, frame.path + [(frame.tag, frame.raw_attrs)], self.comment_key, text)

    def end_element(self, raw_name: str) -> None:
        frame = self.stack.pop()
        parent_chain = [(f.tag, f.raw_attrs) for f in self.stack]
        value = self._finalize(frame, parent_chain)

        result = self._pp(parent_chain, frame.tag, value)
        if result is None:
            return
        key, value = result

        if self.item_depth == 0:
            if self.stack:
                self._add_child(self.stack[-1].data, parent_chain, key, value)
            else:
                wrapped = self.dict_constructor()
                self._add_child(wrapped, parent_chain, key, value)
                self.result = wrapped
            return

        depth = len(self.stack) + 1
        if depth == self.item_depth:
            self_chain = frame.path + [(frame.tag, frame.raw_attrs)]
            if self.item_callback(self_chain, value) is False:
                raise ParsingInterrupted("item_callback returned False")
            return
        if depth < self.item_depth:
            return
        self._add_child(self.stack[-1].data, parent_chain, key, value)

    # -- value construction -----------------------------------------------------

    def _finalize(self, frame: _Frame, parent_chain: list) -> Any:
        raw_text = self.cdata_separator.join(frame.text_parts)
        text = raw_text.strip() if self.strip_whitespace else raw_text
        has_text = bool(text)

        if frame.data:
            if has_text:
                self_chain = frame.path + [(frame.tag, frame.raw_attrs)]
                result = self._pp(self_chain, self.cdata_key, text)
                if result is not None:
                    key, value = result
                    frame.data[key] = value
            return frame.data

        if not has_text:
            return None

        if self.force_cdata(parent_chain, frame.tag, text):
            wrapped = self.dict_constructor()
            wrapped[self.cdata_key] = text
            return wrapped
        return text


def parse(
    xml_input,
    *,
    encoding: Optional[str] = None,
    disable_entities: bool = True,
    process_namespaces: bool = False,
    namespace_separator: str = ":",
    namespaces: Optional[dict] = None,
    xml_attribs: bool = True,
    attr_prefix: str = "@",
    cdata_key: str = "#text",
    force_cdata: PathKeyValue = False,
    cdata_separator: str = "",
    strip_whitespace: bool = True,
    process_comments: bool = False,
    comment_key: str = "#comment",
    force_list: PathKeyValue = None,
    item_depth: int = 0,
    item_callback: Callable[[list, Any], Any] = lambda *args: True,
    postprocessor: Optional[Callable[[list, str, Any], Any]] = None,
    dict_constructor=dict,
    expat=_default_expat,
):
    """Parse XML into a dict.

    ``xml_input`` may be a ``str``, ``bytes``, a file-like object (anything
    with a ``.read()`` method), or an iterable of ``str``/``bytes`` chunks.

    The root element is depth 1. When ``item_depth`` is 0 (the default),
    the whole document is parsed and returned as a dict. When
    ``item_depth`` is greater than 0, parsing runs in streaming mode:
    every subtree found at that depth is handed to
    ``item_callback(path, item)`` and discarded rather than retained, so
    arbitrarily large documents can be processed in bounded memory;
    ``parse()`` itself returns ``None`` in that mode. Returning ``False``
    from ``item_callback`` raises :class:`ParsingInterrupted`.

    ``expat`` is pluggable: pass an object exposing ``ParserCreate`` (and,
    typically, ``ExpatError``) to use an alternate implementation.
    """
    handler = _SaxToDict(
        xml_attribs=xml_attribs,
        attr_prefix=attr_prefix,
        cdata_key=cdata_key,
        force_cdata=_make_predicate(force_cdata),
        cdata_separator=cdata_separator,
        strip_whitespace=strip_whitespace,
        process_comments=process_comments,
        comment_key=comment_key,
        force_list=_make_predicate(force_list),
        item_depth=item_depth,
        item_callback=item_callback,
        postprocessor=postprocessor,
        dict_constructor=dict_constructor,
        process_namespaces=process_namespaces,
        namespace_separator=namespace_separator,
        namespaces=namespaces,
    )

    parser = expat.ParserCreate(
        encoding, namespace_separator if process_namespaces else None
    )
    parser.buffer_text = True
    parser.ordered_attributes = False
    parser.StartElementHandler = handler.start_element
    parser.EndElementHandler = handler.end_element
    parser.CharacterDataHandler = handler.char_data
    if process_comments:
        parser.CommentHandler = handler.comment
    if process_namespaces:
        parser.StartNamespaceDeclHandler = handler.start_ns

    if disable_entities:
        def _forbid(*_args, **_kwargs):
            raise EntitiesForbidden(
                "entities are disabled (pass disable_entities=False to allow them)"
            )

        def _forbid_external(*_args, **_kwargs):
            raise EntitiesForbidden(
                "external entities are disabled (pass disable_entities=False to allow them)"
            )

        parser.EntityDeclHandler = _forbid
        parser.UnparsedEntityDeclHandler = _forbid
        parser.ExternalEntityRefHandler = _forbid_external

    _feed(parser, xml_input)

    if handler.item_depth == 0 and handler.result is not None:
        for text in handler._toplevel_comments:
            handler._add_child(handler.result, [], comment_key, text)

    return handler.result


def _feed(parser, xml_input) -> None:
    if isinstance(xml_input, (str, bytes)):
        parser.Parse(xml_input, True)
        return
    if hasattr(xml_input, "read"):
        while True:
            chunk = xml_input.read(_CHUNK_SIZE)
            if not chunk:
                break
            parser.Parse(chunk, False)
        parser.Parse("", True)
        return
    # Generic iterable of str/bytes chunks.
    for chunk in xml_input:
        parser.Parse(chunk, False)
    parser.Parse("", True)
