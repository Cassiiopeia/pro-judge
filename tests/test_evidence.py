"""근거 장부(evidence.yaml): 형식 검사와 빈칸 계산."""
import copy

import pytest
import yaml

from _common import InputError, load_yaml
import evidence as ev


def ledger(**over):
    base = {
        "scope": "target",
        "subject": "테스트 대상",
        "sources": [
            {"id": "s1", "kind": "repo", "ref": "https://github.com/x/y", "how": "repo_facts.py", "trust": "self", "status": "ok"},
            {"id": "s2", "kind": "user", "ref": "시연 영상 있나요?", "how": "사용자 답변", "trust": "user", "status": "ok"},
        ],
        "evidence": [
            {"item": "feasibility", "type": "demo", "source": "s1", "text": "배포 주소에서 로그인 작동"},
            {"item": "impact", "type": "numbers", "source": "s1", "text": "베타 사용자 12명"},
        ],
        "absent": [],
    }
    base.update(over)
    return base


@pytest.fixture
def rubric(contest_dir):
    return load_yaml(contest_dir / "rubric.yaml")


def test_valid_ledger_has_no_errors(rubric):
    assert ev.check(ledger(), rubric) == []


@pytest.mark.parametrize("mutate, word", [
    (lambda l: l.update(scope="all"), "scope"),
    (lambda l: l["sources"].append(dict(l["sources"][0])), "중복"),
    (lambda l: l["sources"][0].update(kind="tv"), "kind"),
    (lambda l: l["sources"][0].update(trust="maybe"), "trust"),
    (lambda l: l["sources"][0].update(status="done"), "status"),
    (lambda l: l["evidence"][0].update(source="s9"), "s9"),
    (lambda l: l["evidence"][0].update(type="vibe"), "type"),
    (lambda l: l["evidence"][0].update(item="nope"), "nope"),
])
def test_check_catches_errors(rubric, mutate, word):
    l = ledger()
    mutate(l)
    errs = ev.check(l, rubric)
    assert errs and any(word in e for e in errs), errs


def test_target_gaps_follow_rubric_evidence_types(rubric):
    # 점수표: feasibility [demo, numbers], impact [numbers, field-test]
    gaps = ev.gaps(ledger(), rubric)
    assert {(g["item"], g["type"]) for g in gaps} == {("feasibility", "numbers"), ("impact", "field-test")}


def test_star_item_and_absent_fill_gaps(rubric):
    l = ledger()
    l["evidence"].append({"item": "*", "type": "numbers", "source": "s1", "text": "커밋 52개"})
    l["absent"].append({"item": "impact", "type": "field-test", "source": "s2", "text": "사용자: 실증 안 함"})
    assert ev.gaps(l, rubric) == []


def test_failed_source_does_not_fill(rubric):
    l = ledger()
    l["sources"][0]["status"] = "failed"
    gaps = {(g["item"], g["type"]) for g in ev.gaps(l, rubric)}
    assert ("feasibility", "demo") in gaps and ("impact", "numbers") in gaps


def test_contest_gaps_use_fixed_topics():
    l = ledger(scope="contest", evidence=[
        {"item": "announcement", "type": "quote", "source": "s1", "text": "공고 원문"},
        {"item": "criteria", "type": "numbers", "source": "s1", "text": "항목별 배점"},
    ], absent=[{"item": "past-winners", "type": "observation", "source": "s2", "text": "역대 수상작 공개 안 됨"}])
    assert ev.check(l, None) == []
    assert [g["item"] for g in ev.gaps(l, None)] == ["schedule", "submission", "penalties", "judges"]


def test_contest_rejects_unknown_topic():
    l = ledger(scope="contest", evidence=[{"item": "vibes", "type": "quote", "source": "s1", "text": "x"}])
    assert any("vibes" in e for e in ev.check(l, None))


def test_summary_for_report(rubric):
    s = ev.summary(ledger(), rubric)
    assert [x["id"] for x in s["sources"]] == ["s1", "s2"]
    assert len(s["gaps"]) == 2 and s["absent"] == []
    assert s["gaps"][0]["name"]  # 항목 이름이 붙는다


def test_cli_gaps(tmp_path, contest_dir, capsys):
    p = tmp_path / "evidence.yaml"
    p.write_text(yaml.safe_dump(ledger(), allow_unicode=True), encoding="utf-8")
    assert ev.main(["gaps", str(p), "--rubric", str(contest_dir / "rubric.yaml")]) == 0
    out = capsys.readouterr().out
    assert "feasibility" in out and "numbers" in out


def test_cli_check_fails_on_broken(tmp_path, contest_dir, capsys):
    l = ledger()
    l["evidence"][0]["source"] = "s9"
    p = tmp_path / "evidence.yaml"
    p.write_text(yaml.safe_dump(l, allow_unicode=True), encoding="utf-8")
    assert ev.main(["check", str(p), "--rubric", str(contest_dir / "rubric.yaml")]) == 1
    assert "s9" in capsys.readouterr().out
