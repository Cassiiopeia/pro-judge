#!/usr/bin/env python3
"""shared/를 각 skill 폴더의 shared/로 복사한다.

vercel-labs/skills CLI는 skill 폴더 하나만 복사하므로(installer.ts copyDirectory) 레포 루트의
shared/는 설치되지 않는다. 그래서 사본을 각 skill에 넣어 커밋하고, 테스트가 원본과 같은지 지킨다.
사본은 생성물이다 — 직접 고치지 말고 shared/를 고친 뒤 이 스크립트를 돌린다.
사용: python3 tools/sync_shared.py [--check]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET_SKILLS = ("pro-judge-setup", "pro-judge-ideas", "pro-judge-score", "pro-judge-grill", "pro-judge-gather")
IGNORE_DIRS = {"__pycache__", ".pytest_cache"}


def _files(base: Path) -> dict:
    if not base.is_dir():
        return {}
    return {p.relative_to(base).as_posix(): p.read_bytes()
            for p in base.rglob("*")
            if p.is_file() and not IGNORE_DIRS & set(p.parts) and p.suffix != ".pyc"}


def sync(root: Path = ROOT) -> None:
    src = root / "shared"
    for skill in TARGET_SKILLS:
        dst = root / "skills" / skill / "shared"
        if dst.exists():
            shutil.rmtree(dst)  # 생성물만 지운다 — skill 본문은 건드리지 않는다
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*IGNORE_DIRS, "*.pyc"))


def check(root: Path = ROOT) -> list:
    src = _files(root / "shared")
    diffs = []
    for skill in TARGET_SKILLS:
        dst = _files(root / "skills" / skill / "shared")
        for rel in sorted(set(src) | set(dst)):
            if src.get(rel) != dst.get(rel):
                diffs.append(f"skills/{skill}/shared/{rel}")
    return diffs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="shared/ → skills/*/shared/ 동기화")
    ap.add_argument("--check", action="store_true", help="복사하지 않고 차이만 확인")
    args = ap.parse_args(argv)
    if args.check:
        diffs = check()
        for d in diffs:
            print(f"다름: {d}")
        return 1 if diffs else 0
    sync()
    print("동기화 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
