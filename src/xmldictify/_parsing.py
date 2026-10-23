"""XML -> dict parsing, built directly on xml.parsers.expat."""

from __future__ import annotations

from typing import Any, Callable, Iterable, Optional, Union
from xml.parsers import expat

from ._errors import EntitiesForbidden, XMLParseError

_CHUNK_SIZE = 64 * 1024

Predicate = Callable[[tuple, str, Any], bool]
PathKeyValue = Union[bool, Iterable[str], Predicate, None]


class _StopParsing(Exception):
    """Internal sentinel raised to unwind expat when item_callback returns False."""


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
    __slots__ = ("tag", "path", "data", "text_parts")

    def __init__(self, tag: str, path: tuple, dict_constructor):
        self.tag = tag
        self.path = path
        self.data = dict_constructor()
        self.text_parts: list[str] = []


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
        self.namespaces = namespaces or {}

        self.stack: list[_Frame] = []
        self.result = None

    # -- namespace resolution -------------------------------------------------

    def _resolve_name(self, raw_name: str) -> str:
        if not self.process_namespaces:
            return raw_name
        sep = self.namespace_separator
        if sep not in raw_name:
            return raw_name
        uri, local = raw_name.rsplit(sep, 1)
        if uri in self.namespaces:
            prefix = self.namespaces[uri]
            return local if prefix is None else f"{prefix}:{local}"
        return raw_name

    # -- list/child attachment -------------------------------------------------

    def _add_child(self, container, path: tuple, key: str, value: Any) -> None:
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

    def start_element(self, raw_name: str, raw_attrs: dict) -> None:
        tag = self._resolve_name(raw_name)
        path = tuple(f.tag for f in self.stack)
        frame = _Frame(tag, path, self.dict_constructor)
        if self.xml_attribs:
            for raw_key, value in raw_attrs.items():
                key = self.attr_prefix + self._resolve_name(raw_key)
                frame.data[key] = value
        self.stack.append(frame)

    def char_data(self, data: str) -> None:
        if self.stack:
            self.stack[-1].text_parts.append(data)

    def comment(self, data: str) -> None:
        if not self.process_comments or not self.stack:
            return
        text = data.strip() if self.strip_whitespace else data
        frame = self.stack[-1]
        self._add_child(frame.data, frame.path, self.comment_key, text)

    def end_element(self, raw_name: str) -> None:
        frame = self.stack.pop()
        value = self._finalize(frame)

        if self.postprocessor is not None:
            result = self.postprocessor(frame.path, frame.tag, value)
            if result is None:
                return
            key, value = result
        else:
            key = frame.tag

        if not self.stack:
            self._finish_root(frame.path, key, value)
            return

        self._dispatch(frame.path, key, value)

    # -- value construction -----------------------------------------------------

    def _finalize(self, frame: _Frame) -> Any:
        raw_text = self.cdata_separator.join(frame.text_parts)
        text = raw_text.strip() if self.strip_whitespace else raw_text
        has_text = bool(text)

        if frame.data:
            if has_text:
                frame.data[self.cdata_key] = text
            return frame.data

        if not has_text:
            return None

        if self.force_cdata(frame.path, frame.tag, text):
            wrapped = self.dict_constructor()
            wrapped[self.cdata_key] = text
            return wrapped
        return text

    # -- attachment / streaming dispatch ----------------------------------------

    def _dispatch(self, path: tuple, key: str, value: Any) -> None:
        depth = len(self.stack)  # depth of the child that just finished

        if self.item_depth:
            if depth == self.item_depth:
                if self.item_callback(path, value) is False:
                    raise _StopParsing()
                return
            if depth < self.item_depth:
                return

        self._add_child(self.stack[-1].data, self.stack[-1].path, key, value)

    def _finish_root(self, path: tuple, key: str, value: Any) -> None:
        if self.item_depth:
            # Streaming mode: the root carries no retained value.
            self.result = None
            return
        wrapped = self.dict_constructor()
        wrapped[key] = value
        self.result = wrapped
        self.item_callback((), wrapped)


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
    item_callback: Callable[[tuple, Any], Any] = lambda *args: True,
    postprocessor: Optional[Callable[[tuple, str, Any], Any]] = None,
    dict_constructor=dict,
):
    """Parse XML into a dict.

    ``xml_input`` may be a ``str``, ``bytes``, a file-like object (anything
    with a ``.read()`` method), or an iterable of ``str``/``bytes`` chunks.

    When ``item_depth`` is 0 (the default), the whole document is parsed and
    returned as a single dict/scalar tree. When ``item_depth`` is greater
    than 0, parsing runs in streaming mode: every subtree found at that
    depth (root = depth 0) is handed to ``item_callback(path, item)`` and
    then discarded rather than retained, so arbitrarily large documents can
    be processed in bounded memory; ``parse()`` itself returns ``None`` in
    that mode. Returning ``False`` from ``item_callback`` stops parsing
    early (no exception is raised).

    ``path`` arguments passed to ``force_list``, ``force_cdata``,
    ``postprocessor`` and ``item_callback`` are tuples of ancestor tag
    names (not including the element's own tag).
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

    if disable_entities:
        def _forbid(*_args, **_kwargs):
            raise EntitiesForbidden(
                "DOCTYPE declarations and entities are disabled "
                "(pass disable_entities=False to allow them)"
            )

        def _forbid_external(*_args, **_kwargs):
            raise EntitiesForbidden(
                "External entity references are disabled "
                "(pass disable_entities=False to allow them)"
            )

        parser.StartDoctypeDeclHandler = _forbid
        parser.EntityDeclHandler = _forbid
        parser.UnparsedEntityDeclHandler = _forbid
        parser.ExternalEntityRefHandler = _forbid_external

    try:
        _feed(parser, xml_input)
    except _StopParsing:
        pass
    except expat.ExpatError as exc:
        raise XMLParseError(str(exc)) from exc

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
