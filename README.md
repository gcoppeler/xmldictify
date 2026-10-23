# xmldictify

Convert XML to Python dicts and back again — a small, dependency-free
library built directly on the standard library's `xml.parsers.expat`.

```python
import xmldictify

doc = xmldictify.parse("""
<response>
    <status>good</status>
    <value a="1" b="2">hello</value>
</response>
""")
# {'response': {'status': 'good', 'value': {'@a': '1', '@b': '2', '#text': 'hello'}}}

xml = xmldictify.unparse(doc, pretty=True)
```

## Why

This is an independent, from-scratch implementation offering functionality
equivalent to the popular [`xmltodict`](https://github.com/martinblech/xmltodict)
library, written without reusing any of that project's source code.

## API

### `parse(xml_input, **options)`

Parses XML (a `str`, `bytes`, file-like object, or iterable of chunks) into
a dict. The root element is depth 1. Key options: `attr_prefix` (default
`'@'`), `cdata_key` (default `'#text'`), `xml_attribs`, `force_list`,
`force_cdata`, `process_namespaces`, `namespaces`, `namespace_separator`,
`process_comments`, `comment_key`, `strip_whitespace`, `cdata_separator`,
`postprocessor`, `dict_constructor`, `disable_entities` (default `True`,
blocks DOCTYPE/entity-based XXE attacks), `expat` (pluggable parser
module, defaults to the stdlib one), and the streaming pair
`item_depth`/`item_callback` (a callback returning `False` raises
`ParsingInterrupted`).

### `unparse(input_dict, output=None, **options)`

Converts a dict back into an XML string, or writes it to `output` if
given. When `full_document=True` (the default), `input_dict` must have
exactly one top-level key (aside from any `comment_key` entry); with
`full_document=False`, any number of top-level entries (or none) are
emitted as siblings with no wrapping tag. Key options: `pretty`, `indent`,
`newl`, `short_empty_elements`, `full_document`, `encoding`,
`bytes_errors`, `attr_prefix`, `cdata_key`, `comment_key`, `expand_iter`,
`namespaces` (collapses `uri:local` keys back to a short prefix, and
reconstructs an `'@xmlns'` dict value into `xmlns`/`xmlns:prefix`
attributes), and `preprocessor(key, value)` (called for every
attribute/text/comment/child pair; return `None` to drop it).

Booleans coerce to lowercase `"true"`/`"false"`; `bytes` values are
decoded using `encoding`/`bytes_errors`; a `None` attribute value
serializes as `""`.

See the module docstrings in `src/xmldictify/` for the full option
reference and the documented behavior for ambiguous/edge cases.

## Equivalence with xmltodict

This implementation's behavior was independently verified against
`xmltodict`'s own published test suite (`tests/test_xmltodict.py` and
`tests/test_dicttoxml.py`, fetched from its GitHub repository) — not its
source code — which both pass in full against this package via a thin
import-aliasing shim. That test suite is not vendored into this repo.

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e ".[test]"
.venv/bin/pytest
```
