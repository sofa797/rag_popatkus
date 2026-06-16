# import pytest
from unittest.mock import patch
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))


def test_parse_section_regex(mock_pdfplumber):
    with patch("shared.parser.popatkus_parser.pdfplumber.open", mock_pdfplumber):
        from shared.parser.popatkus_parser import PopatkusParser
        mock_page = mock_pdfplumber.return_value.__enter__.return_value.pages[0]
        mock_page.extract_text.return_value = "I. Общие положения"
        parser = PopatkusParser("dummy.pdf")
        result = parser.parse()
        sections = [r for r in result if r.get("type") == "section"]
        assert len(sections) >= 1
        assert sections[0]["section"] == "I"


def test_parse_paragraph_regex(mock_pdfplumber):
    with patch("shared.parser.popatkus_parser.pdfplumber.open", mock_pdfplumber):
        from shared.parser.popatkus_parser import PopatkusParser
        mock_page = mock_pdfplumber.return_value.__enter__.return_value.pages[0]
        mock_page.extract_text.return_value = "1. Первый пункт текста"
        parser = PopatkusParser("dummy.pdf")
        result = parser.parse()
        paragraphs = [r for r in result if r.get("type") == "paragraph"]
        assert len(paragraphs) >= 1
        assert paragraphs[0]["item"] == "1"


def test_parse_definition_regex(mock_pdfplumber):
    with patch("shared.parser.popatkus_parser.pdfplumber.open", mock_pdfplumber):
        from shared.parser.popatkus_parser import PopatkusParser
        mock_page = mock_pdfplumber.return_value.__enter__.return_value.pages[0]
        mock_page.extract_text.return_value = "Используемые понятия и сокращения\nТермин – это определение слова"
        parser = PopatkusParser("dummy.pdf")
        result = parser.parse()
        definitions = [r for r in result if r.get("type") == "definition"]
        assert len(definitions) >= 1
        assert definitions[0]["term"] == "Термин"


def test_save_to_json(tmp_path):
    from shared.parser.popatkus_parser import PopatkusParser
    parser = PopatkusParser("dummy.pdf")
    parser.structures = [{"type": "test", "text": "content"}]
    output_file = tmp_path / "output.json"
    parser.save_to_json(str(output_file))
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data[0]["type"] == "test"
    assert data[0]["text"] == "content"


def test_get_statistics():
    from shared.parser.popatkus_parser import PopatkusParser
    parser = PopatkusParser("dummy.pdf")
    parser.structures = [
        {"type": "paragraph"},
        {"type": "paragraph"},
        {"type": "definition"},
        {"type": "section"}
    ]
    stats = parser.get_statistics()
    assert stats["paragraph"] == 2
    assert stats["definition"] == 1
    assert stats["section"] == 1
