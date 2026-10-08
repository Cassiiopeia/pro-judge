"""보고서 화면 설계 — 첫 화면에서 총점과 할 일이 먼저 보이고, 위험한 항목이 색으로 드러나는지."""
import re
from datetime import datetime

import pytest

from _common import load_yaml, write_json
from aggregate import aggregate
from contest_dirs import new_run
import render_dashboard
import render_report
from render_report import contest_labels, render
from report_blocks import to_html, to_markdown
from factories import base_results
from test_render_grill_ideas import GRILL


@pytest.fixture
def result(contest_dir):
    r = aggregate(load_yaml(contest_dir / "rubric.yaml"), base_results(),
                  created_at="2026-10-08T14:05", target="발표자료 v1", run="20261008-1405_score")
    r["narrative"]["overall"] = "실현 가능성이 가장 약하다."
    return r


def test_total_comes_before_notices(result):
    # 경고 상자가 총점을 밀어내던 문제 — 총점 카드가 먼저, 경고는 그 아래 한 덩어리
    _, html = render(result)
    assert html.index('class="hero') < html.index('class="notice')
    assert '<span class="hero-score">62.0</span>' in html


def test_notices_fold_into_one_details(result):
    _, html = render(result)
    assert html.count('class="notice') == 1
    notice = re.search(r'<details class="notice">(.*?)</details>', html, re.S).group(1)
    assert "보정 안 됨" in notice and "진단 지표" in notice
    md, _ = render(result)
    assert "보정 안 됨" in md  # md에서는 그대로 남는다


def test_hero_shows_top_fix(result):
    _, html = render(result)
    hero = re.search(r'<section class="hero[^"]*">(.*?)</section>', html, re.S).group(1)
    top = result["fix_priority"][0]
    assert top["name"] in hero and f"+{top['gain']:g}" in hero


def test_bars_scale_with_points_and_color_by_ratio():
    html = to_html([{"type": "bars", "rows": [{"label": "큰 항목", "value": 2, "max": 20},
                                              {"label": "작은 항목", "value": 4.5, "max": 5}],
                     "scale": True}], "T")
    # 트랙 길이가 배점에 비례한다 — 5점 항목이 20점 항목과 같은 길이로 보이지 않게
    assert re.search(r'class="track" style="width:100\.0%"', html)
    assert re.search(r'class="track" style="width:25\.0%"', html)
    assert 'class="fill lv-low"' in html and 'class="fill lv-high"' in html


def test_fix_cards(result):
    _, html = render(result)
    assert html.count('class="fix"') == len(result["fix_priority"])
    md, _ = render(result)
    assert "## 고칠 것 Top 5" in md


def test_persona_titles_replace_ids(result, contest_dir):
    labels = contest_labels(contest_dir / "runs" / "x")
    assert labels["personas"]["developer"] == "개발자 심사위원"
    assert labels["items"]["feasibility"] == "실현 가능성"
    md, html = render(result, labels)
    assert "개발자 심사위원" in md and "개발자 심사위원" in html


def test_grill_uses_labels_and_cards(contest_dir):
    labels = contest_labels(contest_dir / "runs" / "x")
    md, html = render(GRILL, labels)
    assert "개발자 심사위원" in html and "실현 가능성" in html
    assert 'class="qa' in html
    assert "## 질문과 판정" in md


def test_brand_print_and_still_self_contained(result):
    _, html = render(result)
    assert "PRO-Judge" in html and "@media print" in html
    assert "<script" not in html and not re.search(r'(src|href)="https?://', html)


def test_markdown_handles_new_blocks():
    md = to_markdown([{"type": "hero", "score": 31.7, "max": 100, "caption": "c", "sub": ["a"], "top_fix": None},
                      {"type": "notice", "label": "읽는 법", "items": [{"label": "L", "text": "T"}]},
                      {"type": "fixes", "items": []}])
    assert "**31.7** / 100" in md and "**L** T" in md and "(없음)" in md


def test_dashboard_trend(contest_dir):
    for day, gate in ((8, 5), (9, 8)):
        run = new_run(contest_dir, "score", datetime(2026, 10, day, 9, 0))
        write_json(run / "result.json", aggregate(load_yaml(contest_dir / "rubric.yaml"),
                                                  base_results(gate=gate), run=run.name))
    _, html = render_dashboard.build(contest_dir)
    hero = re.search(r'<section class="hero[^"]*">(.*?)</section>', html, re.S).group(1)
    assert "62.0" in hero and "+9.3" in hero
    assert "PRO-Judge" in html
