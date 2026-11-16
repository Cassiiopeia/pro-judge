import re

from conftest import ROOT
from _common import parse_yaml_text

# skill 3개: 대회 준비, 채점, 질의응답
SKILLS = ("pj-prepare", "pj-score", "pj-qna")
SCRIPTS = {p.name for p in (ROOT / "shared" / "scripts").glob("*.py")}
REFS = {p.relative_to(ROOT / "shared" / "references").as_posix()
        for p in (ROOT / "shared" / "references").rglob("*.md")}


def frontmatter(text):
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    assert m, "머리말 없음"
    return parse_yaml_text(m.group(1), "SKILL.md")


def test_skill_frontmatter():
    for name in SKILLS:
        meta = frontmatter((ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8"))
        assert meta["name"] == name
        assert len(meta["description"]) > 40


def test_referenced_paths_exist():
    docs = [ROOT / "skills" / name / "SKILL.md" for name in SKILLS]
    docs += list((ROOT / "shared" / "references").glob("*.md"))
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for script in re.findall(r"shared/scripts/([\w_]+\.py)", text):
            assert script in SCRIPTS, (doc.name, script)
        for ref in re.findall(r"shared/references/([\w\-/]+\.md)", text):
            assert ref in REFS or ref.startswith("contest-types/<"), (doc.name, ref)


def test_example_is_valid():
    import validate_persona, validate_rubric
    example = ROOT / "skills" / "pj-prepare" / "references" / "example"
    assert validate_rubric.main([str(example)]) == 0
    assert validate_persona.main([str(example)]) == 0
