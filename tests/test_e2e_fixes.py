"""실제 공고로 끝까지 돌린 실측에서 나온 결함."""
import pytest

from _common import InputError, load_yaml, run_cli
from aggregate import aggregate as agg
import render_dashboard
import render_report
import rank_ideas
import validate_persona
import validate_rubric
from factories import base_results, persona_result


@pytest.fixture
def rubric(contest_dir):
    return load_yaml(contest_dir / "rubric.yaml")


def item(result, iid):
    return next(i for i in result["items"] if i["id"] == iid)


# E1 — 페르소나를 쓰기 전 단계에서도 점수표 자체는 검사할 수 있어야 한다
def test_rubric_check_before_personas_exist(contest_dir, capsys):
    for f in (contest_dir / "personas").glob("*.md"):
        f.unlink()
    assert validate_rubric.main([str(contest_dir)]) == 1
    assert validate_rubric.main([str(contest_dir), "--skip-personas"]) == 0


# E2·E3 — 페르소나는 자기 그룹에 배점이 있는 항목만 채점하고, 다른 그룹 점수는 경보·표에 섞지 않는다
def test_persona_scores_only_own_group_items(rubric):
    rubric["items"].append({
        "id": "citizen-only", "name": "시민 체감", "points": {"citizens": 0}, "source": "inferred", "why": "x",
        "questions": [{"text": "a", "source": "inferred", "why": "x"}, {"text": "b", "source": "inferred", "why": "x"}],
        "evidence_types": ["observation"], "anchors": {0: "a", 5: "b", 10: "c"}, "caps": []})
    results = base_results()
    results[2]["runs"][0]["items"]["citizen-only"] = {"score": 2, "quotes": [], "cap_applied": None, "unlock_hint": None}
    r = agg(rubric, results)
    assert r["participation"]["succeeded"] == 3          # judges는 citizen-only를 안 매겨도 실패가 아니다
    assert item(r, "citizen-only")["by_persona"] == {"citizen": 2}


def test_spread_only_within_scoring_groups(rubric):
    rubric["items"][0]["points"] = {"judges": 55}
    rubric["items"][1]["points"] = {"judges": 15, "citizens": 30}
    results = base_results()
    results[2]["runs"][0]["items"]["feasibility"]["score"] = 0   # 배점 없는 그룹의 '자리 채움' 점수
    r = agg(rubric, results)
    feas = item(r, "feasibility")
    assert "citizen" not in feas["by_persona"]
    assert feas["spread"] == 2 and "feasibility" not in r["deviation_alerts"]


# E5 — 공고에 취지 기준이 없으면 취지 경보도 없다
def test_no_gate_no_warning(rubric):
    rubric["gate"] = {"source": "none"}
    r = agg(rubric, base_results(gate=2))
    assert r["gate"]["warning"] is False
    md, _ = render_report.render(r)
    assert "취지 경보" not in md


# 고칠 것 표의 해제 조건 칸은 대표 문장 하나만 — 비슷한 문장 다섯 개를 이어 붙이지 않는다
def test_fix_table_shows_one_unlock_hint(rubric):
    results = base_results()
    for n, res in enumerate(results):
        res["runs"][0]["items"]["feasibility"]["unlock_hint"] = f"배포 주소가 필요하다 {n}"
    md, _ = render_report.render(agg(rubric, results))
    row = next(line for line in md.splitlines() if line.startswith("| 1 |"))
    assert row.count("배포 주소가 필요하다") == 1


# 없는 폴더를 주면 traceback 대신 한 줄 오류
@pytest.mark.parametrize("main", [render_report.main, render_dashboard.main, rank_ideas.main])
def test_missing_folder_is_input_error(tmp_path, capsys, main):
    with pytest.raises(SystemExit) as e:
        run_cli(lambda: main([str(tmp_path / "없음")]))
    assert e.value.code == 2 and "오류:" in capsys.readouterr().err


# E7 — 단골 질문은 3개 이상 (스키마 문서와 검사기가 같은 규칙을 쓴다)
def test_persona_needs_three_questions(contest_dir):
    text = (contest_dir / "personas" / "developer.md").read_text(encoding="utf-8")
    head, rest = text.split("## 단골 질문\n", 1)
    body, tail = rest.split("\n## ", 1)
    two = "- 질문 하나?\n- 질문 둘?\n"
    errs = validate_persona.validate_persona(head + "## 단골 질문\n" + two + "\n## " + tail, "developer")
    assert any("단골 질문" in e and "3개" in e for e in errs)
