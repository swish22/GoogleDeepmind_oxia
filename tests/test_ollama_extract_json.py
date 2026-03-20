import json

from llm.json_extract import extract_first_json_object, strip_trailing_commas_json


def test_extract_sanitizes_escaped_underscore_and_trailing_text():
    raw = """```json
{
  "meal\\_name": "Vita Bowl",
  "ingredients": ["rice"]
}
] trailing garbage
```"""

    extracted = extract_first_json_object(raw)
    parsed = json.loads(extracted)
    assert parsed["meal_name"] == "Vita Bowl"
    assert parsed["ingredients"] == ["rice"]


def test_extract_handles_trailing_characters_after_json():
    raw = '{"a": 1} ]}] more'
    extracted = extract_first_json_object(raw)
    parsed = json.loads(extracted)
    assert parsed == {"a": 1}


def test_strip_trailing_commas_nested():
    raw = """{
  "meal_name": "Vita",
  "ingredients": ["a", "b",],
  "x": 1,
}"""
    fixed = strip_trailing_commas_json(raw)
    assert json.loads(fixed) == {"meal_name": "Vita", "ingredients": ["a", "b"], "x": 1}


def test_extract_handles_trailing_comma_before_closing_brace():
    # Common LLM mistake: comma after last field
    raw = """{
  "meal_name": "Vita Co",
  "ingredients": ["x"],
  "estimated_glycemic_load": 40,
}"""
    extracted = extract_first_json_object(raw)
    parsed = json.loads(extracted)
    assert parsed["meal_name"] == "Vita Co"
    assert parsed["estimated_glycemic_load"] == 40
