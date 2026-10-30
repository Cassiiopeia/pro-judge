#!/usr/bin/env python3
"""질의응답 재료 고르기: 최근 채점 회차 > 약한 항목·상한·편차·공통 약점

에이전트가 "가장 약한 항목"을 매번 손으로 계산하면 실행마다 달라진다. 같은 결과면 같은 목록이 나오게 여기서 정한다.
사용: python3 grill_targets.py <대회 폴더>   (출력: JSON)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import InputError, list_runs, load_json, run_cli  # noqa: E402

WEAK_ITEM_COUNT = 3


def find_latest_score_run(contest_dir: Path):
    """보정용(calibration)이 아닌 가장 최근 score 회차 > (폴더, result) | None"""
    for run_dir in reversed(list_runs(contest_dir, "score")):
        result_file = run_dir / "result.json"
        if result_file.is_file():
            result = load_json(result_file)
            if not result.get("calibration"):
                return run_dir, result
    return None


def pick_weak_items(items: list, count: int = WEAK_ITEM_COUNT) -> list:
    """득점률 낮은 순 (같으면 배점 큰 항목 > id 순) 상위 count개"""
    scored = [it for it in items if it.get("points_total")]
    ranked = sorted(scored, key=lambda it: (it["earned"] / it["points_total"], -it["points_total"], it["id"]))
    return [{"id": it["id"], "name": it.get("name", it["id"]), "earned": it["earned"],
             "points_total": it["points_total"], "rate": round(it["earned"] / it["points_total"], 3)}
            for it in ranked[:count]]


def select_targets(contest_dir: Path) -> dict:
    found = find_latest_score_run(contest_dir)
    if found is None:
        raise InputError("채점 결과 없음 — 질문은 채점 결과의 약점에서 나온다. pro-judge-score부터")
    run_dir, result = found
    items = result.get("items") or []
    return {
        "run": run_dir.name,
        "weak_items": pick_weak_items(items),
        "capped_items": [{"id": it["id"], "caps": it["caps"], "unlock_hints": it.get("unlock_hints") or []}
                         for it in items if it.get("caps")],
        "deviation_alerts": result.get("deviation_alerts") or [],
        "consensus_gaps": result.get("consensus_gaps") or [],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="질의응답 재료 고르기")
    ap.add_argument("contest_dir")
    args = ap.parse_args(argv)
    print(json.dumps(select_targets(Path(args.contest_dir).resolve()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    run_cli(main)
