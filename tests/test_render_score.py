import re

import pytest

from _common import load_yaml, write_json
from aggregate import aggregate
import render_report
from render_report import render
from report_blocks import to_html, to_markdown
from factories import base_results


@pytest.fixture
def result(contest_dir):
    r = aggregate(load_yaml(contest_dir / "rubric.yaml"), base_results(),
                  created_at="2026-10-08T14:05", target="발표자료 v1", run="20261008-1405_score")
    r["narrative"]["overall"] = "실현 가능성이 가장 약하다."
    return r


def test_score_markdown_sections(result):
    md, _ = render(result)
    for text in ("# 테스트-해커톤 채점 보고서", "62.0", "## 고칠 것 Top 5", "## 편차 경보",
                 "## 항목별", "실현 가능성", "## 총평", "실현 가능성이 가장 약하다.", "## 부록", "보정 안 됨"):
        assert text in md, text


def test_flags_in_report(result):
    result["independent"] = False
    result["participation"] = {"expected": 3, "succeeded": 2}
    result["missing_personas"] = ["citizen"]
    result["no_official_criteria"] = True
    result["gate"]["warning"] = True
    result["total_range"] = [55.0, 66.0]
    result["previous"] = {"run": "x", "total": 60.0, "delta": 2.0}
    md, _ = render(result)
    for text in ("독립 실행 아님", "3명 중 2명", "공식 기준 없음", "취지 경보", "55.0 ~ 66.0", "+2.0"):
        assert text in md, text


def test_html_self_contained(result):
    _, html = render(result)
    assert html.startswith("<!doctype html>")
    assert 'class="bars"' in html and "<style>" in html
    assert not re.search(r'(src|href)="https?://', html)
    assert "<script" not in html


def test_escaping(result):
    result["narrative"]["overall"] = "<script>alert(1)</script>"
    result["items"][0]["quotes"] = ["A | B\n둘째 줄"]
    md, html = render(result)
    assert "<script>alert" not in html and "&lt;script&gt;" in html
    row = next(line for line in md.splitlines() if "A \\| B" in line)
    assert "둘째 줄" in row  # 줄바꿈이 표 행을 끊지 않는다


def test_blocks_roundtrip():
    blocks = [{"type": "h1", "text": "T"}, {"type": "list", "items": []},
              {"type": "bars", "rows": [{"label": "a", "value": 5, "max": 10}]},
              {"type": "links", "items": [{"text": "r", "href": "runs/x/report.html"}]}]
    md = to_markdown(blocks)
    assert "- (없음)" in md and "5 / 10" in md and "[r](runs/x/report.html)" in md
    assert 'href="runs/x/report.html"' in to_html(blocks, "T")


def test_bars_do_not_shrink_on_phone():
    # SVG viewBox는 폭 390px에서 통째로 줄어 글자가 6px이 된다 — 글자 크기가 고정된 HTML 행이어야 한다
    html = to_html([{"type": "bars", "rows": [{"label": "실현 <가능성>", "value": 32, "max": 55}]}], "T")
    assert "<svg" not in html
    assert 'class="bar-row"' in html and "실현 &lt;가능성&gt;" in html
    assert "width:58.2%" in html and "32 / 55" in html


def test_bar_tracks_align_across_rows():
    # 행마다 grid가 따로라 점수 열이 auto면 '2 / 20'과 '4.75 / 15' 행의 막대 길이가 달라진다
    html = to_html([{"type": "bars", "rows": [{"label": "a", "value": 2, "max": 20}]}], "T")
    row_css = re.search(r"\.bar-row\{[^}]*grid-template-columns:([^;}]*)", html).group(1)
    assert "auto" not in row_css


def test_cli(tmp_path, result):
    write_json(tmp_path / "result.json", result)
    assert render_report.main([str(tmp_path)]) == 0
    assert (tmp_path / "report.md").is_file() and (tmp_path / "report.html").is_file()
