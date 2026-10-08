#!/usr/bin/env python3
"""대회 대시보드(index.html)와 회차별 총점 추이(history.md)를 만든다.

사용: python3 render_dashboard.py <대회 폴더>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import InputError, list_runs, load_json, load_yaml, run_cli  # noqa: E402
from report_blocks import to_html, to_markdown  # noqa: E402

RECENT_COLUMNS = 5
RECENT_LINKS = 10
KIND_LABEL = {"score": "채점", "grill": "질의응답", "ideas": "아이디어"}


def _contest_name(contest_dir: Path) -> str:
    rubric_path = contest_dir / "rubric.yaml"
    rubric = load_yaml(rubric_path) if rubric_path.is_file() else None
    return rubric.get("contest") if isinstance(rubric, dict) and rubric.get("contest") else contest_dir.name


def build(contest_dir: Path):
    contest_dir = Path(contest_dir)
    name = _contest_name(contest_dir)
    scored = [(p, load_json(p / "result.json")) for p in list_runs(contest_dir, "score") if (p / "result.json").is_file()]
    scored = [(p, r) for p, r in scored if not r.get("calibration")]  # 보정용 채점(남의 작품)은 내 추이가 아니다

    rows, prev = [], None
    for p, r in scored:
        rng = f"{r['total_range'][0]:.1f} ~ {r['total_range'][1]:.1f}" if r["total_range"] else "-"
        delta = "-" if prev is None else f"{r['total'] - prev:+.1f}"
        rows.append([p.name, r.get("target") or "-", f"{r['total']:.1f}", rng, delta])
        prev = r["total"]
    history_blocks = [{"type": "h1", "text": f"{name} 회차별 총점"}]
    if rows:
        history_blocks.append({"type": "table", "headers": ["회차", "대상", "총점", "범위", "변화"], "rows": rows})
    else:
        history_blocks.append({"type": "p", "text": "아직 채점 회차가 없음"})

    recent = scored[-RECENT_COLUMNS:]
    item_rows = []
    if recent:
        for item in recent[-1][1]["items"]:
            cells = []
            for _, r in recent:
                hit = next((i for i in r["items"] if i["id"] == item["id"]), None)
                cells.append(f"{hit['earned']:g}" if hit else "-")
            item_rows.append([f"{item['name']} ({item['points_total']:g})", *cells])
    links = [{"text": f"{p.name} {KIND_LABEL[p.name.split('_')[1].split('-')[0]]}",
              "href": f"runs/{p.name}/report.html"}
             for p in reversed(list_runs(contest_dir)) if (p / "report.html").is_file()][:RECENT_LINKS]

    dash = [{"type": "h1", "text": f"{name} 대시보드"},
            {"type": "h2", "text": "총점 추이"},
            ({"type": "bars", "rows": [{"label": p.name, "value": r["total"], "max": 100} for p, r in scored]}
             if scored else {"type": "p", "text": "아직 채점 회차가 없음"}),
            {"type": "h2", "text": "항목별 변화 (최근 회차)"},
            {"type": "table", "headers": ["항목 (배점)", *[p.name for p, _ in recent]], "rows": item_rows},
            {"type": "h2", "text": "최근 보고서"},
            {"type": "links", "items": links}]
    return to_markdown(history_blocks), to_html(dash, f"{name} 대시보드")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="대회 대시보드 생성")
    ap.add_argument("contest_dir")
    args = ap.parse_args(argv)
    contest_dir = Path(args.contest_dir)
    if not contest_dir.is_dir():
        raise InputError(f"대회 폴더 없음: {contest_dir}")
    history, html = build(contest_dir)
    (contest_dir / "history.md").write_text(history, encoding="utf-8")
    (contest_dir / "index.html").write_text(html, encoding="utf-8")
    print(contest_dir / "index.html")
    return 0


if __name__ == "__main__":
    run_cli(main)
