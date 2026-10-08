"""보고서 블록을 md와 html로 바꾼다.

보고서 내용은 블록 목록 하나로 만들고 두 형식은 여기서만 찍는다 — 두 보고서의 숫자가 어긋나지 않게.
html은 메일·메신저로 그대로 보내도 되도록 외부 요청 없는 파일 하나로 만든다.
"""
from __future__ import annotations

from html import escape

BAR_CHARS = 20


def _md_cell(v) -> str:
    return str(v).replace("|", "\\|").replace("\r", "").replace("\n", " ")


def _md_line(v) -> str:
    return str(v).replace("\r", "").replace("\n", " ")


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
        elif t == "callout":
            body = str(b["text"]).replace("\n", "\n> ")
            out.append(f"> **{_md_line(b['label'])}** {body}")
        elif t == "list":
            out.append("\n".join(f"- {_md_line(x)}" for x in b["items"]) if b["items"] else "- (없음)")
        elif t == "links":
            out.append("\n".join(f"- [{_md_line(x['text'])}]({x['href']})" for x in b["items"])
                       if b["items"] else "- (없음)")
        elif t == "table":
            lines = ["| " + " | ".join(_md_cell(h) for h in b["headers"]) + " |",
                     "|" + "---|" * len(b["headers"])]
            lines += ["| " + " | ".join(_md_cell(c) for c in row) + " |" for row in b["rows"]]
            out.append("\n".join(lines) if b["rows"] else "\n".join(lines[:2]) + "\n\n(없음)")
        elif t == "bars":
            lines = ["| 항목 | 점수 | |", "|---|---|---|"]
            for r in b["rows"]:
                filled = round(r["value"] / r["max"] * BAR_CHARS) if r["max"] else 0
                lines.append(f"| {_md_cell(r['label'])} | {r['value']:g} / {r['max']:g} | "
                             f"{'█' * filled}{'░' * (BAR_CHARS - filled)} |")
            out.append("\n".join(lines))
        else:
            raise ValueError(f"모르는 블록 {t}")
    return "\n\n".join(out) + "\n"


CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--muted:#666;--line:#e3e3e3;--bar:#3b6fd8;--track:#eef1f6;--warn:#b54708;--warn-bg:#fff4e5}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#ececec;--muted:#9a9a9a;--line:#2e2e2e;--bar:#6c9cff;--track:#232833;--warn:#ffb86b;--warn-bg:#2b2116}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}
main{max-width:920px;margin:0 auto;padding:24px 16px 64px}h1{font-size:24px;margin:0 0 8px}h2{font-size:18px;margin:32px 0 8px;padding-top:8px;border-top:1px solid var(--line)}
p{margin:8px 0;white-space:pre-wrap}.callout{background:var(--warn-bg);color:var(--warn);border-radius:8px;padding:10px 14px;margin:8px 0}
.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:600}a{color:var(--bar)}
.bars{margin:8px 0}.bar-row{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,2fr) auto;gap:10px;align-items:center;font-size:14px;margin:6px 0}
.bar-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.track{background:var(--track);border-radius:4px;height:14px}.fill{background:var(--bar);border-radius:4px;height:100%}.bar-value{color:var(--muted);white-space:nowrap}
"""


def _bars_html(rows: list) -> str:
    # SVG viewBox는 폰 폭에서 통째로 줄어 글자가 읽히지 않는다 — 글자 크기가 고정된 grid 행으로 그린다
    parts = ['<div class="bars" role="img">']
    for r in rows:
        ratio = max(0.0, min(1.0, (r["value"] / r["max"]) if r["max"] else 0.0))
        parts.append(f'<div class="bar-row"><span class="bar-label">{escape(str(r["label"]))}</span>'
                     f'<div class="track"><div class="fill" style="width:{ratio * 100:.1f}%"></div></div>'
                     f'<span class="bar-value">{r["value"]:g} / {r["max"]:g}</span></div>')
    parts.append("</div>")
    return "".join(parts)


def to_html(blocks: list, title: str) -> str:
    body = []
    for b in blocks:
        t = b["type"]
        if t in ("h1", "h2", "p"):
            body.append(f"<{t}>{escape(str(b['text']))}</{t}>")
        elif t == "callout":
            body.append(f'<div class="callout"><strong>{escape(str(b["label"]))}</strong> {escape(str(b["text"]))}</div>')
        elif t == "list":
            items = b["items"] or ["(없음)"]
            body.append("<ul>" + "".join(f"<li>{escape(str(x))}</li>" for x in items) + "</ul>")
        elif t == "links":
            items = "".join(f'<li><a href="{escape(x["href"], quote=True)}">{escape(str(x["text"]))}</a></li>'
                            for x in b["items"]) or "<li>(없음)</li>"
            body.append(f"<ul>{items}</ul>")
        elif t == "table":
            head = "".join(f"<th>{escape(str(h))}</th>" for h in b["headers"])
            rows = "".join("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in row) + "</tr>" for row in b["rows"])
            body.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{rows or ""}</tbody></table></div>'
                        + ("" if b["rows"] else "<p>(없음)</p>"))
        elif t == "bars":
            body.append(_bars_html(b["rows"]))
        else:
            raise ValueError(f"모르는 블록 {t}")
    return ("<!doctype html>\n<html lang=\"ko\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{escape(title)}</title><style>{CSS}</style></head>"
            f"<body><main>{''.join(body)}</main></body></html>\n")
