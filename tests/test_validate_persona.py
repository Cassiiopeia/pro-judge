from _common import load_yaml
import validate_persona
from validate_persona import validate_persona as check


def read(contest_dir, name):
    return (contest_dir / "personas" / f"{name}.md").read_text(encoding="utf-8")


def test_ok(contest_dir):
    rubric = load_yaml(contest_dir / "rubric.yaml")
    for name in ("developer", "domain-expert", "citizen"):
        assert check(read(contest_dir, name), name, rubric) == []


def test_no_frontmatter():
    assert "머리말" in check("# 제목\n\n## 누구인가\n누구\n", "x")[0]


def test_name_mismatch(contest_dir):
    errs = check(read(contest_dir, "developer"), "dev")
    assert any("파일명과 다름" in e for e in errs)


def test_missing_section(contest_dir):
    text = read(contest_dir, "developer").replace("## 단골 질문", "## 다른 칸")
    assert any("'## 단골 질문' 칸 없음" in e for e in check(text, "developer"))


def test_empty_section(contest_dir):
    text = read(contest_dir, "developer").replace("짧고 건조하다. 숫자를 되묻는다.", "")
    assert any("'## 말투' 칸이 비어 있음" in e for e in check(text, "developer"))


def test_bad_strictness(contest_dir):
    text = read(contest_dir, "developer").replace("strictness: strict", "strictness: 매우")
    assert any("strictness" in e for e in check(text, "developer"))


def test_group_not_in_rubric(contest_dir):
    rubric = load_yaml(contest_dir / "rubric.yaml")
    text = read(contest_dir, "developer").replace("group: judges", "group: citizens")
    assert any("personas 목록에 없음" in e for e in check(text, "developer", rubric))


def test_frontmatter_syntax_error():
    errs = check("---\nname: [x\n---\n", "x")
    assert any("YAML 문법 오류" in e for e in errs)


def test_cli(contest_dir, capsys):
    assert validate_persona.main([str(contest_dir)]) == 0
    (contest_dir / "personas" / "citizen.md").write_text("없음", encoding="utf-8")
    assert validate_persona.main([str(contest_dir)]) == 1
    assert "citizen" in capsys.readouterr().out


def test_cli_no_personas(tmp_path, capsys):
    (tmp_path / "personas").mkdir()
    assert validate_persona.main([str(tmp_path)]) == 1
