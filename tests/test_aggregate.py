import copy

import pytest

from _common import load_json, load_yaml, write_json
import aggregate
from aggregate import AggregateError, aggregate as agg
from contest_dirs import new_run
from factories import BASE, base_results, persona_result


@pytest.fixture
def rubric(contest_dir):
    return load_yaml(contest_dir / "rubric.yaml")


def item(result, iid):
    return next(i for i in result["items"] if i["id"] == iid)


def test_basic_total(rubric):
    r = agg(rubric, base_results())
    assert r["raw_total"] == 62.0 and r["total"] == 62.0
    assert item(r, "feasibility")["earned"] == 32.0
    assert item(r, "impact")["earned"] == 30.0
    assert r["gate"]["multiplier"] == 1.0 and r["gate"]["warning"] is False
    assert r["total_range"] is None
    assert r["participation"] == {"expected": 3, "succeeded": 3}


def test_gate_bands(rubric):
    assert agg(rubric, base_results(gate=5))["total"] == 52.7   # 62 × 0.85
    r = agg(rubric, base_results(gate=4))
    assert r["total"] == 37.2 and r["gate"]["warning"] is True  # 62 × 0.6


def test_gate_not_official_only_warns(rubric):
    rubric["gate"] = {"source": "inferred", "why": "추정"}
    r = agg(rubric, base_results(gate=3))
    assert r["total"] == 62.0 and r["gate"]["multiplier"] == 1.0 and r["gate"]["warning"] is True


def test_median_over_runs(rubric):
    results = base_results()
    results[0]["runs"] = [copy.deepcopy(results[0]["runs"][0]) for _ in range(3)]
    for run, s in zip(results[0]["runs"], (3, 6, 9)):
        run["items"]["feasibility"]["score"] = s
    assert item(agg(rubric, results), "feasibility")["by_persona"]["developer"] == 6


def test_quote_for_seven(rubric):
    results = base_results()
    results[0] = persona_result("developer", {"feasibility": 6, "impact": 9}, quotes=False)
    r = agg(rubric, results)
    impact = item(r, "impact")
    assert impact["by_persona"]["developer"] == 6
    assert "quote-for-seven" in impact["caps"]
    assert any("인용 없는 9점" in w for w in r["warnings"])


def test_cap_clamp(rubric):
    results = base_results()
    results[1] = persona_result("domain-expert", {"feasibility": 7, "impact": 6}, caps={"feasibility": "no-demo"})
    assert item(agg(rubric, results), "feasibility")["by_persona"]["domain-expert"] == 4


def test_common_cap_clamp(rubric):
    results = base_results()
    results[0] = persona_result("developer", {"feasibility": 8, "impact": 8}, caps={"feasibility": "claim-failed"})
    assert item(agg(rubric, results), "feasibility")["by_persona"]["developer"] == 4


def test_unknown_cap_warns(rubric):
    results = base_results()
    results[0] = persona_result("developer", {"feasibility": 6, "impact": 8}, caps={"impact": "made-up"})
    r = agg(rubric, results)
    assert any("모르는 상한 규칙" in w for w in r["warnings"])


def test_inferred_range(rubric):
    caps = {"feasibility": "no-demo"}
    results = [
        persona_result("developer", {"feasibility": 4, "impact": 8}, caps=caps),
        persona_result("domain-expert", {"feasibility": 4, "impact": 6}, caps=caps),
        persona_result("citizen", {"feasibility": 4, "impact": 6}, caps=caps),
    ]
    r = agg(rubric, results)
    # feasibility 22(=16+6), impact 30 → 52. inferred 상한 항목 ±1점: 16.5 ~ 27.5
    assert r["total"] == 52.0
    assert r["total_range"] == [46.5, 57.5]
    assert r["inferred_share"] == 0.55
    assert item(r, "feasibility")["inferred_dependent"] is True


def test_broken_persona_excluded(rubric):
    results = base_results()
    del results[1]["runs"][0]["items"]["impact"]
    r = agg(rubric, results)
    assert r["participation"] == {"expected": 3, "succeeded": 2}
    assert r["missing_personas"] == ["domain-expert"]
    assert any("impact" in e for e in r["failed"]["domain-expert"])
    # feasibility 24+12=36, impact 24+9=33
    assert r["total"] == 69.0


def test_missing_persona_file_counts(rubric):
    r = agg(rubric, base_results()[:1] + base_results()[2:])
    assert r["missing_personas"] == ["domain-expert"] and r["failed"] == {}


def test_group_all_failed_raises(rubric):
    results = base_results()
    results[2]["runs"] = []
    with pytest.raises(AggregateError, match="citizens"):
        agg(rubric, results)


