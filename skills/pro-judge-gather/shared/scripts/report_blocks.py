"""보고서 블록을 md와 html로 바꾼다.

보고서 내용은 블록 목록 하나로 만들고 두 형식은 여기서만 찍는다 — 두 보고서의 숫자가 어긋나지 않게.
html은 메일·메신저로 그대로 보내도 되도록 외부 요청·스크립트 없는 파일 하나로 만든다.
"""
from __future__ import annotations

from html import escape

BAR_CHARS = 20
BRAND = "PRO-Judge"
# 비율 구간 — 0/5/10 앵커 사이에서 "5점 기준 아래", "5~7", "7 이상"으로 나눈다
LEVELS = ((0.4, "lv-low"), (0.7, "lv-mid"), (1.01, "lv-high"))


def level_class(ratio: float) -> str:
    return next(c for limit, c in LEVELS if ratio < limit)


def _ratio(value, maximum) -> float:
    return max(0.0, min(1.0, (value / maximum) if maximum else 0.0))


def _md_cell(v) -> str:
    return str(v).replace("|", "\\|").replace("\r", "").replace("\n", " ")


def _md_line(v) -> str:
    return str(v).replace("\r", "").replace("\n", " ")


def _md_table(headers: list, rows: list) -> str:
    lines = ["| " + " | ".join(_md_cell(h) for h in headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(_md_cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines) if rows else "\n".join(lines[:2]) + "\n\n(없음)"


def _fix_md(n: int, f: dict) -> str:
    parts = [f"{n}. **{_md_line(f['name'])}** +{f['gain']:g}점 ({_md_line(f['now'])})"]
    for key, label in (("anchor", "다음 기준"), ("caps", "걸린 상한"), ("hint", "해제 조건")):
        if f.get(key):
            parts.append(f"   - {label}: {_md_line(f[key])}")
    return "\n".join(parts)


QA_HEADERS = {"practice": ["#", "심사위원", "항목", "질문", "답", "판정", "이유"],
              "sheet": ["#", "심사위원", "항목", "질문", "모범 답변 뼈대"]}


def _qa_row(q: dict, mode: str) -> list:
    base = [q["no"], q["who"], q["item"], q["question"]]
    if mode == "sheet":
        return base + [q.get("model_answer") or "-"]
    return base + [q.get("answer") or "-", q.get("verdict_label") or "-", q.get("reason") or "-"]


def to_markdown(blocks: list) -> str:
    out = []
    for b in blocks:
        t = b["type"]
        if t == "h1":
            out.append(f"# {_md_line(b['text'])}")
        elif t == "h2":
            out.append(f"## {_md_line(b['text'])}")
        elif t == "p":
            out.append(str(b["text"]))
        elif t == "meta":
            out.append(" · ".join(_md_line(x) for x in b["items"]))
        elif t == "callout":
            body = str(b["text"]).replace("\n", "\n> ")
            out.append(f"> **{_md_line(b['label'])}** {body}")
        elif t == "notice":
            out.append(f"> **{_md_line(b['label'])}**\n" + "\n".join(
                f"> - **{_md_line(x['label'])}** {_md_line(x['text'])}" for x in b["items"]))
        elif t == "hero":
            lines = [f"**{b['score']:.1f}** / {b['max']:g}"] + [_md_line(s) for s in b.get("sub") or []]
            if b.get("top_fix"):
                f = b["top_fix"]
                lines.append(f"가장 먼저 고칠 것: **{_md_line(f['name'])}** +{f['gain']:g}점")
            out.append("\n\n".join(lines))
        elif t == "list":
            out.append("\n".join(f"- {_md_line(x)}" for x in b["items"]) if b["items"] else "- (없음)")
        elif t == "links":
            out.append("\n".join(f"- [{_md_line(x['text'])}]({x['href']})" for x in b["items"])
                       if b["items"] else "- (없음)")
        elif t == "table":
            out.append(_md_table(b["headers"], b["rows"]))
        elif t == "bars":
            lines = ["| 항목 | 점수 | |", "|---|---|---|"]
            for r in b["rows"]:
                filled = round(_ratio(r["value"], r["max"]) * BAR_CHARS)
                lines.append(f"| {_md_cell(r['label'])} | {r['value']:g} / {r['max']:g} | "
                             f"{'█' * filled}{'░' * (BAR_CHARS - filled)} |")
            out.append("\n".join(lines))
        elif t == "fixes":
            out.append("\n".join(_fix_md(n, f) for n, f in enumerate(b["items"], 1)) or "(없음)")
        elif t == "cards":
            out.append("\n".join(f"- **{_md_line(c['title'])}**" + (f" ({_md_line(c['sub'])})" if c.get("sub") else "")
                                 + f": {_md_line(c['text'])}" for c in b["items"]) or "- (없음)")
        elif t == "qa":
            out.append(_md_table(QA_HEADERS[b["mode"]], [_qa_row(q, b["mode"]) for q in b["items"]]))
        else:
            raise ValueError(f"모르는 블록 {t}")
    return "\n\n".join(out) + "\n"


# 브랜드 색은 사이트와 같은 붉은 펜 색. 점수 구간 색은 색약을 고려해 명도 차이도 함께 둔다
CSS = """
:root{--bg:#f6f5f2;--card:#fff;--fg:#1d1d1f;--muted:#6b6b70;--line:#e6e3dd;--brand:#b4232a;--brand-soft:#fbeaea;
--low:#c8322b;--mid:#d9822b;--high:#2f8f5b;--track:#ece9e3;--warn:#8a4b08;--warn-bg:#fff6e8;--shadow:0 1px 2px rgba(0,0,0,.04),0 8px 24px rgba(0,0,0,.06)}
@media (prefers-color-scheme:dark){:root{--bg:#121214;--card:#1c1c1f;--fg:#ececee;--muted:#a0a0a8;--line:#2c2c31;--brand:#f2706a;--brand-soft:#3a1f1f;
--low:#f0675f;--mid:#f0a050;--high:#4fc283;--track:#2a2a2f;--warn:#ffc27a;--warn-bg:#2b2318;--shadow:none}}
*{box-sizing:border-box}html{word-break:keep-all;overflow-wrap:break-word}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.65 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Pretendard","Noto Sans KR",sans-serif}
main{max-width:960px;margin:0 auto;padding:28px 16px 48px}
.brand{font-size:12px;font-weight:700;letter-spacing:.04em;color:var(--brand);margin:0 0 6px}
h1{font-size:26px;line-height:1.3;margin:0 0 10px}
h2{font-size:18px;margin:40px 0 12px;display:flex;align-items:center;gap:8px}
h2::before{content:"";width:4px;height:18px;border-radius:2px;background:var(--brand)}
p{margin:8px 0;white-space:pre-wrap}.muted{color:var(--muted)}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 18px;padding:0;list-style:none}
.meta li{font-size:13px;color:var(--muted);background:var(--card);border:1px solid var(--line);border-radius:999px;padding:2px 10px}
.hero{display:grid;grid-template-columns:auto minmax(0,1fr);gap:24px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:24px;box-shadow:var(--shadow)}
.ring{--c:var(--mid);width:148px;height:148px;border-radius:50%;display:grid;place-items:center;
background:radial-gradient(closest-side,var(--card) 79%,transparent 80% 100%),conic-gradient(var(--c) calc(var(--p)*1%),var(--track) 0)}
.ring.lv-low{--c:var(--low)}.ring.lv-high{--c:var(--high)}
.ring-in{text-align:center;line-height:1.1}.hero-score{font-size:40px;font-weight:800;letter-spacing:-.02em}.hero-max{display:block;font-size:13px;color:var(--muted);margin-top:4px}
.hero-caption{font-weight:700;margin:0 0 6px}.hero-sub{margin:0;padding:0;list-style:none;color:var(--muted);font-size:14px}
.top-fix{margin-top:14px;border-radius:12px;background:var(--brand-soft);padding:12px 14px}
.top-fix .k{font-size:12px;font-weight:700;color:var(--brand)}.top-fix .v{font-weight:700}.gain{color:var(--brand);font-weight:800;white-space:nowrap}
.notice{margin:14px 0 0;background:var(--warn-bg);color:var(--warn);border-radius:12px;padding:10px 16px;font-size:14px}
.notice summary{cursor:pointer;font-weight:700}.notice ul{margin:8px 0 4px;padding-left:18px}.notice li{margin:4px 0}
.callout{background:var(--warn-bg);color:var(--warn);border-radius:10px;padding:10px 14px;margin:8px 0}
.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow)}
.bar-row{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,2fr) 6.5em;gap:12px;align-items:center;font-size:14px;margin:9px 0}
.bar-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.track{background:var(--track);border-radius:6px;height:12px;overflow:hidden}
.fill{height:100%;border-radius:6px;background:var(--mid)}.fill.lv-low{background:var(--low)}.fill.lv-high{background:var(--high)}
.bar-value{color:var(--muted);white-space:nowrap;text-align:right;font-variant-numeric:tabular-nums}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:var(--muted);margin-top:10px}.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:4px;vertical-align:-1px}
.fixes{display:grid;gap:10px}.fix{display:grid;grid-template-columns:2.2em minmax(0,1fr) auto;gap:12px;align-items:start;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.fix .n{width:2em;height:2em;border-radius:50%;display:grid;place-items:center;background:var(--brand-soft);color:var(--brand);font-weight:800}
.fix .t{font-weight:700}.fix .now{color:var(--muted);font-size:13px;font-weight:400;margin-left:6px}.fix dl{margin:6px 0 0;font-size:14px}.fix dt{color:var(--muted);font-size:12px;margin-top:6px}.fix dd{margin:0}
.fix .gain{font-size:20px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;font-size:14px}.card .t{font-weight:700}.card .s{color:var(--muted);font-size:12px;margin-bottom:6px}
.qa{display:grid;gap:10px}.q{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;font-size:14px}
.q.follow{margin-left:24px;border-style:dashed}.q .who{color:var(--muted);font-size:12px}.q .qt{font-weight:700;font-size:15px;margin:4px 0 8px}
.q .ans{border-left:3px solid var(--line);padding:2px 0 2px 10px;margin:6px 0;white-space:pre-wrap}
.badge{display:inline-block;font-size:12px;font-weight:700;border-radius:999px;padding:1px 9px;margin-left:6px}.v-up{background:#e3f4ea;color:#1f6b42}.v-same{background:#f1efe9;color:#6b6b70}.v-down{background:#fbe4e2;color:#a3261f}
.table-wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:14px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border-bottom:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top}
tr:last-child td{border-bottom:0}th{color:var(--muted);font-weight:600;font-size:13px;white-space:nowrap}a{color:var(--brand)}
ul.plain{padding-left:20px}footer{margin-top:48px;padding-top:16px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
@media (max-width:560px){h1{font-size:22px}.hero{grid-template-columns:1fr;justify-items:center;text-align:center;padding:20px}
.hero-sub{text-align:center}.top-fix{text-align:left;width:100%}.bar-row{grid-template-columns:minmax(0,1fr) 5.5em;row-gap:4px}
.bar-row .track{grid-column:1/-1;grid-row:2}.fix{grid-template-columns:2.2em minmax(0,1fr)}.fix .gain{grid-column:2}.q.follow{margin-left:12px}}
@media print{body{background:#fff}.hero,.panel,.fix,.card,.q,.table-wrap{box-shadow:none;break-inside:avoid}.notice{display:block}details.notice>*{display:block}
main{max-width:none;padding:0}h2{break-after:avoid}}
"""


def _bars_html(b: dict) -> str:
    # SVG viewBox는 폰 폭에서 통째로 줄어 글자가 읽히지 않는다 — 글자 크기가 고정된 grid 행으로 그린다
    rows = b["rows"]
    top = max((r["max"] for r in rows), default=0)
    parts = ['<div class="bars panel" role="img">']
    for r in rows:
        ratio = _ratio(r["value"], r["max"])
        # scale이면 트랙 길이를 배점에 비례시킨다 — 20점 항목의 2점과 5점 항목의 2점이 같아 보이지 않게
        track = f' style="width:{(r["max"] / top * 100) if b.get("scale") and top else 100:.1f}%"'
        parts.append(f'<div class="bar-row"><span class="bar-label">{escape(str(r["label"]))}</span>'
                     f'<div class="track"{track}><div class="fill {level_class(ratio)}" style="width:{ratio * 100:.1f}%"></div></div>'
                     f'<span class="bar-value">{r["value"]:g} / {r["max"]:g}</span></div>')
    if b.get("scale"):
        parts.append('<div class="legend"><span>막대 길이 = 배점</span><span><i style="background:var(--low)"></i>40% 미만</span>'
                     '<span><i style="background:var(--mid)"></i>40~70%</span><span><i style="background:var(--high)"></i>70% 이상</span></div>')
    parts.append("</div>")
    return "".join(parts)


def _hero_html(b: dict) -> str:
    ratio = _ratio(b["score"], b["max"])
    sub = "".join(f"<li>{escape(str(s))}</li>" for s in b.get("sub") or [])
    fix = ""
    if b.get("top_fix"):
        f = b["top_fix"]
        fix = (f'<div class="top-fix"><div class="k">가장 먼저 고칠 것</div>'
               f'<div><span class="v">{escape(str(f["name"]))}</span> <span class="gain">+{f["gain"]:g}점</span></div>'
               + (f'<div class="muted">{escape(str(f["anchor"]))}</div>' if f.get("anchor") else "") + "</div>")
    return (f'<section class="hero"><div class="ring {level_class(ratio)}" style="--p:{ratio * 100:.1f}">'
            f'<div class="ring-in"><span class="hero-score">{b["score"]:.1f}</span>'
            f'<span class="hero-max">/ {b["max"]:g}</span></div></div>'
            f'<div><p class="hero-caption">{escape(str(b.get("caption") or ""))}</p><ul class="hero-sub">{sub}</ul>{fix}</div></section>')


def _fix_html(n: int, f: dict) -> str:
    dl = "".join(f"<dt>{label}</dt><dd>{escape(str(f[key]))}</dd>"
                 for key, label in (("anchor", "다음 기준 문장 — 이 문장이 자료에 생기게 만든다"), ("caps", "걸린 상한"), ("hint", "해제 조건"))
                 if f.get(key))
    return (f'<div class="fix"><span class="n">{n}</span><div><span class="t">{escape(str(f["name"]))}</span>'
            f'<span class="now">{escape(str(f["now"]))}</span><dl>{dl}</dl></div><span class="gain">+{f["gain"]:g}점</span></div>')


VERDICT_CLASS = {"올림": "v-up", "그대로": "v-same", "깎음": "v-down"}


def _qa_html(b: dict) -> str:
    parts = ['<div class="qa">']
    for q in b["items"]:
        badge = (f'<span class="badge {VERDICT_CLASS.get(q.get("verdict_label"), "v-same")}">{escape(q["verdict_label"])}</span>'
                 if q.get("verdict_label") else "")
        if b["mode"] == "sheet":
            body = f'<div class="ans">{escape(str(q.get("model_answer") or "-"))}</div>'
        else:
            body = (f'<div class="ans">{escape(str(q.get("answer") or "(답 없음)"))}</div>'
                    + (f'<div class="muted">{escape(str(q["reason"]))}</div>' if q.get("reason") else ""))
        parts.append(f'<div class="q{" follow" if q.get("follow") else ""}"><div class="who">{escape(str(q["no"]))} · '
                     f'{escape(str(q["who"]))} · {escape(str(q["item"]))}{badge}</div>'
                     f'<div class="qt">{escape(str(q["question"]))}</div>{body}</div>')
    parts.append("</div>")
    return "".join(parts) if b["items"] else "<p>(없음)</p>"


def to_html(blocks: list, title: str, footer: str = "") -> str:
    body = [f'<p class="brand">{BRAND}</p>']
    for b in blocks:
        t = b["type"]
        if t in ("h1", "h2"):
            body.append(f"<{t}>{escape(str(b['text']))}</{t}>")
        elif t == "p":
            body.append(f'<p{" class=\"muted\"" if b.get("muted") else ""}>{escape(str(b["text"]))}</p>')
        elif t == "meta":
            body.append('<ul class="meta">' + "".join(f"<li>{escape(str(x))}</li>" for x in b["items"]) + "</ul>")
        elif t == "callout":
            body.append(f'<div class="callout"><strong>{escape(str(b["label"]))}</strong> {escape(str(b["text"]))}</div>')
        elif t == "notice":
            items = "".join(f"<li><strong>{escape(str(x['label']))}</strong> {escape(str(x['text']))}</li>" for x in b["items"])
            body.append(f'<details class="notice"><summary>{escape(str(b["label"]))}</summary><ul>{items}</ul></details>')
        elif t == "hero":
            body.append(_hero_html(b))
        elif t == "list":
            items = b["items"] or ["(없음)"]
            body.append('<ul class="plain">' + "".join(f"<li>{escape(str(x))}</li>" for x in items) + "</ul>")
        elif t == "links":
            items = "".join(f'<li><a href="{escape(x["href"], quote=True)}">{escape(str(x["text"]))}</a></li>'
                            for x in b["items"]) or "<li>(없음)</li>"
            body.append(f'<ul class="plain">{items}</ul>')
        elif t == "table":
            head = "".join(f"<th>{escape(str(h))}</th>" for h in b["headers"])
            rows = "".join("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in row) + "</tr>" for row in b["rows"])
            body.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{rows or ""}</tbody></table></div>'
                        + ("" if b["rows"] else "<p>(없음)</p>"))
        elif t == "bars":
            body.append(_bars_html(b))
        elif t == "fixes":
            body.append('<div class="fixes">' + "".join(_fix_html(n, f) for n, f in enumerate(b["items"], 1)) + "</div>"
                        if b["items"] else "<p>(없음)</p>")
        elif t == "cards":
            body.append('<div class="cards">' + "".join(
                f'<div class="card"><div class="t">{escape(str(c["title"]))}</div>'
                + (f'<div class="s">{escape(str(c["sub"]))}</div>' if c.get("sub") else "")
                + f'<div>{escape(str(c["text"]))}</div></div>' for c in b["items"]) + "</div>")
        elif t == "qa":
            body.append(_qa_html(b))
        else:
            raise ValueError(f"모르는 블록 {t}")
    foot = f"<footer>{BRAND}로 만든 보고서" + (f" · {escape(footer)}" if footer else "") + "</footer>"
    return ("<!doctype html>\n<html lang=\"ko\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{escape(title)}</title><style>{CSS}</style></head>"
            f"<body><main>{''.join(body)}{foot}</main></body></html>\n")
