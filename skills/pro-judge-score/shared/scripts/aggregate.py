#!/usr/bin/env python3
"""페르소나별 채점 원자료를 합산해 result.json을 만든다.

같은 입력이면 같은 숫자가 나와야 하므로 점수 계산은 전부 여기서 한다.
에이전트가 상한·인용 규칙을 어겨도 여기서 강제로 맞춘다.
사용: python3 aggregate.py <런 폴더> [--contest-dir DIR] [--target TEXT]
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_rubric import validate_rubric  # noqa: E402
import evidence  # noqa: E402
from _common import InputError, list_runs, load_json, load_yaml, parse_run_name, run_cli, write_json  # noqa: E402

# 확인 불가(claim-not-verified)가 시연 실패(claim-failed)보다 높으면 데모를 숨기는 편이 유리해진다 — 같은 값으로 둔다
COMMON_CAP_VALUES = {"intent-not-evidence": 5, "no-specifics": 5, "claim-not-verified": 4, "claim-failed": 4}
QUOTE_FOR_SEVEN = "quote-for-seven"
QUOTE_MIN_SCORE = 7
DEVIATION_THRESHOLD = 3
INSTABILITY_THRESHOLD = 3   # 같은 심사위원의 회차 간 점수 차가 이만큼이면 그 점수는 흔들린다
CONSENSUS_MAX_SCORE = 5
INFERRED_RANGE_SHARE = 0.3   # 추정 규칙에 기대는 배점이 이 비율 이상이면 총점을 범위로 낸다
ANCHOR_LEVELS = (5, 10)
INFERRED_MARGIN = 1          # 추정 규칙이 걸린 항목은 ±1점 흔들릴 수 있다고 본다
SKIP_FILES = {"result.json", "ideas.json"}


class AggregateError(Exception):
    pass


def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _is_score(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 10


def _opt_text(v):
    return v.strip() if isinstance(v, str) and v.strip() else None


def _norm_text(text: str) -> str:
    """공백·줄바꿈·대소문자 차이는 같은 문장으로 본다 — 추출 도구마다 줄바꿈이 달라서."""
    return " ".join(text.split()).lower()


def _normalize_persona(raw: dict, rubric: dict, source_norm: str | None = None, scope: set | None = None):
    """원자료를 검사하고 상한·인용 규칙을 강제한다. (정규화 결과 | None, 오류, 경고)"""
    name = raw["persona"]
    errors, warnings = [], []
    runs = raw.get("runs")
    if not isinstance(runs, list) or not runs:
        return None, ["runs가 비어 있음"], []
    norm_runs = []
    for r_i, run in enumerate(runs):
        where = f"runs[{r_i}]"
        if not isinstance(run, dict):
            errors.append(f"{where}: 객체가 아님")
            continue
        if not _is_score(run.get("gate_score")):
            errors.append(f"{where}.gate_score: 0~10 정수여야 함")
        scored = run.get("items")
        if not isinstance(scored, dict):
            errors.append(f"{where}.items: 객체가 아님")
            continue
        norm_items = {}
        for item in rubric["items"]:
            iid = item["id"]
            if scope is not None and iid not in scope:
                continue  # 자기 그룹에 배점이 없는 항목은 채점 대상이 아니다 — 매겨 와도 쓰지 않는다
            iw = f"{where}.items.{iid}"
            entry = scored.get(iid)
            if not isinstance(entry, dict):
                errors.append(f"{iw}: 없음")
                continue
            score = entry.get("score")
            if not _is_score(score):
                errors.append(f"{iw}.score: 0~10 정수여야 함")
                continue
            raw_quotes = entry.get("quotes")
            if isinstance(raw_quotes, str):
                raw_quotes = [raw_quotes]  # LLM이 인용 하나를 문자열로 내는 일이 흔하다 — 글자 단위로 쪼개지 않게
            elif raw_quotes is not None and not isinstance(raw_quotes, list):
                errors.append(f"{iw}.quotes: 문자열 목록이어야 함")
                continue
            quotes = [q.strip() for q in raw_quotes or [] if isinstance(q, str) and q.strip()]
            if source_norm is not None:
                # 지어낸 인용으로 7점 이상을 여는 것을 막는다 — 원문에 그대로 있는 문장만 근거로 인정
                fake = [q for q in quotes if _norm_text(q) not in source_norm]
                for q in fake:
                    warnings.append(f"{name} {iw}: 원문에 없는 인용 제외 — {q[:40]!r}")
                quotes = [q for q in quotes if q not in fake]
            cap = _opt_text(entry.get("cap_applied"))
            item_caps = {c["rule"]: c["cap"] for c in item.get("caps") or []}
            if cap is not None and cap != QUOTE_FOR_SEVEN:
                limit = item_caps.get(cap, COMMON_CAP_VALUES.get(cap))
                if limit is None:
                    warnings.append(f"{name} {iw}: 모르는 상한 규칙 {cap!r}")
                elif score > limit:
                    warnings.append(f"{name} {iw}: {cap} 상한 {limit}을 넘는 {score}점 → {limit}")
                    score = limit
            if score >= QUOTE_MIN_SCORE and not quotes:
                warnings.append(f"{name} {iw}: 인용 없는 {score}점 → {QUOTE_MIN_SCORE - 1}")
                score, cap = QUOTE_MIN_SCORE - 1, QUOTE_FOR_SEVEN
            norm_items[iid] = {"score": score, "quotes": quotes, "cap_applied": cap,
                               "unlock_hint": _opt_text(entry.get("unlock_hint"))}
        norm_runs.append({"gate_score": run.get("gate_score"), "items": norm_items,
                          "summary": _opt_text(run.get("summary")) or ""})
    if errors:
        return None, errors, warnings
    return {"persona": name, "model": _opt_text(raw.get("model")),
            "independent": raw.get("independent") is True, "runs": norm_runs}, [], warnings


def _majority_cap(runs: list, iid: str):
    """회차 과반이 같은 상한을 걸었을 때만 그 페르소나의 상한으로 본다 (중앙값과 같은 취지)."""
    counts = Counter(r["items"][iid]["cap_applied"] for r in runs)
    cap, n = counts.most_common(1)[0]
    return cap if cap is not None and n * 2 > len(runs) else None


def _unique(values, limit: int) -> list:
    out = []
    for v in values:
        if v and v not in out:
            out.append(v)
    return out[:limit]


def collect_inferred(rubric: dict) -> list:
    rules = []
    for g in rubric.get("evaluator_groups") or []:
        if g.get("source") == "inferred":
            rules.append(f"evaluator_groups({g['id']}): {g.get('why', '')}")
    gate = rubric.get("gate") or {}
    if gate.get("source") == "inferred":
        rules.append(f"gate: {gate.get('why', '')}")
    for it in rubric["items"]:
        if it.get("source") == "inferred":
            rules.append(f"items[{it['id']}]: {it.get('why', '')}")
        for q in it.get("questions") or []:
            if q.get("source") == "inferred":
                rules.append(f"items[{it['id']}] 질문 '{q.get('text', '')}': {q.get('why', '')}")
        for c in it.get("caps") or []:
            if c.get("source") == "inferred":
                rules.append(f"items[{it['id']}] 상한 {c['rule']}({c['cap']}): {c.get('why', '')}")
    return rules


def aggregate(rubric: dict, raw_results: list, *, previous: dict | None = None,
              created_at: str = "", target: str = "", run: str = "",
              load_failures: dict | None = None, source_text: str | None = None,
              calibration: bool = False) -> dict:
    groups = rubric["evaluator_groups"]
    persona_groups: dict = {}
    for g in groups:
        for p in g["personas"]:
            persona_groups.setdefault(p, []).append(g["id"])

    source_norm = _norm_text(source_text) if source_text is not None else None
    # 파일 자체를 못 읽은 페르소나도 "제외"로 남겨 N명 중 M명에 반영한다
    valid, failed, warnings = {}, dict(load_failures or {}), []
    for raw in raw_results:
        name = raw.get("persona") if isinstance(raw, dict) else None
        if not isinstance(name, str) or name not in persona_groups:
            failed[str(name)] = ["rubric에 없는 페르소나"]
            continue
        scope = {it["id"] for it in rubric["items"] if set(it["points"]) & set(persona_groups[name])}
        norm, errs, warns = _normalize_persona(raw, rubric, source_norm, scope)
        warnings += warns
        if errs:
            failed[name] = errs
        else:
            valid[name] = norm

    members = {g["id"]: [p for p in g["personas"] if p in valid] for g in groups}
    for gid, ps in members.items():
        if not ps:
            raise AggregateError(f"평가자 그룹 {gid}에 쓸 수 있는 채점 결과가 하나도 없음")

    med = {p: {iid: median(r["items"][iid]["score"] for r in v["runs"]) for iid in v["runs"][0]["items"]}
           for p, v in valid.items()}

    def group_score(iid: str, gid: str) -> float:
        return mean(med[p][iid] for p in members[gid])

    def earned_of(item: dict, shift: int = 0) -> float:
        total = 0.0
        for gid, pts in item["points"].items():
            gs = min(10.0, max(0.0, group_score(item["id"], gid) + shift))
            total += gs / 10 * pts
        return total

    prev_items = {i["id"]: i for i in (previous or {}).get("items", [])}
    items_out = []
    for it in rubric["items"]:
        iid = it["id"]
        scorers = [p for p in valid if iid in med[p]]  # 이 항목에 배점이 있는 그룹의 심사위원만
        by_persona = {p: med[p][iid] for p in scorers}
        persona_caps = [_majority_cap(valid[p]["runs"], iid) for p in scorers]
        caps = _unique(persona_caps, 10)
        inferred_caps = {c["rule"] for c in it.get("caps") or [] if c.get("source") == "inferred"}
        all_runs = [r for p in scorers for r in valid[p]["runs"]]
        earned = earned_of(it)
        points_total = sum(it["points"].values())
        prev = prev_items.get(iid)
        items_out.append({
            "id": iid,
            "name": it["name"],
            "source": it["source"],
            "points_total": _r(points_total),
            "earned": _r(earned),
            "score_mean": _r(mean(by_persona.values())),
            "by_persona": {p: _r(s) for p, s in by_persona.items()},
            "group_scores": {gid: _r(group_score(iid, gid)) for gid in it["points"]},
            "spread": _r(max(by_persona.values()) - min(by_persona.values())),
            "caps": caps,
            "quotes": _unique((q for r in all_runs for q in r["items"][iid]["quotes"]), 5),
            "unlock_hints": _unique((r["items"][iid]["unlock_hint"] for r in all_runs), 5),
            "inferred_dependent": it["source"] == "inferred" or any(c in inferred_caps for c in caps),
            "delta": _r(earned - prev["earned"]) if prev else None,
            "run_range": _r(max(max(r["items"][iid]["score"] for r in valid[p]["runs"])
                                - min(r["items"][iid]["score"] for r in valid[p]["runs"]) for p in scorers)),
            "_item": it,
        })

    gate_cfg = rubric.get("gate") or {}
    gate_score = mean(median(r["gate_score"] for r in v["runs"]) for v in valid.values())
    multiplier = 1.0
    if gate_cfg.get("source") == "official":
        for band in sorted(gate_cfg["bands"], key=lambda b: b["min"], reverse=True):
            if gate_score >= band["min"]:
                multiplier = band["multiplier"]
                break

    raw_total = sum(i["earned"] for i in items_out)
    total = _r(round(raw_total * multiplier, 1))
    inferred_share = _r(sum(i["points_total"] for i in items_out if i["inferred_dependent"]) / 100)
    total_range = None
    if inferred_share >= INFERRED_RANGE_SHARE:
        low = sum(earned_of(i["_item"], -INFERRED_MARGIN) if i["inferred_dependent"] else i["earned"] for i in items_out)
        high = sum(earned_of(i["_item"], INFERRED_MARGIN) if i["inferred_dependent"] else i["earned"] for i in items_out)
        total_range = [_r(round(low * multiplier, 1)), _r(round(high * multiplier, 1))]

    # 모델 수는 그 항목을 실제로 채점한 심사위원 기준 — 1명만 채점한 항목이 "공통"이 되지 않게
    consensus = [i["id"] for i in items_out
                 if len({valid[p]["model"] for p in i["by_persona"] if valid[p]["model"]}) >= 2
                 and all(s <= CONSENSUS_MAX_SCORE for s in i["by_persona"].values())]

    # "못 받은 점수"가 아니라 "다음 앵커까지 올렸을 때 오르는 점수"로 고른다 — 앵커 문장이 곧 할 일이다
    candidates = []
    for i in items_out:
        if not i["points_total"]:
            continue
        level = i["earned"] / i["points_total"] * 10
        goal = next((a for a in ANCHOR_LEVELS if a > level + 1e-9), None)
        if goal is None:
            continue
        anchors = {str(k): v for k, v in (i["_item"].get("anchors") or {}).items()}
        candidates.append({"item": i["id"], "name": i["name"],
                           "gain": _r(round((goal - level) / 10 * i["points_total"] * multiplier, 1)),
                           "level": _r(level), "next_anchor": goal,
                           "next_anchor_text": str(anchors.get(str(goal), "")).strip(),
                           # 순위는 다음 앵커 기준 그대로 두고, 만점까지 남은 점수를 함께 낸다
                           "max_gain": _r(round((i["points_total"] - i["earned"]) * multiplier, 1)),
                           "caps": i["caps"], "unlock_hints": i["unlock_hints"]})
    fix_priority = sorted(candidates, key=lambda f: f["gain"], reverse=True)[:5]
    # 다음 앵커가 가까운 항목은 순위에서 밀리지만 손실은 클 수 있다 — 가장 큰 구멍은 따로 보여 준다
    losses = sorted(({"item": i["id"], "name": i["name"], "caps": i["caps"],
                      "lost": _r(round((i["points_total"] - i["earned"]) * multiplier, 1))}
                     for i in items_out if i["points_total"] - i["earned"] > 1e-9),
                    key=lambda x: x["lost"], reverse=True)[:3]
    losses = [{"item": x["item"], "name": x["name"], "lost": x["lost"], "caps": x["caps"]} for x in losses]

    for i in items_out:
        del i["_item"]

    expected = list(persona_groups)
    cal_cfg = rubric.get("calibration") or {}
    return {
        "kind": "score",
        "contest": rubric["contest"],
        "run": run,
        "created_at": created_at,
        "target": target,
        "total": total,
        "total_range": total_range,
        "raw_total": _r(raw_total),
        "gate": {"source": gate_cfg.get("source", "none"), "score": _r(gate_score),
                 # 공고에 취지 기준이 없으면(none) 경보할 기준도 없다
                 "multiplier": multiplier, "warning": gate_cfg.get("source", "none") != "none" and gate_score < 5},
        "items": items_out,
        "deviation_alerts": [i["id"] for i in items_out if i["spread"] >= DEVIATION_THRESHOLD],
        "instability_alerts": [i["id"] for i in items_out if i["run_range"] >= INSTABILITY_THRESHOLD],
        "quotes_verified": source_norm is not None,
        "calibration": calibration,
        "consensus_gaps": consensus,
        "fix_priority": fix_priority,
        "losses": losses,
        "personas": [{"name": p, "groups": persona_groups[p], "model": v["model"],
                      "independent": v["independent"], "summary": v["runs"][-1]["summary"]}
                     for p, v in valid.items()],
        "participation": {"expected": len(expected), "succeeded": len(valid)},
        "missing_personas": [p for p in expected if p not in valid],
        "failed": failed,
        "warnings": warnings,
        "independent": all(v["independent"] for v in valid.values()),
        "inferred_share": inferred_share,
        "no_official_criteria": all(it["source"] == "inferred" for it in rubric["items"]),
        "calibrated": cal_cfg.get("status") == "done",
        "inferred_rules": collect_inferred(rubric),
        "previous": ({"run": previous.get("run", ""), "total": previous["total"],
                      "delta": _r(round(total - previous["total"], 1))} if previous else None),
        "narrative": {"overall": "", "personas": {}},
    }


def _find_contest_dir(run_dir: Path) -> Path:
    for p in [run_dir, *run_dir.parents]:
        if (p / "rubric.yaml").is_file():
            return p
    raise InputError(f"{run_dir} 위쪽에서 rubric.yaml을 찾지 못함 — --contest-dir로 지정")


def _find_previous(contest_dir: Path, run_dir: Path):
    """같은 대회의 직전 채점 회차. 아이디어 하위 폴더처럼 runs/ 바로 아래가 아니면 비교하지 않는다."""
    parsed = parse_run_name(run_dir.name)
    if not parsed or run_dir.parent.resolve() != (contest_dir / "runs").resolve():
        return None
    runs = [p.resolve() for p in list_runs(contest_dir, parsed[1])]
    idx = runs.index(run_dir.resolve())
    for p in reversed(runs[:idx]):
        if (p / "result.json").is_file():
            prev = load_json(p / "result.json")
            if not prev.get("calibration"):  # 보정용으로 채점한 남의 작품과는 비교하지 않는다
                return prev
    return None


def _read_target(run_dir: Path):
    """<런>/target/ 아래 텍스트를 모아 인용 대조 원문으로 쓴다. 폴더가 없으면 대조하지 않는다."""
    target = run_dir / "target"
    if not target.is_dir():
        return None
    texts = []
    for f in sorted(target.rglob("*")):
        if f.is_file():
            try:
                texts.append(f.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue  # 원본 PDF·이미지는 건너뛴다 — 추출한 텍스트 파일만 대조 대상
    return "\n".join(texts)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="페르소나 채점 합산")
    ap.add_argument("run_dir")
    ap.add_argument("--contest-dir")
    ap.add_argument("--target", default="")
    ap.add_argument("--calibration", action="store_true", help="보정용(역대 수상작·낙선작) 채점 — 회차 비교·추이에서 뺀다")
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir)
    contest_dir = Path(args.contest_dir) if args.contest_dir else _find_contest_dir(run_dir)
    rubric = load_yaml(contest_dir / "rubric.yaml")
    # 손으로 고친 rubric이 깨져 있으면 합산 중 traceback 대신 고칠 목록을 보여 준다
    rubric_errors = validate_rubric(rubric)
    if rubric_errors:
        raise InputError("rubric.yaml 결함 — validate_rubric.py로 고친 뒤 다시 실행:\n- " + "\n- ".join(rubric_errors))
    # 근거 장부가 깨져 있으면 채점 결과를 만들기 전에 멈춘다 — 무엇을 봤는지 틀린 채로 보고서가 나가면 안 된다
    ledger_path = run_dir / "evidence.yaml"
    ledger = evidence.load_checked(ledger_path, rubric) if ledger_path.is_file() else None
    files = [f for f in sorted(run_dir.glob("*.json")) if f.name not in SKIP_FILES]
    if not files:
        raise InputError(f"{run_dir}에 페르소나 결과 json이 없음")
    raws, load_failures = [], {}
    for f in files:
        try:
            raws.append(load_json(f))
        except InputError as e:
            # 서브에이전트 출력이 잘리는 게 가장 흔한 실패 — 그 페르소나만 빼고 합산한다
            load_failures[f.stem] = [str(e)]
    try:
        result = aggregate(rubric, raws, previous=_find_previous(contest_dir, run_dir),
                           created_at=datetime.now().isoformat(timespec="minutes"),
                           target=args.target, run=run_dir.name, load_failures=load_failures,
                           source_text=_read_target(run_dir), calibration=args.calibration)
    except AggregateError as e:
        raise InputError(str(e))
    result["evidence"] = evidence.summary(ledger, rubric) if ledger else None
    write_json(run_dir / "result.json", result)
    if not result["quotes_verified"]:
        print("경고: target/ 폴더가 없어 인용 원문 대조를 하지 않음")
    for w in result["warnings"]:
        print(f"경고: {w}")
    for name, errs in result["failed"].items():
        print(f"제외: {name} — {'; '.join(errs[:3])}")
    print(f"총점 {result['total']} ({result['participation']['succeeded']}/{result['participation']['expected']}명)")
    print(run_dir / "result.json")
    return 0


if __name__ == "__main__":
    run_cli(main)
