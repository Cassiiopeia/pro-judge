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
from _common import InputError, load_json, run_cli  # noqa: E402
from report_blocks import to_html, to_markdown  # noqa: E402


def _fmt_delta(d) -> str:
    return "-" if d is None else f"{d:+.1f}"


def _score_blocks(r: dict) -> list:
    b = [{"type": "h1", "text": f"{r['contest']} 채점 보고서"},
         {"type": "p", "text": f"{r['created_at']} · 회차 {r['run'] or '-'} · 대상 {r['target'] or '-'}"}]
    if r["no_official_criteria"]:
        b.append({"type": "callout", "label": "공식 기준 없음",
                  "text": "모든 항목이 추정(inferred)이다. 점수는 참고용이다."})
    if not r["calibrated"]:
        b.append({"type": "callout", "label": "보정 안 됨",
                  "text": "역대 수상작으로 점수표를 검증하지 않았다."})
    if not r["independent"]:
        b.append({"type": "callout", "label": "독립 실행 아님",
                  "text": "페르소나를 한 맥락에서 차례대로 돌렸다. 서로의 판단이 섞였을 수 있다."})
    p = r["participation"]
    if p["succeeded"] < p["expected"]:
        b.append({"type": "callout", "label": f"{p['expected']}명 중 {p['succeeded']}명",
                  "text": f"빠진 심사위원: {', '.join(r['missing_personas'])}"})
    g = r["gate"]
    if g["warning"]:
        b.append({"type": "callout", "label": "취지 경보",
                  "text": f"취지 적합 {g['score']:g}/10 · 배율 {g['multiplier']:g} ({g['source']})"})

    total = f"{r['total']:.1f} / 100"
    if r["total_range"]:
        total += f" (범위 {r['total_range'][0]:.1f} ~ {r['total_range'][1]:.1f}, 추정 규칙 비중 {r['inferred_share']:.0%})"
    if r["previous"]:
        total += f" · 지난 회차 {r['previous']['total']:.1f} 대비 {_fmt_delta(r['previous']['delta'])}"
    b += [{"type": "h2", "text": "총점"}, {"type": "p", "text": total},
          {"type": "bars", "rows": [{"label": i["name"], "value": i["earned"], "max": i["points_total"]}
                                    for i in r["items"]]}]

    b += [{"type": "h2", "text": "고칠 것 Top 5"},
          {"type": "table", "headers": ["순위", "항목", "오를 수 있는 점수", "걸린 상한", "해제 조건"],
           "rows": [[n, f["name"], f"{f['gain']:g}", ", ".join(f["caps"]) or "-", " / ".join(f["unlock_hints"]) or "-"]
                    for n, f in enumerate(r["fix_priority"], 1)]}]

    names = {i["id"]: i["name"] for i in r["items"]}
    b += [{"type": "h2", "text": "편차 경보"},
          {"type": "list", "items": [f"{names[iid]}: 심사위원 사이 {next(i['spread'] for i in r['items'] if i['id'] == iid):g}점 차이"
                                     for iid in r["deviation_alerts"]]},
          {"type": "h2", "text": "진짜 구멍 (다른 모델도 같은 지적)"},
          {"type": "list", "items": [names[iid] for iid in r["consensus_gaps"]]}]

    b += [{"type": "h2", "text": "항목별"},
          {"type": "table", "headers": ["항목", "득점 / 배점", "심사위원별", "상한", "인용", "변화"],
           "rows": [[i["name"], f"{i['earned']:g} / {i['points_total']:g}",
                     ", ".join(f"{p} {s:g}" for p, s in i["by_persona"].items()),
                     ", ".join(i["caps"]) or "-", " / ".join(i["quotes"]) or "(인용 없음)", _fmt_delta(i["delta"])]
                    for i in r["items"]]}]

    nar = r.get("narrative") or {}
    b += [{"type": "h2", "text": "총평"}, {"type": "p", "text": nar.get("overall") or "(총평 없음)"},
          {"type": "h2", "text": "심사위원별 총평"},
          {"type": "list", "items": [f"{p['name']} ({', '.join(p['groups'])}, {p['model'] or '모델 미기록'}): "
                                     f"{(nar.get('personas') or {}).get(p['name']) or p['summary'] or '-'}"
                                     for p in r["personas"]]}]

    b += [{"type": "h2", "text": "부록"},
          {"type": "p", "text": "추정(inferred) 규칙 — 공고에 없어 에이전트가 정한 것"},
          {"type": "list", "items": r["inferred_rules"]},
          {"type": "p", "text": "실행 정보"},
          {"type": "list", "items": [f"{p['name']}: 모델 {p['model'] or '-'}, 독립 실행 {'예' if p['independent'] else '아니오'}"
                                     for p in r["personas"]]
                                    + [f"제외 {n}: {'; '.join(e[:3])}" for n, e in r["failed"].items()]},
          {"type": "p", "text": "경고"},
          {"type": "list", "items": r["warnings"]}]
    return b


