#!/usr/bin/env python3
"""대회 폴더와 런 폴더를 만든다.

docs/pro-judge/는 심사 전략·점수가 공개 레포에 올라가지 않게 '*' gitignore로 감싼다.
사용:
  python3 contest_dirs.py init <레포 루트> "<대회 이름>"
  python3 contest_dirs.py new-run <대회 폴더> <score|grill|ideas>
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import RUN_KINDS, InputError, run_cli  # noqa: E402


def slugify(name: str) -> str:
    s = re.sub(r'[\\/:*?"<>|]+', "-", name.strip())
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-.")
    if not s:
        raise InputError("대회 이름이 비어 있음")
    return s


def _tracked_files(repo_root: Path, base: Path) -> list:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--", str(base.relative_to(repo_root))],
            capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return []  # git 레포가 아니면 추적 파일도 없다
    return [line for line in out.splitlines() if line]


def init_contest(repo_root: Path, name: str):
    repo_root = Path(repo_root).resolve()
    base = repo_root / "docs" / "pro-judge"
    notices = []
    tracked = _tracked_files(repo_root, base)
    if tracked:
        # 이미 공개된 파일은 gitignore로 숨겨지지 않는다 — 지우는 판단은 사용자 몫
        notices.append(f"docs/pro-judge/ 아래 git이 이미 추적 중인 파일 {len(tracked)}개가 있음 "
                       f"(건드리지 않음): {', '.join(tracked[:5])}")
    base.mkdir(parents=True, exist_ok=True)
    gitignore = base / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n", encoding="utf-8")
    contest = base / slugify(name)
    (contest / "personas").mkdir(parents=True, exist_ok=True)
    (contest / "runs").mkdir(exist_ok=True)
    return contest, notices


def new_run(contest_dir: Path, kind: str, now: datetime | None = None) -> Path:
    if kind not in RUN_KINDS:
        raise InputError(f"런 종류는 {'/'.join(RUN_KINDS)} 중 하나 (현재: {kind!r})")
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M")
    runs = Path(contest_dir) / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        path = runs / (f"{stamp}_{kind}" if n == 1 else f"{stamp}_{kind}-{n}")
        try:
            path.mkdir()  # exist_ok 없이 만들어야 동시 실행에서도 겹치지 않는다
            return path
        except FileExistsError:
            n += 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="대회·런 폴더 생성")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("repo_root")
    p_init.add_argument("name")
    p_run = sub.add_parser("new-run")
    p_run.add_argument("contest_dir")
    p_run.add_argument("kind")
    args = ap.parse_args(argv)
    if args.cmd == "init":
        contest, notices = init_contest(Path(args.repo_root), args.name)
        for n in notices:
            print(f"알림: {n}")
        print(contest)
    else:
        print(new_run(Path(args.contest_dir), args.kind))
    return 0


if __name__ == "__main__":
    run_cli(main)
