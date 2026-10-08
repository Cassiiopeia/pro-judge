#!/usr/bin/env python3
"""저장소에서 채점 근거가 되는 사실을 뽑는다. 코드·훅은 실행하지 않고 파일과 git 이력만 읽는다.

출력은 사람이 읽는 텍스트다. <런>/target/에 저장하면 합산이 인용을 이 글과 대조한다.
fork 저장소는 원본(--upstream)을 주면 원본에 없는 팀 커밋만 따로 센다 — 주지 않으면 원본 커밋이 섞인다.

사용: repo_facts.py <저장소> [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--upstream <경로|URL>] [--out <파일>]
"""
from __future__ import annotations

import argparse
import collections
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import InputError, run_cli  # noqa: E402

README_LIMIT = 12000
UPSTREAM_REMOTE = "upstream-pj"


def _git(repo: Path, *args, check=False) -> str:
    # 저장소의 훅·설정이 끼어들지 않게 훅 경로를 비운다 — 남의 저장소를 읽기만 한다
    r = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else f"git {args[0]} 실패")
    return r.stdout


def _authors(log: str) -> collections.Counter:
    return collections.Counter(line.split("|", 1)[1] for line in log.splitlines() if "|" in line)


def _upstream_section(repo: Path, upstream: str) -> list:
    try:
        if UPSTREAM_REMOTE in _git(repo, "remote").split():
            _git(repo, "remote", "set-url", UPSTREAM_REMOTE, upstream, check=True)
        else:
            _git(repo, "remote", "add", UPSTREAM_REMOTE, upstream, check=True)
        _git(repo, "fetch", "-q", "--filter=blob:none", UPSTREAM_REMOTE, "HEAD", check=True)
        log = _git(repo, "log", "FETCH_HEAD..HEAD", "--format=%ad|%an", "--date=short", check=True)
    except RuntimeError as e:
        return [f"- fork 원본 비교 실패: {e}"]
    authors = _authors(log)
    total = sum(authors.values())
    return [f"- 원본 대비 팀 커밋 {total}개, 작성자 {len(authors)}명: "
            + ", ".join(f"{a} {c}" for a, c in authors.most_common(8)) + f" (원본: {upstream})"]


def facts(repo, since=None, until=None, upstream=None) -> str:
    repo = Path(repo)
    if _git(repo, "rev-parse", "--is-inside-work-tree").strip() != "true":
        raise InputError(f"git 저장소가 아님: {repo}")
    files = _git(repo, "ls-files").splitlines()
    lines = [f"# 저장소 사실: {repo.name}", ""]
    total = _git(repo, "rev-list", "--count", "HEAD").strip() or "0"
    first = _git(repo, "log", "--reverse", "--format=%ad", "--date=short").splitlines()[:1]
    lines.append(f"- 전체 커밋 {total}개, 첫 커밋 {first[0] if first else '-'}, 파일 {len(files)}개")

    period = []
    if since:
        period.append(f"--since={since}")
    if until:
        period.append(f"--until={until} 23:59")
    log = _git(repo, "log", *period, "--format=%ad|%an", "--date=short")
    authors = _authors(log)
    months = collections.Counter(line[:7] for line in log.splitlines() if "|" in line)
    lines.append(f"- 기간 커밋 {sum(authors.values())}개, 작성자 {len(authors)}명 ({since or '처음'}~{until or '지금'}): "
                 + ", ".join(f"{a} {c}" for a, c in authors.most_common(8)))
    lines.append("- 월별 커밋: " + (", ".join(f"{m} {c}" for m, c in sorted(months.items())) or "없음"))
    if upstream:
        lines += _upstream_section(repo, upstream)

    def named(*prefixes):
        return [f for f in files if f.lower().split("/")[-1].startswith(prefixes)]

    lic = named("license", "copying")
    lines.append(f"- LICENSE: {', '.join(lic[:3]) or '없음'}")
    lines.append(f"- CONTRIBUTING: {', '.join(named('contributing')[:2]) or '없음'} · "
                 f"CODE_OF_CONDUCT: {', '.join(named('code_of_conduct')[:1]) or '없음'}")
    tests = [f for f in files if "/test" in "/" + f.lower() or ".test." in f.lower() or "_test." in f.lower()]
    lines.append(f"- 테스트로 보이는 파일 {len(tests)}개")
    ci = [f for f in files if f.startswith(".github/workflows/")]
    lines.append(f"- CI 워크플로우: {', '.join(ci[:5]) or '없음'}")
    if lic:
        lines += ["", f"## {lic[0]} (앞부분)", (repo / lic[0]).read_text(errors="replace")[:400]]
    top = collections.Counter(f.split("/")[0] + ("/" if "/" in f else "") for f in files)
    lines += ["", "## 최상위 구조 (파일 수)"] + [f"- {k} {v}" for k, v in sorted(top.items())[:60]]
    readmes = [f for f in files if f.lower().split("/")[-1].startswith("readme") and f.count("/") <= 1][:3]
    docs = [f for f in files if f.lower().endswith(".md") and f.count("/") <= 1 and f not in readmes
            and not f.lower().startswith(("license", "changelog"))][:4]
    for f in readmes + docs:
        lines += ["", f"## 파일 {f}", (repo / f).read_text(errors="replace")[:README_LIMIT]]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="저장소 사실 추출 (실행 없음)")
    ap.add_argument("repo")
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--upstream", help="fork 원본 저장소 경로나 URL")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    text = facts(args.repo, args.since, args.until, args.upstream)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    run_cli(main)
