import copy

import pytest

from _common import InputError, load_yaml, parse_yaml_text
import validate_rubric
from validate_rubric import validate_rubric as check


def load(contest_dir):
    return load_yaml(contest_dir / "rubric.yaml")


def test_ok(contest_dir):
    assert check(load(contest_dir), contest_dir / "personas") == []


def has(errors, text):
    return any(text in e for e in errors), errors


def test_weight_sum(contest_dir):
    r = load(contest_dir)
    r["evaluator_groups"][0]["weight"] = 60
    ok, errs = has(check(r), "weight 합이 100이 아님")
    assert ok, errs


def test_item_points_mismatch(contest_dir):
    r = load(contest_dir)
    r["items"][0]["points"]["judges"] = 30
    ok, errs = has(check(r), "항목 배점 합")
    assert ok, errs


def test_empty_anchor(contest_dir):
    r = load(contest_dir)
    r["items"][0]["anchors"][5] = ""
    ok, errs = has(check(r), "anchors.5: 비어 있음")
    assert ok, errs


def test_banned_anchor_word(contest_dir):
    r = load(contest_dir)
    r["items"][0]["anchors"][10] = "근거가 충분하다"
    ok, errs = has(check(r), "관찰 불가 표현")
    assert ok, errs


def test_inferred_needs_why(contest_dir):
    r = load(contest_dir)
    del r["evaluator_groups"][1]["why"]
    ok, errs = has(check(r), "why")
    assert ok, errs


def test_missing_source(contest_dir):
    r = load(contest_dir)
    del r["items"][1]["source"]
    ok, errs = has(check(r), "items[impact]: source")
    assert ok, errs


def test_missing_persona_file(contest_dir):
    (contest_dir / "personas" / "citizen.md").unlink()
    ok, errs = has(check(load(contest_dir), contest_dir / "personas"), "personas/citizen.md 없음")
    assert ok, errs


def test_group_without_persona(contest_dir):
    r = load(contest_dir)
    r["evaluator_groups"][1]["personas"] = []
    ok, errs = has(check(r), "페르소나가 없음")
    assert ok, errs


def test_question_count(contest_dir):
    r = load(contest_dir)
    r["items"][0]["questions"] = r["items"][0]["questions"][:1]
    ok, errs = has(check(r), "2~3개")
    assert ok, errs


def test_gate_needs_zero_band(contest_dir):
    r = load(contest_dir)
    r["gate"]["bands"] = [b for b in r["gate"]["bands"] if b["min"] != 0]
    ok, errs = has(check(r), "min 0")
    assert ok, errs


def test_wrong_types_do_not_crash(contest_dir):
    r = load(contest_dir)
    r["items"] = "abc"
    r["evaluator_groups"] = {"x": 1}
    errs = check(r)
    assert any("items: 목록이어야 함" in e for e in errs)
    assert any("evaluator_groups: 목록이어야 함" in e for e in errs)
    assert check("문자열") == ["rubric.yaml 최상위는 매핑이어야 함"]


def test_cli_ok(contest_dir, capsys):
    assert validate_rubric.main([str(contest_dir)]) == 0
    assert "OK" in capsys.readouterr().out


def test_cli_defects(contest_dir, capsys):
    p = contest_dir / "rubric.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace("weight: 70", "weight: 60"), encoding="utf-8")
    assert validate_rubric.main([str(contest_dir)]) == 1
    assert "실패:" in capsys.readouterr().out


def test_yaml_syntax_error(tmp_path):
    with pytest.raises(InputError, match="YAML 문법 오류"):
        parse_yaml_text("a: [1, 2", "rubric.yaml")


def test_pyyaml_missing(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "yaml", None)
    with pytest.raises(InputError, match="pip install pyyaml"):
        parse_yaml_text("a: 1", "x")
