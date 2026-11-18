"""설계 리뷰 반영: 인용 원문 대조, 다음 앵커 기준 고칠 것 순위, 데모 회피 유인 제거,
회차 흔들림 경보, 보정 채점 분리, 정직한 보고서 표기."""
import copy
from datetime import datetime

import pytest

from _common import load_json, load_yaml, write_json
import aggregate
from aggregate import aggregate as agg
from contest_dirs import new_run
import render_dashboard
from render_report import render
from factories import base_results, persona_result


@pytest.fixture
def rubric(contest_dir):
    return load_yaml(contest_dir / "rubric.yaml")


def item(result, iid):
    return next(i for i in result["items"] if i["id"] == iid)


# D1 — 원문에 없는 인용은 근거가 아니다
def test_quote_not_in_source_is_dropped(rubric):
    r = agg(rubric, base_results(), source_text="자료 본문 … impact   근거\n원문 …")
    assert r["quotes_verified"] is True
    feas = item(r, "feasibility")
    assert feas["by_persona"]["citizen"] == 6          # 8점이었지만 인용이 원문에 없어 6
    assert "quote-for-seven" in feas["caps"]
    assert item(r, "impact")["by_persona"]["developer"] == 8   # 공백·줄바꿈 차이는 같은 문장으로 본다
    assert any("원문에 없는 인용" in w for w in r["warnings"])


def test_no_source_means_unverified(rubric):
    assert agg(rubric, base_results())["quotes_verified"] is False


def test_cli_reads_target_folder(contest_dir):
    run = new_run(contest_dir, "score")
    for res in base_results():
        write_json(run / f"{res['persona']}.json", res)
    (run / "target").mkdir()
    (run / "target" / "slides.md").write_text("impact 근거 원문", encoding="utf-8")
    assert aggregate.main([str(run)]) == 0
    out = load_json(run / "result.json")
    assert out["quotes_verified"] is True
    assert item(out, "feasibility")["by_persona"]["citizen"] == 6


def test_read_target_skips_binary_originals(tmp_path):
    # 원본 PDF는 글자만 있어도 대조 원문에 섞이면 안 되고, 통째로 읽을 필요도 없다
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "slides.txt").write_text("추출한 본문", encoding="utf-8")
    (tmp_path / "target" / "slides.pdf").write_text("%PDF-1.4 ascii only", encoding="utf-8")
    (tmp_path / "target" / "shot.png").write_bytes(b"\x89PNG\r\n")
    assert aggregate._read_target(tmp_path) == "추출한 본문"


# D2 — 고칠 것은 다음 앵커까지 오르는 점수로 고른다
def test_fix_priority_targets_next_anchor(rubric):
    results = [
        persona_result("developer", {"feasibility": 4, "impact": 8}),
        persona_result("domain-expert", {"feasibility": 4, "impact": 6}),
        persona_result("citizen", {"feasibility": 5, "impact": 6}),
    ]
    r = agg(rubric, results)
    # feasibility: 16+7.5=23.5/55 → 4.27점 → 다음 앵커 5까지 4.0점. impact: 30/45 → 6.67 → 10까지 15점
    assert [f["item"] for f in r["fix_priority"]] == ["impact", "feasibility"]
    feas = r["fix_priority"][1]
    assert feas["gain"] == 4.0 and feas["next_anchor"] == 5
    assert feas["next_anchor_text"] == "핵심 기능 1개가 시연되지만 운영 주체가 없다"


def test_fix_priority_skips_full_marks(rubric):
    results = [persona_result(n, {"feasibility": 10, "impact": 6}) for n in ("developer", "domain-expert", "citizen")]
    assert [f["item"] for f in agg(rubric, results)["fix_priority"]] == ["impact"]


# D3 — 확인 불가가 시연 실패보다 유리하면 데모를 숨기게 된다
def test_unverified_not_better_than_failed(rubric):
    results = base_results()
    results[0] = persona_result("developer", {"feasibility": 6, "impact": 8}, caps={"feasibility": "claim-not-verified"})
    assert item(agg(rubric, results), "feasibility")["by_persona"]["developer"] == 4
    assert aggregate.COMMON_CAP_VALUES["claim-not-verified"] <= aggregate.COMMON_CAP_VALUES["claim-failed"]


# D4 — 같은 심사위원이 회차마다 크게 흔들리면 그 점수는 믿기 어렵다
def test_instability_alert(rubric):
    results = base_results()
    results[0]["runs"] = [copy.deepcopy(results[0]["runs"][0]) for _ in range(3)]
    for run, s in zip(results[0]["runs"], (3, 6, 6)):
        run["items"]["feasibility"]["score"] = s
    r = agg(rubric, results)
    assert r["instability_alerts"] == ["feasibility"]
    md, _ = render(r)
    assert "회차마다" in md


def test_report_states_what_score_means(rubric):
    r = agg(rubric, base_results())
    md, _ = render(r)
    assert "진단 지표" in md and "인용 원문 대조 안 함" in md
    r["total_range"] = [50.0, 60.0]
    md, _ = render(r)
    assert "신뢰구간 아님" in md


# D7 — 보정용으로 채점한 남의 작품은 내 회차 비교·추이에 섞이지 않는다
def test_calibration_runs_are_separate(contest_dir):
    cal = new_run(contest_dir, "score", datetime(2026, 10, 8, 9, 0))
    for res in base_results():
        write_json(cal / f"{res['persona']}.json", res)
    assert aggregate.main([str(cal), "--calibration", "--target", "2025 대상작"]) == 0
    mine = new_run(contest_dir, "score", datetime(2026, 10, 8, 10, 0))
    for res in base_results(gate=5):
        write_json(mine / f"{res['persona']}.json", res)
    assert aggregate.main([str(mine)]) == 0
    assert load_json(cal / "result.json")["calibration"] is True
    assert load_json(mine / "result.json")["previous"] is None
    history, html = render_dashboard.build(contest_dir)
    assert mine.name in history and cal.name not in history
    md, _ = render(load_json(cal / "result.json"))
    assert "보정용 채점" in md
