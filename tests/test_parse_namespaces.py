import xmldictify as x

NS_XML = """<root xmlns="http://defaultns.com/" xmlns:a="http://a.com/" xmlns:b="http://b.com/">
<x>1</x><a:y>2</a:y><b:z>3</b:z></root>"""


def test_default_no_namespace_processing():
    result = x.parse(NS_XML)
    assert result["root"]["@xmlns"] == "http://defaultns.com/"
    assert result["root"]["@xmlns:a"] == "http://a.com/"
    assert result["root"]["x"] == "1"
    assert result["root"]["a:y"] == "2"


def test_process_namespaces_expands_to_uri():
    # The @xmlns declarations are always reconstructed verbatim (raw URIs),
    # regardless of how element/attribute names are resolved.
    result = x.parse(NS_XML, process_namespaces=True)
    assert result == {
        "http://defaultns.com/:root": {
            "@xmlns": {
                "": "http://defaultns.com/",
                "a": "http://a.com/",
                "b": "http://b.com/",
            },
            "http://defaultns.com/:x": "1",
            "http://a.com/:y": "2",
            "http://b.com/:z": "3",
        }
    }


def test_namespaces_collapse_map():
    result = x.parse(
        NS_XML,
        process_namespaces=True,
        namespaces={"http://defaultns.com/": None, "http://a.com/": "ns_a"},
    )
    assert result == {
        "root": {
            "@xmlns": {
                "": "http://defaultns.com/",
                "a": "http://a.com/",
                "b": "http://b.com/",
            },
            "x": "1",
            "ns_a:y": "2",
            "http://b.com/:z": "3",
        }
    }


def test_custom_namespace_separator():
    result = x.parse(NS_XML, process_namespaces=True, namespace_separator="|")
    assert "http://defaultns.com/|root" in result
