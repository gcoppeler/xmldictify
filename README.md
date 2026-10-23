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
a dict. Key options: `attr_prefix` (default `'@'`), `cdata_key` (default
`'#text'`), `xml_attribs`, `force_list`, `force_cdata`, `process_namespaces`,
`namespaces`, `namespace_separator`, `process_comments`, `comment_key`,
`strip_whitespace`, `cdata_separator`, `postprocessor`, `dict_constructor`,
`disable_entities` (default `True`, blocks DOCTYPE/entity-based XXE
attacks), and the streaming pair `item_depth`/`item_callback`.

### `unparse(input_dict, output=None, **options)`

Converts a dict with exactly one top-level (root) key back into an XML
string, or writes it to `output` if given. Key options: `pretty`, `indent`,
`newl`, `short_empty_elements`, `full_document`, `encoding`, `attr_prefix`,
`cdata_key`, `expand_iter`.

See the module docstrings in `src/xmldictify/` for the full option
reference and the documented behavior for ambiguous/edge cases (empty
elements, streaming semantics, namespace collapsing, etc).

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e ".[test]"
.venv/bin/pytest
```
