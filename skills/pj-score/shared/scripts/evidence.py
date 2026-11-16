#!/usr/bin/env python3
"""근거 장부(evidence.yaml) 검사와 빈칸 계산.

채점 전에 무엇을 봤고 무엇을 못 봤는지를 남긴다. 빈칸은 점수표의 evidence_types(대상 모드)나
고정 주제 목록(대회 모드)에서 기계적으로 계산한다 — 같은 장부·같은 점수표면 같은 빈칸이 나온다.

사용:
  evidence.py check <evidence.yaml> [--rubric <rubric.yaml>]
  evidence.py gaps  <evidence.yaml> [--rubric <rubric.yaml>] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import InputError, load_yaml, run_cli  # noqa: E402

SCOPES = ("target", "contest")
KINDS = ("file", "repo", "url", "web", "user", "video")
TRUSTS = ("official", "reported", "self", "user")
STATUSES = ("ok", "partial", "failed")
EVIDENCE_TYPES = ("numbers", "proper-nouns", "demo", "field-test", "quote", "observation")
# 대회 모드에서 반드시 확인할 주제 — 하나라도 비면 점수표나 제출 계획이 공고와 어긋날 수 있다
CONTEST_TOPICS = {
    "announcement": "공고 원문",
    "criteria": "심사 항목·배점",
    "schedule": "일정",
    "submission": "제출물·분량·형식 요건",
    "penalties": "감점·실격·제외 규정",
    "judges": "심사위원·평가자 구성",
    "past-winners": "역대 수상작",
}


def _items(rubric) -> dict:
    return {i["id"]: i for i in (rubric or {}).get("items", []) if isinstance(i, dict) and "id" in i}


def check(ledger, rubric) -> list:
    if not isinstance(ledger, dict):
        return ["장부가 매핑(YAML 객체)이 아니다"]
    errs = []
    scope = ledger.get("scope")
    if scope not in SCOPES:
        errs.append(f"scope는 {'|'.join(SCOPES)} 중 하나 (지금: {scope!r})")
    ids = []
    for n, s in enumerate(ledger.get("sources") or []):
        where = f"sources[{n}]"
        if not isinstance(s, dict):
            errs.append(f"{where}: 매핑이 아니다")
            continue
        sid = s.get("id")
        if not sid:
            errs.append(f"{where}: id 없음")
        elif sid in ids:
            errs.append(f"{where}: id '{sid}' 중복")
        ids.append(sid)
        for key, allowed in (("kind", KINDS), ("trust", TRUSTS), ("status", STATUSES)):
            if s.get(key) not in allowed:
                errs.append(f"{where}: {key}는 {'|'.join(allowed)} 중 하나 (지금: {s.get(key)!r})")
        if not s.get("ref"):
            errs.append(f"{where}: ref(어디서) 없음")
    valid_items = set(_items(rubric)) | {"*"} if scope == "target" else set(CONTEST_TOPICS)
    for section in ("evidence", "absent"):
        for n, e in enumerate(ledger.get(section) or []):
            where = f"{section}[{n}]"
            if not isinstance(e, dict):
                errs.append(f"{where}: 매핑이 아니다")
                continue
            if e.get("source") not in ids:
                errs.append(f"{where}: 없는 source '{e.get('source')}'")
            if e.get("type") not in EVIDENCE_TYPES:
                errs.append(f"{where}: type은 {'|'.join(EVIDENCE_TYPES)} 중 하나 (지금: {e.get('type')!r})")
            item = e.get("item")
            # 대상 모드에서 점수표를 안 주면 항목 id는 확인할 수 없다
            if (scope == "contest" or rubric is not None) and item not in valid_items:
                errs.append(f"{where}: 알 수 없는 item '{item}'")
            if not e.get("text"):
                errs.append(f"{where}: text 없음")
    return errs


def _covered(ledger) -> set:
    """실패하지 않은 출처의 근거와 '없음 확인'만 빈칸을 채운다."""
    usable = {s.get("id") for s in ledger.get("sources") or [] if s.get("status") != "failed"}
    got = set()
    for section in ("evidence", "absent"):
        for e in ledger.get(section) or []:
            if e.get("source") in usable:
                got.add((e.get("item"), e.get("type")))
    return got


def gaps(ledger, rubric) -> list:
    covered = _covered(ledger)
    if ledger.get("scope") == "contest":
        items_done = {item for item, _ in covered}
        return [{"item": t, "type": None, "name": name} for t, name in CONTEST_TOPICS.items() if t not in items_done]
    out = []
    for iid, item in _items(rubric).items():
        for etype in item.get("evidence_types") or []:
            if (iid, etype) not in covered and ("*", etype) not in covered:
                out.append({"item": iid, "type": etype, "name": item.get("name", iid)})
    return out


def summary(ledger, rubric) -> dict:
    """합산 결과(result.json)에 싣는 요약 — 보고서의 '확인한 자료와 빈칸' 절이 쓴다."""
    names = {iid: i.get("name", iid) for iid, i in _items(rubric).items()}
    names.update(CONTEST_TOPICS if ledger.get("scope") == "contest" else {})
    return {
        "scope": ledger.get("scope"),
        "sources": [{k: s.get(k) for k in ("id", "kind", "ref", "how", "trust", "status", "note")}
                    for s in ledger.get("sources") or []],
        "gaps": gaps(ledger, rubric),
        "absent": [{"item": a.get("item"), "type": a.get("type"), "name": names.get(a.get("item"), a.get("item")),
                    "text": a.get("text")} for a in ledger.get("absent") or []],
    }


def load_checked(path: Path, rubric) -> dict:
    ledger = load_yaml(path)
    errs = check(ledger, rubric)
    if errs:
        raise InputError(f"{path} 결함:\n- " + "\n- ".join(errs))
    return ledger


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="근거 장부 검사·빈칸 계산")
    ap.add_argument("command", choices=["check", "gaps"])
    ap.add_argument("ledger")
    ap.add_argument("--rubric")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    ledger = load_yaml(Path(args.ledger))
    rubric = load_yaml(Path(args.rubric)) if args.rubric else None
    errs = check(ledger, rubric)
    if args.command == "check":
        for e in errs:
            print(f"- {e}")
        print("OK" if not errs else f"결함 {len(errs)}개")
        return 1 if errs else 0
    if errs:
        raise InputError("장부 결함 — check로 먼저 고칠 것:\n- " + "\n- ".join(errs))
    found = gaps(ledger, rubric)
    if args.json:
        print(json.dumps(found, ensure_ascii=False, indent=2))
    else:
        for g in found:
            print(f"- {g['item']} ({g['name']})" + (f": {g['type']}" if g["type"] else ""))
        print(f"빈칸 {len(found)}개")
    return 0


if __name__ == "__main__":
    run_cli(main)
