import pytest

import xmldictify as x

DOCTYPE_WITH_ENTITY = """<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe "boom">
]>
<root>&xxe;</root>"""

EXTERNAL_ENTITY = """<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>"""

BARE_DOCTYPE = '<?xml version="1.0"?><!DOCTYPE root><root>hi</root>'

DOCTYPE_WITH_EXTERNAL_DTD = """<?xml version='1.0'?>
<!DOCTYPE data SYSTEM "diagram.dtd">
<foo>bar</foo>"""


def test_entity_declaration_rejected_by_default():
    with pytest.raises(x.EntitiesForbidden):
        x.parse(DOCTYPE_WITH_ENTITY)


def test_external_entity_rejected_by_default():
    with pytest.raises(x.EntitiesForbidden):
        x.parse(EXTERNAL_ENTITY)


def test_bare_doctype_without_entities_is_allowed():
    # A DOCTYPE with no actual entity declarations is harmless and should
    # not be blocked, even under disable_entities=True.
    assert x.parse(BARE_DOCTYPE) == {"root": "hi"}


def test_doctype_with_external_dtd_reference_is_allowed():
    # Referencing an external DTD (but declaring no entities) is also
    # harmless and should not be blocked.
    assert x.parse(DOCTYPE_WITH_EXTERNAL_DTD, disable_entities=True) == {"foo": "bar"}
    assert x.parse(DOCTYPE_WITH_EXTERNAL_DTD, disable_entities=False) == {"foo": "bar"}


def test_disable_entities_false_allows_internal_entities():
    result = x.parse(DOCTYPE_WITH_ENTITY, disable_entities=False)
    assert result == {"root": "boom"}
