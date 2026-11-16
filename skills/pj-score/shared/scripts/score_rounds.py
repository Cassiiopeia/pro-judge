#!/usr/bin/env python3
"""채점 한 회차 파일 검사와 페르소나 파일 합치기.

서브에이전트가 회차 JSON을 채팅으로 돌려주면 오케스트레이터가 다시 옮겨 적다가 잘리거나 바뀐다.
그래서 서브에이전트가 자기 회차를 파일로 직접 쓰고 check로 검사하며, 오케스트레이터는 merge만 한다.
사용:
  python3 score_rounds.py check <런 폴더> <persona> <회차 파일>
  python3 score_rounds.py merge <런 폴더>
회차 파일: <런 폴더>/rounds/<persona>-<회차 번호>.json (persona-output.md "한 회차 JSON" + 선택 키 "model")
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate import _find_contest_dir, _normalize_persona  # noqa: E402
from _common import InputError, load_json, load_yaml, run_cli, write_json  # noqa: E402

ROUNDS_DIR = "rounds"
# 회차 파일 이름: <persona>-<번호>.json
ROUND_FILE = re.compile(r"^(?P<persona>.+)-(?P<number>\d+)\.json$")


def _persona_scope(rubric: dict, persona: str) -> set:
    """페르소나가 속한 평가자 그룹에 배점이 있는 항목 id"""
    groups = {g["id"] for g in rubric["evaluator_groups"] if persona in g["personas"]}
    if not groups:
        raise InputError(f"rubric에 없는 페르소나: {persona}")
    return {it["id"] for it in rubric["items"] if set(it["points"]) & groups}


def check_round(run_dir: Path, persona: str, round_file: Path) -> list:
    """회차 1개 검사 > 오류 목록 (빈 목록이면 합산에 쓸 수 있음)"""
    rubric = load_yaml(_find_contest_dir(run_dir) / "rubric.yaml")
    round_data = load_json(round_file)
    _, errors, _ = _normalize_persona({"persona": persona, "runs": [round_data]}, rubric,
                                      scope=_persona_scope(rubric, persona))
    return errors


def merge_rounds(run_dir: Path) -> dict:
    """rounds/<persona>-<n>.json > <런 폴더>/<persona>.json (깨진 회차는 빼고 이름을 돌려줌)"""
    rounds_dir = run_dir / ROUNDS_DIR
    if not rounds_dir.is_dir():
        raise InputError(f"{rounds_dir} 없음 — 서브에이전트가 회차 파일을 쓰지 않았음")
    by_persona: dict = {}
    for f in sorted(rounds_dir.glob("*.json"), key=lambda p: p.name):
        m = ROUND_FILE.match(f.name)
        if m:
            by_persona.setdefault(m["persona"], []).append((int(m["number"]), f))
    if not by_persona:
        raise InputError(f"{rounds_dir}에 <persona>-<번호>.json 파일이 없음")
    written, skipped = [], []
    for persona, files in sorted(by_persona.items()):
        runs, model = [], None
        for _, f in sorted(files):
            try:
                round_data = load_json(f)
            except InputError:
                skipped.append(f.name)  # 깨진 회차는 뺀다 (persona-output.md 규칙)
                continue
            round_model = round_data.pop("model", None)
            model = model or round_model
            runs.append(round_data)
        if runs:
            write_json(run_dir / f"{persona}.json",
                       {"persona": persona, "model": model, "independent": True, "runs": runs})
            written.append(persona)
    return {"written": written, "skipped": skipped}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="채점 회차 파일 검사·합치기")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_check = sub.add_parser("check")
    p_check.add_argument("run_dir")
    p_check.add_argument("persona")
    p_check.add_argument("round_file")
    p_merge = sub.add_parser("merge")
    p_merge.add_argument("run_dir")
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    if args.cmd == "check":
        errors = check_round(run_dir, args.persona, Path(args.round_file))
        if errors:
            raise InputError("회차 형식 오류 — 고쳐서 같은 파일에 다시 쓰고 다시 검사:\n- " + "\n- ".join(errors))
        print(f"통과: {args.round_file}")
        return 0
    merged = merge_rounds(run_dir)
    for name in merged["skipped"]:
        print(f"제외: {name} (JSON 문법 오류)")
    for persona in merged["written"]:
        print(run_dir / f"{persona}.json")
    return 0


if __name__ == "__main__":
    run_cli(main)
