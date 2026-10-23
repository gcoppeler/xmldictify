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


def test_doctype_rejected_by_default():
    with pytest.raises(x.EntitiesForbidden):
        x.parse(DOCTYPE_WITH_ENTITY)


def test_external_entity_rejected_by_default():
    with pytest.raises(x.EntitiesForbidden):
        x.parse(EXTERNAL_ENTITY)


def test_bare_doctype_without_entities_also_rejected_by_default():
    with pytest.raises(x.EntitiesForbidden):
        x.parse(BARE_DOCTYPE)


def test_disable_entities_false_allows_internal_entities():
    result = x.parse(DOCTYPE_WITH_ENTITY, disable_entities=False)
    assert result == {"root": "boom"}
