#!/usr/bin/env python3
"""페르소나 문서 검사기.

상상으로 만든 심사위원을 막으려고 '왜 이 사람이 심사위원인가'를 포함한 필수 칸을 강제한다.
사용: python3 validate_persona.py <대회 폴더>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import InputError, load_yaml, parse_yaml_text, run_cli  # noqa: E402

REQUIRED_SECTIONS = ("누구인가", "심사위원 근거", "무겁게 보는 항목", "인정하는 근거",
                     "감점 트리거", "단골 질문", "말투")
STRICTNESS = {"lenient", "normal", "strict"}
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def _sections(body: str) -> dict:
    sections: dict = {}
    current = None
    for line in body.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def validate_persona(text: str, stem: str, rubric: dict | None = None) -> list:
    text = text.replace("\r\n", "\n")
    m = FRONTMATTER.match(text)
    if not m:
        return [f"{stem}: 맨 위 --- 머리말(frontmatter)이 없음"]
    try:
        meta = parse_yaml_text(m.group(1), f"{stem} 머리말")
    except InputError as e:
        return [str(e)]
    if not isinstance(meta, dict):
        return [f"{stem}: 머리말은 매핑이어야 함"]

    errors = []
    if meta.get("name") != stem:
        errors.append(f"{stem}: name({meta.get('name')!r})이 파일명과 다름")
    if meta.get("strictness") not in STRICTNESS:
        errors.append(f"{stem}: strictness는 {'/'.join(sorted(STRICTNESS))} 중 하나여야 함")
    group = meta.get("group")
    if not group:
        errors.append(f"{stem}: group 없음")
    elif rubric is not None:
        members = {g.get("id"): g.get("personas") or []
                   for g in rubric.get("evaluator_groups") or [] if isinstance(g, dict)}
        if group not in members:
            errors.append(f"{stem}: rubric에 없는 group {group!r}")
        elif stem not in members[group]:
            errors.append(f"{stem}: rubric의 {group} 그룹 personas 목록에 없음")

    sections = _sections(text[m.end():])
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            errors.append(f"{stem}: '## {name}' 칸 없음")
        elif not sections[name].strip():
            errors.append(f"{stem}: '## {name}' 칸이 비어 있음")
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="페르소나 검사")
    ap.add_argument("contest_dir")
    args = ap.parse_args(argv)
    contest = Path(args.contest_dir)
    rubric_path = contest / "rubric.yaml"
    rubric = load_yaml(rubric_path) if rubric_path.is_file() else None
    files = sorted((contest / "personas").glob("*.md"))
    if not files:
        print("personas/에 페르소나가 없음")
        return 1
    errors = []
    for f in files:
        errors += validate_persona(f.read_text(encoding="utf-8"), f.stem,
                                   rubric if isinstance(rubric, dict) else None)
    if errors:
        for e in errors:
            print(f"- {e}")
        print(f"실패: {len(errors)}건")
        return 1
    print(f"OK ({len(files)}명)")
    return 0


if __name__ == "__main__":
    run_cli(main)
