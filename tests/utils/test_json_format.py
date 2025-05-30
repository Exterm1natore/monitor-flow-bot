from app.utils.json_format import format_json_to_str


def test_simple_dict():
    data = {"name": "Alice", "age": 30}
    expected = "name: Alice\nage: 30"
    assert format_json_to_str(data) == expected


def test_nested_dict():
    data = {
        "user": {
            "name": "Bob",
            "details": {
                "age": 25,
                "city": "Moscow"
            }
        }
    }
    expected = (
        "user:\n"
        "  name: Bob\n"
        "  details:\n"
        "    age: 25\n"
        "    city: Moscow"
    )
    assert format_json_to_str(data) == expected


def test_list_in_dict():
    data = {
        "numbers": [1, 2, 3]
    }
    expected = (
        "numbers:\n"
        "  - 1\n"
        "  - 2\n"
        "  - 3"
    )
    assert format_json_to_str(data) == expected


def test_dict_in_list():
    data = {
        "items": [
            {"name": "Item1", "price": 10},
            {"name": "Item2", "price": 20}
        ]
    }
    expected = (
        "items:\n"
        "  - name: Item1\n"
        "    price: 10\n"
        "  - name: Item2\n"
        "    price: 20"
    )
    assert format_json_to_str(data) == expected


def test_list_of_strings():
    data = {"fruits": ["apple", "banana", "cherry"]}
    expected = (
        "fruits:\n"
        "  - apple\n"
        "  - banana\n"
        "  - cherry"
    )
    assert format_json_to_str(data) == expected


def test_string_with_escaped_newline():
    data = {"text": "Hello\\nWorld"}
    expected = "text: Hello\nWorld"
    assert format_json_to_str(data) == expected


def test_empty_dict():
    data = {}
    expected = ""
    assert format_json_to_str(data) == expected


def test_empty_list():
    data = {"items": []}
    expected = "items:\n"
    assert format_json_to_str(data) == expected


def test_top_level_list():
    data = [{"x": 1}, {"y": 2}]
    expected = (
        "- x: 1\n"
        "- y: 2"
    )
    assert format_json_to_str(data) == expected