def test_unknown_persona(rubric):
    r = agg(rubric, base_results() + [persona_result("ghost", BASE["developer"])])
    assert "rubric에 없는 페르소나" in r["failed"]["ghost"][0]


def test_score_type_error(rubric):
    results = base_results()
    results[0]["runs"][0]["items"]["impact"]["score"] = "8"
    r = agg(rubric, results)
    assert "developer" in r["failed"]


def test_deviation_and_priority(rubric):
    r = agg(rubric, base_results())
    assert r["deviation_alerts"] == ["feasibility"]          # 8-4=4, impact 8-6=2
    assert [f["item"] for f in r["fix_priority"]] == ["feasibility", "impact"]
    assert r["fix_priority"][0]["gain"] == 23.0               # 55-32


def test_consensus_gaps(rubric):
    results = [
        persona_result("developer", {"feasibility": 4, "impact": 8}, model="opus"),
        persona_result("domain-expert", {"feasibility": 5, "impact": 6}, model="sonnet"),
        persona_result("citizen", {"feasibility": 3, "impact": 6}, model="opus"),
    ]
    assert agg(rubric, results)["consensus_gaps"] == ["feasibility"]
    assert agg(rubric, base_results(model="opus"))["consensus_gaps"] == []


def test_previous_delta(rubric):
    prev = {"run": "20261001-1000_score", "total": 60.0,
            "items": [{"id": "feasibility", "earned": 30.0}, {"id": "impact", "earned": 30.0}]}
    r = agg(rubric, base_results(), previous=prev)
    assert r["previous"] == {"run": "20261001-1000_score", "total": 60.0, "delta": 2.0}
    assert item(r, "feasibility")["delta"] == 2.0


def test_flags(rubric):
    r = agg(rubric, base_results(independent=False))
    assert r["independent"] is False
    assert r["calibrated"] is False
    assert r["no_official_criteria"] is False
    assert any("evaluator_groups(citizens)" in s for s in r["inferred_rules"])
    assert r["narrative"] == {"overall": "", "personas": {}}


def test_cli_with_previous(contest_dir):
    from datetime import datetime
    first = new_run(contest_dir, "score", datetime(2026, 10, 8, 9, 0))
    for res in base_results():
        write_json(first / f"{res['persona']}.json", res)
    assert aggregate.main([str(first), "--target", "발표자료 v1"]) == 0
    second = new_run(contest_dir, "score", datetime(2026, 10, 8, 10, 0))
    for res in base_results(gate=5):
        write_json(second / f"{res['persona']}.json", res)
    assert aggregate.main([str(second)]) == 0
    out = load_json(second / "result.json")
    assert out["previous"]["run"] == first.name and out["previous"]["delta"] == -9.3
    assert out["target"] == "" and load_json(first / "result.json")["target"] == "발표자료 v1"


def test_cli_group_failed_exit(contest_dir, capsys):
    run = new_run(contest_dir, "score")
    write_json(run / "developer.json", base_results()[0])
    with pytest.raises(SystemExit) as e:
        from _common import run_cli
        run_cli(lambda: aggregate.main([str(run)]))
    assert e.value.code == 2
    assert "citizens" in capsys.readouterr().err


def test_consensus_needs_two_models_on_that_item(rubric):
    # 심사위원 1명만 채점한 항목은 "모델 2종 이상이 같은 판단"이 될 수 없다 — 회차 전체 모델 수로 판정하던 오류
    rb = copy.deepcopy(rubric)
    next(i for i in rb["items"] if i["id"] == "impact")["points"] = {"citizens": 15}
    results = [
        persona_result("developer", {"feasibility": 4}, model="opus"),
        persona_result("domain-expert", {"feasibility": 5}, model="sonnet"),
        persona_result("citizen", {"feasibility": 3, "impact": 2}, model="haiku"),
    ]
    assert agg(rb, results)["consensus_gaps"] == ["feasibility"]


def test_losses_and_max_gain(rubric):
    # 순위는 다음 기준까지 오르는 점수 그대로, 대신 못 받은 점수를 함께 낸다 — 배점 큰 항목의 손실이 묻히지 않게
    r = agg(rubric, base_results())
    feas = next(f for f in r["fix_priority"] if f["item"] == "feasibility")
    assert feas["max_gain"] == 23.0                           # 55-32
    assert r["losses"][0] == {"item": "feasibility", "name": "실현 가능성", "lost": 23.0, "caps": []}
    assert [x["lost"] for x in r["losses"]] == sorted((x["lost"] for x in r["losses"]), reverse=True)
