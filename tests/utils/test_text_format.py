from app.utils.text_format import split_text, normalize_whitespace


# -------- Tests for split_text --------

def test_split_text_exact_division():
    text = "abcdefghij"  # длина 10
    result = split_text(text, 2)
    assert result == ["ab", "cd", "ef", "gh", "ij"]


def test_split_text_not_exact():
    text = "abcdefghijk"  # длина 11
    result = split_text(text, 3)
    assert result == ["abc", "def", "ghi", "jk"]


def test_split_text_shorter_than_max():
    text = "short"
    result = split_text(text, 10)
    assert result == ["short"]


def test_split_text_equal_to_max():
    text = "abcdefgh"
    result = split_text(text, 8)
    assert result == ["abcdefgh"]


def test_split_text_empty():
    text = ""
    result = split_text(text, 5)
    assert result == []


def test_split_text_unicode():
    text = "12345678"
    result = split_text(text, 4)
    assert result == ["1234", "5678"]


# -------- Tests for normalize_whitespace --------

def test_normalize_whitespace_basic():
    text = "   Hello   world  "
    result = normalize_whitespace(text)
    assert result == "Hello world"


def test_normalize_whitespace_multiple_lines_and_tabs():
    text = "\tThis\nis\n  a \t test\n"
    result = normalize_whitespace(text)
    assert result == "This is a test"


def test_normalize_whitespace_only_spaces():
    text = "     "
    result = normalize_whitespace(text)
    assert result == ""


def test_normalize_whitespace_with_unicode_spaces():
    text = "Hello\u2003world"  # EM SPACE between words
    result = normalize_whitespace(text)
    assert result == "Hello world"


def test_normalize_whitespace_empty_string():
    assert normalize_whitespace("") == ""
