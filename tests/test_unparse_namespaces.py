import xmldictify as x


def test_namespace_collapse_and_xmlns_reconstruction():
    obj = {
        "http://defaultns.com/:root": {
            "@xmlns": {
                "": "http://defaultns.com/",
                "a": "http://a.com/",
            },
            "http://defaultns.com/:x": "1",
            "http://a.com/:y": "2",
        }
    }
    ns = {"http://defaultns.com/": "", "http://a.com/": "a"}
    result = x.unparse(obj, namespaces=ns, full_document=False)
    assert result == (
        '<root xmlns="http://defaultns.com/" xmlns:a="http://a.com/">'
        "<x>1</x><a:y>2</a:y></root>"
    )


def test_namespace_roundtrip():
    xml = '<root xmlns:a="http://a.com/" id="7"><a:y>2</a:y></root>'
    parsed = x.parse(xml, process_namespaces=True)
    result = x.unparse(parsed, namespaces={"http://a.com/": "a"}, full_document=False)
    reparsed = x.parse(result, process_namespaces=True)
    assert reparsed == parsed