VERDICT_LABEL = {"up": "올림", "same": "그대로", "down": "깎음", None: "-"}
VERDICT_ORDER = {"down": 0, "same": 1}
COST_LABEL = {"low": "낮음", "mid": "중간", "high": "높음"}


def validate_grill(r: dict) -> None:
    if r.get("mode") not in ("practice", "sheet"):
        raise InputError("grill result: mode는 practice/sheet")
    for n, q in enumerate(r.get("questions") or []):
        for qq in [q, *(q.get("follow_ups") or [])]:
            if qq.get("verdict") not in VERDICT_LABEL:
                raise InputError(f"grill result questions[{n}]: verdict는 up/same/down/null")
            if not str(qq.get("question") or "").strip():
                raise InputError(f"grill result questions[{n}]: question이 비어 있음")


def _grill_blocks(r: dict) -> list:
    validate_grill(r)
    mode = "연습" if r["mode"] == "practice" else "질문지"
    b = [{"type": "h1", "text": f"{r['contest']} 질의응답 보고서"},
         {"type": "p", "text": f"{r['created_at']} · {mode} 모드 · 질문 {len(r['questions'])}개"}]
    rows, weak = [], []
    for n, q in enumerate(r["questions"], 1):
        rows.append([n, q["persona"], q["item"], q["question"], q.get("answer") or "-",
                     VERDICT_LABEL[q.get("verdict")], q.get("reason") or "-"])
        if q.get("verdict") in VERDICT_ORDER:
            weak.append((VERDICT_ORDER[q["verdict"]], n, q))
        for m, f in enumerate(q.get("follow_ups") or [], 1):
            rows.append([f"{n}-꼬리{m}", q["persona"], q["item"], f["question"], f.get("answer") or "-",
                         VERDICT_LABEL[f.get("verdict")], f.get("reason") or "-"])
            if f.get("verdict") in VERDICT_ORDER:
                weak.append((VERDICT_ORDER[f["verdict"]], n, f))
    if r["mode"] == "practice":
        b += [{"type": "h2", "text": "질문과 판정"},
              {"type": "table", "headers": ["#", "심사위원", "항목", "질문", "답", "판정", "이유"], "rows": rows},
              {"type": "h2", "text": "약한 답변"},
              {"type": "list", "items": [f"[{VERDICT_LABEL[q['verdict']]}] {q['question']} — {q.get('reason') or '-'}"
                                         for _, _, q in sorted(weak, key=lambda t: (t[0], t[1]))]}]
    else:
        b += [{"type": "h2", "text": "예상 질문지"},
              {"type": "table", "headers": ["#", "심사위원", "항목", "질문", "모범 답변 뼈대"],
               "rows": [[n, q["persona"], q["item"], q["question"], q.get("model_answer") or "-"]
                        for n, q in enumerate(r["questions"], 1)]}]
    b += [{"type": "h2", "text": "자료 수정 제안"},
          {"type": "table", "headers": ["넣을 근거", "항목", "점수 변화"],
           "rows": [[s["evidence"], s["item"], f"{s['from_score']} → {s['to_score']}"] for s in r.get("suggestions") or []]},
          {"type": "h2", "text": "총평"},
          {"type": "p", "text": (r.get("narrative") or {}).get("overall") or "(총평 없음)"}]
    return b


def _ideas_blocks(r: dict) -> list:
    b = [{"type": "h1", "text": f"{r['contest']} 아이디어 비교"},
         {"type": "p", "text": f"{r['created_at']} · 명세대로 완벽히 구현했다고 가정한 상한 점수"},
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
          {"type": "p", "text": (r.get("narrative") or {}).get("overall") or "(총평 없음)"}]
    return b


BUILDERS = {"score": _score_blocks, "grill": _grill_blocks, "ideas": _ideas_blocks}


def build_blocks(result: dict) -> list:
    kind = result.get("kind")
    if kind not in BUILDERS:
        raise InputError(f"result.json kind를 모름: {kind!r}")
    return BUILDERS[kind](result)


def render(result: dict):
    blocks = build_blocks(result)
    return to_markdown(blocks), to_html(blocks, blocks[0]["text"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="보고서 생성")
    ap.add_argument("run_dir")
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir)
    md, html = render(load_json(run_dir / "result.json"))
    (run_dir / "report.md").write_text(md, encoding="utf-8")
    (run_dir / "report.html").write_text(html, encoding="utf-8")
    print(run_dir / "report.md")
    print(run_dir / "report.html")
    return 0


if __name__ == "__main__":
    run_cli(main)
