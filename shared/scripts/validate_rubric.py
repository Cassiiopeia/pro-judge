#!/usr/bin/env python3
"""rubric.yaml 검사기.

점수표가 채점 객관성의 기반이라, 사람이 놓치기 쉬운 결함(빈 앵커, 근거 없는 추정, 배점 불일치)을
에이전트가 통과할 때까지 고치게 만든다.
사용: python3 validate_rubric.py <대회 폴더>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import load_yaml, run_cli  # noqa: E402

SOURCES = {"official", "inferred"}
CONTEST_TYPES = {"open-source", "disability", "social-impact", "startup", "public-data", "ai-tech"}
EVIDENCE_TYPES = {"numbers", "proper-nouns", "demo", "field-test", "quote", "observation"}
COMMON_CAPS = {"intent-not-evidence", "no-specifics", "claim-not-verified",
               "claim-failed", "quote-for-seven", "length-neutral"}
# 관찰할 수 없는 평가어 — 앵커에 쓰면 채점자마다 해석이 갈린다
BANNED_ANCHOR_WORDS = ("잘했", "잘 했", "잘함", "충분", "적절", "우수", "훌륭",
                       "good", "sufficient", "adequate", "excellent")
ANCHOR_KEYS = ("0", "5", "10")


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_int_in(v, lo: int, hi: int) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi


def _text(v) -> str:
    return str(v).strip() if v is not None else ""


def _as_list(v, where, errors) -> list:
    if v is None:
        return []
    if not isinstance(v, list):
        errors.append(f"{where}: 목록이어야 함")
        return []
    return v


def _as_dict(v, where, errors) -> dict:
    if v is None:
        return {}
    if not isinstance(v, dict):
        errors.append(f"{where}: 매핑이어야 함")
        return {}
    return v


def _check_source(node: dict, where: str, errors: list, allowed=SOURCES) -> None:
    src = node.get("source")
    if src not in allowed:
        errors.append(f"{where}: source는 {'/'.join(sorted(allowed))} 중 하나여야 함 (현재: {src!r})")
    elif src == "inferred" and not _text(node.get("why")):
        errors.append(f"{where}: inferred에는 why(근거 한 줄)가 필요함")


def _check_gate(gate: dict, errors: list) -> None:
    _check_source(gate, "gate", errors, SOURCES | {"none"})
    if gate.get("source") != "official":
        return
    bands = _as_list(gate.get("bands"), "gate.bands", errors)
    if not bands:
        errors.append("gate.bands: source가 official이면 구간이 필요함")
        return
    mins = []
    for i, band in enumerate(bands):
        where = f"gate.bands[{i}]"
        if not isinstance(band, dict):
            errors.append(f"{where}: 매핑이어야 함")
            continue
        if _is_int_in(band.get("min"), 0, 10):
            mins.append(band["min"])
        else:
            errors.append(f"{where}.min: 0~10 정수여야 함")
        mult = band.get("multiplier")
        if not (_is_num(mult) and 0 < mult <= 1):
            errors.append(f"{where}.multiplier: 0 초과 1 이하여야 함")
    if 0 not in mins:
        errors.append("gate.bands: min 0 구간이 있어야 모든 점수가 구간에 들어감")


def _check_groups(groups: list, persona_dir: Path | None, errors: list) -> dict:
    """그룹 id → weight. 항목 배점 합과 대조하는 데 쓴다."""
    weights: dict = {}
    for i, g in enumerate(groups):
        where = f"evaluator_groups[{i}]"
        if not isinstance(g, dict):
            errors.append(f"{where}: 매핑이어야 함")
            continue
        gid = _text(g.get("id"))
        if not gid:
            errors.append(f"{where}.id: 비어 있음")
            continue
        where = f"evaluator_groups({gid})"
        if gid in weights:
            errors.append(f"{where}: id 중복")
        _check_source(g, where, errors)
        w = g.get("weight")
        if not (_is_num(w) and w > 0):
            errors.append(f"{where}.weight: 양수여야 함")
            w = 0
        weights[gid] = w
        personas = _as_list(g.get("personas"), f"{where}.personas", errors)
        if not personas:
            errors.append(f"{where}: 페르소나가 없음 — 평가자 그룹마다 최소 한 명")
        elif persona_dir is not None:
            for p in personas:
                if not (persona_dir / f"{p}.md").is_file():
                    errors.append(f"{where}: personas/{p}.md 없음")
    if weights and abs(sum(weights.values()) - 100) > 1e-6:
        errors.append(f"evaluator_groups: weight 합이 100이 아님 ({sum(weights.values()):g})")
    return weights


def _check_item(item, idx: int, weights: dict, group_points: dict, errors: list):
    if not isinstance(item, dict):
        errors.append(f"items[{idx}]: 매핑이어야 함")
        return None
    iid = _text(item.get("id"))
    where = f"items[{iid or idx}]"
    if not iid:
        errors.append(f"{where}.id: 비어 있음")
    if not _text(item.get("name")):
        errors.append(f"{where}.name: 비어 있음")
    _check_source(item, where, errors)
    if item.get("source") == "official" and not _text(item.get("official_text")):
        errors.append(f"{where}.official_text: official 항목은 공고 원문이 필요함")

    points = _as_dict(item.get("points"), f"{where}.points", errors)
    if not points:
        errors.append(f"{where}.points: 비어 있음")
    for gid, pt in points.items():
        if gid not in weights:
            errors.append(f"{where}.points: 없는 평가자 그룹 {gid!r}")
        elif not (_is_num(pt) and pt >= 0):
            errors.append(f"{where}.points.{gid}: 0 이상 숫자여야 함")
        else:
            group_points[gid] = group_points.get(gid, 0) + pt

    questions = _as_list(item.get("questions"), f"{where}.questions", errors)
    if not 2 <= len(questions) <= 3:
        errors.append(f"{where}.questions: 2~3개여야 함 (현재 {len(questions)}개)")
    for j, q in enumerate(questions):
        qw = f"{where}.questions[{j}]"
        if not isinstance(q, dict):
            errors.append(f"{qw}: 매핑이어야 함")
            continue
        if not _text(q.get("text")):
            errors.append(f"{qw}.text: 비어 있음")
        _check_source(q, qw, errors)

    evidence = _as_list(item.get("evidence_types"), f"{where}.evidence_types", errors)
    if not evidence:
        errors.append(f"{where}.evidence_types: 최소 1개 필요")
    for e in evidence:
        if e not in EVIDENCE_TYPES:
            errors.append(f"{where}.evidence_types: 모르는 근거 종류 {e!r}")

    # YAML은 0/5/10 키를 정수로 읽으므로 문자열로 맞춘다
    anchors = {str(k): v for k, v in _as_dict(item.get("anchors"), f"{where}.anchors", errors).items()}
    for k in ANCHOR_KEYS:
        text = _text(anchors.get(k))
        if not text:
            errors.append(f"{where}.anchors.{k}: 비어 있음")
            continue
        lowered = text.lower()
        for word in BANNED_ANCHOR_WORDS:
            if word in lowered:
                errors.append(f"{where}.anchors.{k}: 관찰 불가 표현 '{word}' — 보이는 사실로 다시 쓸 것")

    for j, cap in enumerate(_as_list(item.get("caps"), f"{where}.caps", errors)):
        cw = f"{where}.caps[{j}]"
        if not isinstance(cap, dict):
            errors.append(f"{cw}: 매핑이어야 함")
            continue
        if not _text(cap.get("rule")):
            errors.append(f"{cw}.rule: 비어 있음")
        if not _is_int_in(cap.get("cap"), 0, 9):
            errors.append(f"{cw}.cap: 0~9 정수여야 함")
        if not _text(cap.get("unlock")):
            errors.append(f"{cw}.unlock: 해제 조건이 필요함")
        _check_source(cap, cw, errors)
    return iid or None


def validate_rubric(rubric, persona_dir: Path | None = None) -> list:
    if not isinstance(rubric, dict):
        return ["rubric.yaml 최상위는 매핑이어야 함"]
    errors: list = []
    if not _text(rubric.get("contest")):
        errors.append("contest: 비어 있음")

    purpose = _as_dict(rubric.get("purpose"), "purpose", errors)
    types = _as_list(purpose.get("contest_types"), "purpose.contest_types", errors)
    if not types:
        errors.append("purpose.contest_types: 최소 1개 필요")
    for t in types:
        if t not in CONTEST_TYPES:
            errors.append(f"purpose.contest_types: 모르는 종류 {t!r} ({', '.join(sorted(CONTEST_TYPES))})")

    _check_gate(_as_dict(rubric.get("gate"), "gate", errors), errors)

    calibration = _as_dict(rubric.get("calibration"), "calibration", errors)
    if calibration and calibration.get("status") not in ("done", "none"):
        errors.append("calibration.status: done 또는 none이어야 함")

    weights = _check_groups(_as_list(rubric.get("evaluator_groups"), "evaluator_groups", errors),
                            persona_dir, errors)
    if not weights:
        errors.append("evaluator_groups: 최소 1개 필요")

    items = _as_list(rubric.get("items"), "items", errors)
    if not items:
        errors.append("items: 최소 1개 필요")
    group_points: dict = {}
    seen = set()
    for i, item in enumerate(items):
        iid = _check_item(item, i, weights, group_points, errors)
        if iid and iid in seen:
            errors.append(f"items[{iid}]: id 중복")
        seen.add(iid)
    for gid, w in weights.items():
        got = group_points.get(gid, 0)
        if abs(got - w) > 1e-6:
            errors.append(f"evaluator_groups({gid}): 항목 배점 합 {got:g}이 weight {w:g}와 다름")

    for c in _as_list(rubric.get("common_caps"), "common_caps", errors):
        if c not in COMMON_CAPS:
            errors.append(f"common_caps: 모르는 규칙 {c!r}")
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="rubric.yaml 검사")
    ap.add_argument("contest_dir")
    args = ap.parse_args(argv)
    contest = Path(args.contest_dir)
    path = contest / "rubric.yaml"
    if not path.is_file():
        print(f"rubric.yaml 없음: {path}")
        return 2
    errors = validate_rubric(load_yaml(path), contest / "personas")
    if errors:
        for e in errors:
            print(f"- {e}")
        print(f"실패: {len(errors)}건")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    run_cli(main)
