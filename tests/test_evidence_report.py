"""근거 장부가 합산 결과와 보고서에 실리는지."""
import pytest
import yaml

from _common import load_json, run_cli, write_json
import aggregate
from contest_dirs import new_run
from render_report import render
from factories import base_results
from test_evidence import ledger


@pytest.fixture
def run(contest_dir):
    r = new_run(contest_dir, "score")
    for res in base_results():
        write_json(r / f"{res['persona']}.json", res)
    return r


def test_aggregate_carries_ledger_summary(run):
    (run / "evidence.yaml").write_text(yaml.safe_dump(ledger(), allow_unicode=True), encoding="utf-8")
    assert aggregate.main([str(run)]) == 0
    ev = load_json(run / "result.json")["evidence"]
    assert [s["id"] for s in ev["sources"]] == ["s1", "s2"]
    assert {(g["item"], g["type"]) for g in ev["gaps"]} == {("feasibility", "numbers"), ("impact", "field-test")}


def test_report_shows_sources_and_gaps(run):
    l = ledger()
    l["absent"].append({"item": "impact", "type": "field-test", "source": "s2", "text": "사용자: 실증 안 함"})
    (run / "evidence.yaml").write_text(yaml.safe_dump(l, allow_unicode=True), encoding="utf-8")
    aggregate.main([str(run)])
    md, html = render(load_json(run / "result.json"))
    assert "## 확인한 자료와 빈칸" in md
    assert "https://github.com/x/y" in md and "repo_facts.py" in md
    assert "실현 가능성 — 숫자" in md            # 못 본 것 — 항목 이름과 근거 종류를 사람 말로
    assert "사용자: 실증 안 함" in md             # 없다고 확인된 것
    assert "근거 장부 없음" not in md


def test_report_without_ledger_says_so(run):
    aggregate.main([str(run)])
    r = load_json(run / "result.json")
    assert r["evidence"] is None
    md, _ = render(r)
    assert "근거 장부 없음" in md


def test_broken_ledger_is_input_error(run, capsys):
    l = ledger()
    l["evidence"][0]["source"] = "s9"
    (run / "evidence.yaml").write_text(yaml.safe_dump(l, allow_unicode=True), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        run_cli(lambda: aggregate.main([str(run)]))
    assert e.value.code == 2 and "s9" in capsys.readouterr().err
