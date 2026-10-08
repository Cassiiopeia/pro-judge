import pytest

from _common import InputError, load_yaml
from aggregate import aggregate
from rank_ideas import rank_ideas
from render_report import render
from factories import base_results

GRILL = {
    "kind": "grill", "contest": "테스트-해커톤", "created_at": "2026-10-08T15:00", "mode": "practice",
    "questions": [
        {"persona": "developer", "item": "feasibility", "question": "지금 눌러 볼 수 있나요?",
         "answer": "배포 주소 있습니다", "verdict": "up", "reason": "배포 주소 제시",
         "follow_ups": [{"question": "주소가 뭐죠?", "answer": "준비 중", "verdict": "down", "reason": "주소 없음"}],
         "model_answer": None},
        {"persona": "domain-expert", "item": "impact", "question": "누가 운영하나요?",
         "answer": "아마 구청", "verdict": "same", "reason": "추측", "follow_ups": [], "model_answer": None},
    ],
    "suggestions": [{"evidence": "베타 사용자 12명", "item": "impact", "from_score": 5, "to_score": 7}],
    "narrative": {"overall": "운영 주체 답변이 약하다."},
}


def test_grill_report():
    md, html = render(GRILL)
    for text in ("질의응답 보고서", "지금 눌러 볼 수 있나요?", "올림", "깎음", "꼬리", "## 약한 답변",
                 "베타 사용자 12명", "5 → 7", "운영 주체 답변이 약하다."):
        assert text in md, text
    weak = md.split("## 약한 답변")[1].split("##")[0]
    assert weak.index("주소가 뭐죠?") < weak.index("누가 운영하나요?")  # 깎음이 그대로보다 먼저
    assert "&lt;" not in md and "<table>" in html


def test_grill_sheet_mode():
    sheet = {**GRILL, "mode": "sheet",
             "questions": [{"persona": "developer", "item": "feasibility", "question": "Q1", "answer": None,
                            "verdict": None, "reason": "", "follow_ups": [], "model_answer": "[숫자] 근거로 답한다"}]}
    md, _ = render(sheet)
    assert "## 예상 질문지" in md and "[숫자] 근거로 답한다" in md


def test_grill_invalid():
    bad = {**GRILL, "questions": [{**GRILL["questions"][0], "verdict": "great"}]}
    with pytest.raises(InputError, match="verdict"):
        render(bad)


def test_ideas_report(contest_dir):
    rubric = load_yaml(contest_dir / "rubric.yaml")
    results = {"idea-1": aggregate(rubric, base_results()), "idea-2": aggregate(rubric, base_results(gate=4))}
    out = rank_ideas([{"id": "idea-1", "title": "동네 지도", "cost_level": "mid", "cost_note": "1주"},
                      {"id": "idea-2", "title": "챗봇", "cost_level": "low", "cost_note": "3일"}], results)
    md, _ = render(out)
    for text in ("아이디어 비교", "동네 지도", "취지 경보", "1주", "## 동네 지도 — 점수를 막는 것"):
        assert text in md, text
