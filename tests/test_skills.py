import re

from conftest import ROOT
from _common import parse_yaml_text

SKILLS = ("using-pro-judge", "pro-judge-setup", "pro-judge-ideas", "pro-judge-score", "pro-judge-grill")
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
    for name in SKILLS:
        text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        for script in re.findall(r"shared/scripts/([\w_]+\.py)", text):
            assert script in SCRIPTS, (name, script)
        for ref in re.findall(r"shared/references/([\w\-/]+\.md)", text):
            assert ref in REFS or ref.startswith("contest-types/<"), (name, ref)


def test_example_is_valid():
    import validate_persona, validate_rubric
    example = ROOT / "skills" / "pro-judge-setup" / "references" / "example"
    assert validate_rubric.main([str(example)]) == 0
    assert validate_persona.main([str(example)]) == 0
