import re

from conftest import ROOT
from _common import parse_yaml_text
from aggregate import COMMON_CAP_VALUES
from validate_persona import REQUIRED_SECTIONS
from validate_rubric import COMMON_CAPS, CONTEST_TYPES

REF = ROOT / "shared" / "references"
TYPE_SECTIONS = ("## 기대", "## 보이지 않는 감점", "## 추천 상한 규칙", "## 취지 질문", "## 페르소나 후보")


def test_contest_type_files_match_constant():
    assert {p.stem for p in (REF / "contest-types").glob("*.md")} == CONTEST_TYPES


def test_contest_type_sections_and_caps():
    for p in (REF / "contest-types").glob("*.md"):
        text = p.read_text(encoding="utf-8")
        for s in TYPE_SECTIONS:
            assert s in text, (p.name, s)
        block = re.search(r"## 추천 상한 규칙\n+```yaml\n(.*?)```", text, re.S)
        caps = parse_yaml_text(block.group(1), p.name)
        for c in caps:
            assert {"rule", "cap", "unlock", "source", "why"} <= set(c), (p.name, c)
            assert c["source"] == "inferred" and 0 <= c["cap"] <= 9


def test_common_caps_doc():
    text = (REF / "common-caps.md").read_text(encoding="utf-8")
    for rule in COMMON_CAPS:
        assert f"`{rule}`" in text, rule
    for rule, cap in COMMON_CAP_VALUES.items():
        assert re.search(rf"`{rule}`[^\n]*\| {cap} \|", text), rule


def test_persona_schema_lists_sections():
    text = (REF / "persona-schema.md").read_text(encoding="utf-8")
    for s in REQUIRED_SECTIONS:
        assert f"## {s}" in text, s


def test_required_files():
    for name in ("judge-stance.md", "rubric-schema.md", "persona-prompt.md", "persona-output.md", "grill-output.md"):
        assert (REF / name).read_text(encoding="utf-8").strip(), name
