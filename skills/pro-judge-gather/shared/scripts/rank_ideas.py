#!/usr/bin/env python3
"""아이디어별 합산 결과를 모아 순위표를 만든다.

사용: python3 rank_ideas.py <아이디어 런 폴더>
  <런>/ideas.json 과 <런>/<아이디어 id>/result.json 을 읽어 <런>/result.json 을 쓴다.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import InputError, load_json, run_cli, write_json  # noqa: E402

COST_LEVELS = ("low", "mid", "high")


def rank_ideas(meta: list, results: dict, created_at: str = "") -> dict:
    if not isinstance(meta, list) or not meta:
        raise InputError("ideas.json: 아이디어 목록이 비어 있음")
    ideas = []
    for m in meta:
        iid = m.get("id") if isinstance(m, dict) else None
        if not iid:
            raise InputError("ideas.json: id 없는 아이디어가 있음")
        if m.get("cost_level") not in COST_LEVELS:
            raise InputError(f"ideas.json[{iid}]: cost_level은 {'/'.join(COST_LEVELS)} 중 하나")
        if iid not in results:
            raise InputError(f"{iid}: 합산 결과(result.json)가 없음 — aggregate.py부터 실행")
        r = results[iid]
        top = r["fix_priority"][:3]
        ideas.append({
            "id": iid,
            "title": m.get("title") or iid,
            "total": r["total"],
            "total_range": r["total_range"],
            "gate": r["gate"],
            "blockers": [f"{f['name']} — {', '.join(f['caps']) if f['caps'] else '상한 없음, 근거 부족'}"
                         for f in top],
            "fix_priority": top,
            "cost": {"level": m["cost_level"], "note": m.get("cost_note") or ""},
        })
    # 취지를 벗어난 아이디어는 점수와 무관하게 아래로 — 완성도가 취지 미달을 만회해 주지 않는다
    ideas.sort(key=lambda i: (i["gate"]["warning"], -i["total"]))
    for n, idea in enumerate(ideas, 1):
        idea["rank"] = n
    return {"kind": "ideas", "contest": results[ideas[0]["id"]]["contest"],
            "created_at": created_at, "ideas": ideas, "narrative": {"overall": ""}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="아이디어 순위")
    ap.add_argument("run_dir")
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        raise InputError(f"런 폴더 없음: {run_dir}")
    meta = load_json(run_dir / "ideas.json")
    results = {p.name: load_json(p / "result.json")
               for p in sorted(run_dir.iterdir()) if p.is_dir() and (p / "result.json").is_file()}
    out = rank_ideas(meta, results, datetime.now().isoformat(timespec="minutes"))
    write_json(run_dir / "result.json", out)
    for i in out["ideas"]:
        print(f"{i['rank']}. {i['title']} {i['total']}" + (" (취지 경보)" if i["gate"]["warning"] else ""))
    return 0


if __name__ == "__main__":
    run_cli(main)
