#!/usr/bin/env python3
"""result.json → report.md + report.html.

숫자·표·차트는 여기서 찍고, 에이전트는 result.json의 narrative(총평)만 채운다.
사용: python3 render_report.py <런 폴더>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import InputError, load_json, load_yaml, run_cli  # noqa: E402
from report_blocks import to_html, to_markdown  # noqa: E402


def _fmt_delta(d) -> str:
    return "-" if d is None else f"{d:+.1f}"


def contest_labels(run_dir) -> dict:
    """대회 폴더의 점수표·페르소나에서 사람이 읽는 이름을 모은다.

    result.json에는 id만 있어 보고서에 `community-lead` 같은 내부 이름이 그대로 나왔다.
    대회 폴더를 못 찾거나 파일이 깨져도 보고서는 id로 나가야 하므로 빈 사전으로 둔다.
    """
    labels = {"personas": {}, "items": {}}
    run_dir = Path(run_dir)
    contest = next((p for p in [run_dir, *run_dir.parents] if (p / "rubric.yaml").is_file()), None)
    if contest is None:
        return labels
    try:
        rubric = load_yaml(contest / "rubric.yaml")
        labels["items"] = {it["id"]: it["name"] for it in rubric.get("items") or [] if it.get("id") and it.get("name")}
    except (InputError, AttributeError, TypeError):
        pass
    for f in sorted((contest / "personas").glob("*.md")) if (contest / "personas").is_dir() else []:
        try:
            title = next((ln[2:].strip() for ln in f.read_text(encoding="utf-8").splitlines() if ln.startswith("# ")), "")
        except (OSError, UnicodeDecodeError):
            continue
        if title:
            labels["personas"][f.stem] = title
    return labels


def _when(created_at: str) -> str:
    # ISO 시각의 T는 사람이 읽기에 낯설다
    return str(created_at or "-").replace("T", " ")


def _who(labels: dict, persona: str) -> str:
    return (labels or {}).get("personas", {}).get(persona) or persona


def _item(labels: dict, iid: str) -> str:
    return (labels or {}).get("items", {}).get(iid) or iid


def _notices(r: dict) -> list:
    """첫 화면을 차지하던 경고 상자들 — 한 덩어리로 접어 총점 아래에 둔다. 내용은 그대로 남긴다."""
    # 숫자가 정밀해 보여도 실제 받을 점수의 예측이 아니다 — 매 보고서에 못박는다
    n = [{"label": "진단 지표", "text": "이 점수는 아래 점수표로 잰 상대 진단이다. 실제 대회에서 받을 점수의 예측이 아니다. "
                                        "같은 점수표로 고치기 전후를 비교하는 데 쓴다."}]
    if r.get("calibration"):
        n.append({"label": "보정용 채점", "text": "역대 수상작·낙선작을 점수표 검증용으로 채점한 회차다. 회차 비교와 추이에서 빠진다."})
    if not r.get("quotes_verified"):
        n.append({"label": "인용 원문 대조 안 함",
                  "text": "채점 대상 원문(target/)이 없어 인용이 실제 자료에 있는지 확인하지 못했다. 7점 이상 점수를 그대로 믿지 않는다."})
    if r["no_official_criteria"]:
        n.append({"label": "공식 기준 없음", "text": "모든 항목이 추정(inferred)이다. 점수는 참고용이다."})
    if not r.get("evidence"):
        n.append({"label": "근거 장부 없음",
                  "text": "무엇을 봤고 무엇을 못 봤는지 기록되지 않았다(evidence.yaml). 빠진 자료 때문에 깎인 점수를 구분할 수 없다."})
    if not r["calibrated"]:
        n.append({"label": "보정 안 됨", "text": "역대 수상작으로 점수표를 검증하지 않았다."})
    if not r["independent"]:
        n.append({"label": "독립 실행 아님", "text": "페르소나를 한 맥락에서 차례대로 돌렸다. 서로의 판단이 섞였을 수 있다."})
    p = r["participation"]
    if p["succeeded"] < p["expected"]:
        n.append({"label": f"{p['expected']}명 중 {p['succeeded']}명", "text": f"빠진 심사위원: {', '.join(r['missing_personas'])}"})
    g = r["gate"]
    if g["warning"]:
        n.append({"label": "취지 경보", "text": f"취지 적합 {g['score']:g}/10 · 배율 {g['multiplier']:g} ({g['source']})"})
    return n


def _fix_view(f: dict) -> dict:
    # level·앵커는 10점 척도, gain은 총점 기준이다 — 막대(배점 기준)와 섞여 보이지 않게 척도를 밝힌다
    now = f"10점 척도 {f.get('level', 0):.1f} → {f.get('next_anchor', '-')}"
    if f.get("max_gain") is not None:
        now += f" · 만점까지 최대 +{f['max_gain']:.1f}점"
    return {"name": f["name"], "gain": f["gain"], "now": now,
            "anchor": f.get("next_anchor_text") or "", "caps": ", ".join(f["caps"]),
            "hint": (f["unlock_hints"] or [""])[0]}


def _score_blocks(r: dict, labels: dict | None = None) -> list:
    p, g = r["participation"], r["gate"]
    meta = [_when(r["created_at"]), f"회차 {r['run'] or '-'}", f"대상 {r['target'] or '-'}", f"심사위원 {p['succeeded']}명",
            "인용 원문 대조함" if r.get("quotes_verified") else "인용 원문 대조 안 함"]
    # 접힌 안내만으로는 놓친다 — "예측 아님"은 총점 옆에 늘 보이게 둔다
    sub = ["진단 지표다. 실제 대회 점수의 예측이 아니다."]
    if r["total_range"]:
        sub.append(f"추정 규칙 민감도 {r['total_range'][0]:.1f} ~ {r['total_range'][1]:.1f} (추정 규칙 비중 {r['inferred_share']:.0%}, 신뢰구간 아님)")
    if r["previous"]:
        sub.append(f"지난 회차 {r['previous']['total']:.1f} 대비 {_fmt_delta(r['previous']['delta'])}")
    if g["multiplier"] < 1:
        sub.append(f"취지 배율 {g['multiplier']:g} 적용 전 {r['raw_total']:.1f}")
    fixes = [_fix_view(f) for f in r["fix_priority"]]
    notices = _notices(r)
    b = [{"type": "h1", "text": f"{r['contest']} 채점 보고서"},
         {"type": "meta", "items": meta},
         {"type": "hero", "score": r["total"], "max": 100, "caption": "100점 만점 환산 총점", "sub": sub,
          "top_fix": fixes[0] if fixes else None, "loss": (r.get("losses") or [None])[0]},
         {"type": "notice", "label": f"이 점수 읽는 법 · 확인할 것 {len(notices)}건", "items": notices}]

    nar = _narrative(r)
    b += [{"type": "h2", "text": "총평"}, {"type": "p", "text": nar.get("overall") or "(총평 없음)"}]

    b += [{"type": "h2", "text": "항목별 점수"},
          {"type": "bars", "scale": True,
           "rows": [{"label": i["name"], "value": i["earned"], "max": i["points_total"]} for i in r["items"]]}]

    b += [{"type": "h2", "text": "고칠 것 Top 5"},
          {"type": "p", "muted": True,
           "text": "다음 기준 문장(10점 척도의 5점 또는 10점)까지 올렸을 때 바로 오르는 총점 순서다. 그 문장이 자료에 생기게 만드는 것이 할 일이다. "
                   "다음 기준이 가까운 항목은 오르는 점수가 작게 나온다 — 손실이 큰 항목은 맨 위 '가장 큰 손실'을 함께 본다."},
          {"type": "fixes", "items": fixes}]

    b += _evidence_blocks(r.get("evidence"))

    names = {i["id"]: i["name"] for i in r["items"]}
    b += [{"type": "h2", "text": "편차 경보"},
          {"type": "list", "items": [f"{names[iid]}: 심사위원 사이 {next(i['spread'] for i in r['items'] if i['id'] == iid):g}점 차이"
                                     for iid in r["deviation_alerts"]]},
          {"type": "h2", "text": "회차마다 흔들린 항목"},
          {"type": "list", "items": [f"{names[iid]}: 같은 심사위원 점수가 회차마다 {next(i.get('run_range', 0) for i in r['items'] if i['id'] == iid):g}점까지 달라짐 — 앵커가 모호하거나 근거가 애매하다"
                                     for iid in r.get("instability_alerts", [])]},
          {"type": "h2", "text": "공통 약점 (모델 2종 이상, 전원 5점 이하)"},
          {"type": "list", "items": [names[iid] for iid in r["consensus_gaps"]]}]

    b += [{"type": "fold", "label": "항목별 근거", "blocks": [
          {"type": "table", "headers": ["항목", "득점 / 배점", "심사위원별", "상한", "인용", "변화"],
           "rows": [[i["name"], f"{i['earned']:g} / {i['points_total']:g}",
                     ", ".join(f"{_who(labels, p)} {s:g}" for p, s in i["by_persona"].items()),
                     ", ".join(i["caps"]) or "-", " / ".join(i["quotes"]) or "(인용 없음)", _fmt_delta(i["delta"])]
                    for i in r["items"]]}]}]

    b += [{"type": "h2", "text": "심사위원별 총평"},
          {"type": "cards", "items": [{"title": _who(labels, p["name"]),
                                       "sub": f"모델 {p['model'] or '미기록'}",
                                       "text": (nar.get("personas") or {}).get(p["name"]) or p["summary"] or "-"}
                                      for p in r["personas"]]}]

    b += [{"type": "fold", "label": "부록", "blocks": [
          {"type": "p", "text": "추정(inferred) 규칙 — 공고에 없어 에이전트가 정한 것"},
          {"type": "list", "items": r["inferred_rules"]},
          {"type": "p", "text": "실행 정보"},
          {"type": "list", "items": [f"{_who(labels, p['name'])}: 모델 {p['model'] or '-'}, 독립 실행 {'예' if p['independent'] else '아니오'}"
                                     for p in r["personas"]]
                                    + [f"제외 {n}: {'; '.join(e[:3])}" for n, e in r["failed"].items()]},
          {"type": "p", "text": "경고"},
          {"type": "list", "items": r["warnings"]}]}]
    return b


EVIDENCE_TYPE_LABEL = {"numbers": "숫자", "proper-nouns": "고유명사", "demo": "시연", "field-test": "실증",
                       "quote": "인용", "observation": "관찰", None: "-"}
SOURCE_LABEL = {"file": "파일", "repo": "저장소", "url": "URL", "web": "웹 검색", "user": "사용자", "video": "영상"}
TRUST_LABEL = {"official": "공식", "reported": "보도·제3자", "self": "팀 자료", "user": "사용자 진술"}
STATUS_LABEL = {"ok": "확인함", "partial": "일부만", "failed": "못 봄"}


def _gap_lines(gaps: list) -> list:
    """같은 항목의 빈칸을 한 줄로 — "독창성: 인용", "독창성: 관찰"처럼 흩어지면 무엇이 없는지 안 읽힌다."""
    grouped: dict = {}
    for g in gaps:
        grouped.setdefault(g["name"], [])
        if g.get("type"):
            grouped[g["name"]].append(EVIDENCE_TYPE_LABEL.get(g["type"], g["type"]))
    return [f"{name} — {'·'.join(types)} 근거를 자료에서 찾지 못함" if types else f"{name} — 근거를 자료에서 찾지 못함"
            for name, types in grouped.items()]


def _evidence_blocks(ev) -> list:
    """채점 전에 무엇을 봤고 무엇을 못 봤는지 — 빈칸 때문에 깎인 점수를 자료 부족과 구분하게 한다."""
    if not ev:
        return []
    def label(g):
        return f"{g['name']}: {EVIDENCE_TYPE_LABEL.get(g['type'], g['type'])}" if g.get("type") else g["name"]
    return [{"type": "h2", "text": "확인한 자료와 빈칸"},
            {"type": "table", "headers": ["출처", "어디서", "어떻게", "신뢰", "상태"],
             "rows": [[SOURCE_LABEL.get(s["kind"], s["kind"]), s["ref"], s.get("how") or "-",
                       TRUST_LABEL.get(s["trust"], s["trust"]), STATUS_LABEL.get(s["status"], s["status"]) + (f" ({s['note']})" if s.get("note") else "")]
                      for s in ev["sources"]]},
            {"type": "p", "text": "못 본 것 — 점수표가 요구하는 근거 중 자료에서 찾지 못한 것. 이 항목의 점수는 자료를 넣으면 달라질 수 있다."},
            {"type": "list", "items": _gap_lines(ev["gaps"])},
            {"type": "p", "text": "없다고 확인된 것"},
            {"type": "list", "items": [f"{label(a)} — {a['text']}" for a in ev["absent"]]}]


VERDICT_LABEL = {"up": "올림", "same": "그대로", "down": "깎음", None: "-"}
VERDICT_ORDER = {"down": 0, "same": 1}
COST_LABEL = {"low": "낮음", "mid": "중간", "high": "높음"}


def _narrative(r: dict) -> dict:
    """에이전트가 손으로 채우는 칸이라 타입이 틀리기 쉽다 — traceback 대신 고칠 곳을 말한다."""
    nar = r.get("narrative") or {}
    if not isinstance(nar, dict):
        raise InputError('result.json narrative: {"overall": "...", "personas": {...}} 객체여야 함')
    if not isinstance(nar.get("overall") or "", str):
        raise InputError("result.json narrative.overall: 문자열이어야 함")
    if not isinstance(nar.get("personas") or {}, dict):
        raise InputError("result.json narrative.personas: {이름: 총평} 객체여야 함")
    return nar


def validate_grill(r: dict) -> None:
    if r.get("mode") not in ("practice", "sheet"):
        raise InputError("grill result: mode는 practice/sheet")
    for key in ("contest", "created_at"):
        if not isinstance(r.get(key), str):
            raise InputError(f"grill result: {key}가 문자열이어야 함")
    questions = r.get("questions")
    if not isinstance(questions, list):
        raise InputError("grill result: questions가 목록이어야 함")
    for n, q in enumerate(questions):
        if not isinstance(q, dict):
            raise InputError(f"grill result questions[{n}]: 객체여야 함 (grill-output.md 형식)")
        for key in ("persona", "item"):
            if not str(q.get(key) or "").strip():
                raise InputError(f"grill result questions[{n}]: {key}가 비어 있음")
        follow_ups = q.get("follow_ups") or []
        if not isinstance(follow_ups, list) or not all(isinstance(f, dict) for f in follow_ups):
            raise InputError(f"grill result questions[{n}].follow_ups: 객체 목록이어야 함")
        for qq in [q, *follow_ups]:
            if qq.get("verdict") not in VERDICT_LABEL:
                raise InputError(f"grill result questions[{n}]: verdict는 up/same/down/null")
            if not str(qq.get("question") or "").strip():
                raise InputError(f"grill result questions[{n}]: question이 비어 있음")
    suggestions = r.get("suggestions") or []
    if not isinstance(suggestions, list):
        raise InputError("grill result: suggestions가 목록이어야 함")
    for n, sg in enumerate(suggestions):
        if not isinstance(sg, dict) or not all(k in sg for k in ("evidence", "item", "from_score", "to_score")):
            raise InputError(f"grill result suggestions[{n}]: evidence, item, from_score, to_score가 필요함")
    _narrative(r)


def _grill_blocks(r: dict, labels: dict | None = None) -> list:
    validate_grill(r)
    mode = "연습" if r["mode"] == "practice" else "질문지"
    b = [{"type": "h1", "text": f"{r['contest']} 질의응답 보고서"},
         {"type": "meta", "items": [_when(r["created_at"]), f"{mode} 모드", f"질문 {len(r['questions'])}개"]
                                   + ([f"기준 회차 {r['based_on']}"] if r.get("based_on") else [])}]
    items, weak = [], []
    for n, q in enumerate(r["questions"], 1):
        who, item = _who(labels, q["persona"]), _item(labels, q["item"])
        items.append({"no": n, "who": who, "item": item, "question": q["question"], "answer": q.get("answer"),
                      "verdict_label": VERDICT_LABEL[q.get("verdict")] if q.get("verdict") else None,
                      "reason": q.get("reason"), "model_answer": q.get("model_answer")})
        if q.get("verdict") in VERDICT_ORDER:
            weak.append((VERDICT_ORDER[q["verdict"]], n, q))
        for m, f in enumerate(q.get("follow_ups") or [], 1):
            items.append({"no": f"{n}-꼬리{m}", "who": who, "item": item, "question": f["question"], "answer": f.get("answer"),
                          "verdict_label": VERDICT_LABEL[f.get("verdict")] if f.get("verdict") else None,
                          "reason": f.get("reason"), "follow": True})
            if f.get("verdict") in VERDICT_ORDER:
                weak.append((VERDICT_ORDER[f["verdict"]], n, f))
    if r["mode"] == "practice":
        b += [{"type": "h2", "text": "질문과 판정"}, {"type": "qa", "mode": "practice", "items": items},
              {"type": "h2", "text": "약한 답변"},
              {"type": "list", "items": [f"[{VERDICT_LABEL[q['verdict']]}] {q['question']} — {q.get('reason') or '-'}"
                                         for _, _, q in sorted(weak, key=lambda t: (t[0], t[1]))]}]
    else:
        b += [{"type": "h2", "text": "예상 질문지"},
              {"type": "p", "muted": True, "text": "심사위원이 약한 항목을 찌를 질문과, 자료에 있는 사실로 채운 답변 뼈대다. 대괄호 칸은 아직 자료에 없는 것이다."},
              {"type": "qa", "mode": "sheet", "items": items}]
    b += [{"type": "h2", "text": "자료 수정 제안"},
          {"type": "table", "headers": ["넣을 근거", "항목", "점수 변화"],
           "rows": [[s["evidence"], _item(labels, s["item"]), f"{s['from_score']} → {s['to_score']} (10점 척도)"] for s in r.get("suggestions") or []]},
          {"type": "h2", "text": "총평"},
          {"type": "p", "text": _narrative(r).get("overall") or "(총평 없음)"}]
    return b


def _ideas_blocks(r: dict, labels: dict | None = None) -> list:
    b = [{"type": "h1", "text": f"{r['contest']} 아이디어 비교"},
         {"type": "meta", "items": [_when(r["created_at"]), f"아이디어 {len(r['ideas'])}개"]},
         {"type": "p", "muted": True, "text": "명세대로 완벽히 구현했다고 가정한 상한 점수다."},
         {"type": "table", "headers": ["순위", "아이디어", "상한 점수", "취지", "막는 요인", "구현 비용"],
          "rows": [[i["rank"], i["title"],
                    f"{i['total']:.1f}" + (f" ({i['total_range'][0]:.1f}~{i['total_range'][1]:.1f})" if i["total_range"] else ""),
                    ("취지 경보 " if i["gate"]["warning"] else "") + f"{i['gate']['score']:g}/10",
                    " / ".join(i["blockers"]) or "-",
                    f"{COST_LABEL.get(i['cost']['level'], i['cost']['level'])} — {i['cost']['note'] or '-'}"]
                   for i in r["ideas"]]},
         {"type": "bars", "rows": [{"label": i["title"], "value": i["total"], "max": 100} for i in r["ideas"]]}]
    for i in r["ideas"]:
        b += [{"type": "h2", "text": f"{i['title']} — 점수를 막는 것"},
              {"type": "list", "items": [f"{f['name']}: +{f['gain']:g}점 여지 — {' / '.join(f['unlock_hints']) or '해제 조건 없음'}"
                                         for f in i["fix_priority"]]}]
    b += [{"type": "h2", "text": "총평"},
          {"type": "p", "text": _narrative(r).get("overall") or "(총평 없음)"}]
    return b


BUILDERS = {"score": _score_blocks, "grill": _grill_blocks, "ideas": _ideas_blocks}


def build_blocks(result: dict, labels: dict | None = None) -> list:
    kind = result.get("kind")
    if kind not in BUILDERS:
        raise InputError(f"result.json kind를 모름: {kind!r}")
    return BUILDERS[kind](result, labels)


def render(result: dict, labels: dict | None = None):
    blocks = build_blocks(result, labels)
    return to_markdown(blocks), to_html(blocks, blocks[0]["text"], "진단 지표이며 실제 대회 점수의 예측이 아니다")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="보고서 생성")
    ap.add_argument("run_dir")
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir)
    md, html = render(load_json(run_dir / "result.json"), contest_labels(run_dir))
    (run_dir / "report.md").write_text(md, encoding="utf-8")
    (run_dir / "report.html").write_text(html, encoding="utf-8")
    print(run_dir / "report.md")
    print(run_dir / "report.html")
    return 0


if __name__ == "__main__":
    run_cli(main)
