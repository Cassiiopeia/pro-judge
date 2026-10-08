"""pro-judge 스크립트 공용 입출력.

외부 의존이 PyYAML 하나라, 없거나 문법이 틀렸을 때 traceback 대신 고칠 방법을 말한다.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Callable


class InputError(Exception):
    """사용자가 고칠 수 있는 입력 오류. CLI는 메시지 한 줄만 찍고 끝낸다."""


def parse_yaml_text(text: str, where: str) -> Any:
    try:
        import yaml
    except ImportError:
        raise InputError("PyYAML이 필요합니다: python3 -m pip install pyyaml")
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise InputError(f"{where}: YAML 문법 오류 — {e}")


def load_yaml(path: Path) -> Any:
    return parse_yaml_text(Path(path).read_text(encoding="utf-8"), str(path))


def load_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise InputError(f"{path}: JSON 문법 오류 — {e}")


def write_json(path: Path, data: Any) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_cli(main: Callable[[], int]) -> None:
    try:
        sys.exit(main())
    except InputError as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(2)


RUN_KINDS = ("score", "grill", "ideas")
# 같은 분에 두 번 돌면 -2, -3을 붙인다. 정렬은 (시각, 번호)로 해서 문자열 정렬 함정을 피한다
RUN_NAME = re.compile(r"^(\d{8}-\d{4})_(score|grill|ideas)(?:-(\d+))?$")


def parse_run_name(name: str):
    m = RUN_NAME.match(name)
    if not m:
        return None
    return m.group(1), m.group(2), int(m.group(3) or 1)


def list_runs(contest_dir: Path, kind: str | None = None) -> list:
    runs = Path(contest_dir) / "runs"
    if not runs.is_dir():
        return []
    found = []
    for p in runs.iterdir():
        parsed = parse_run_name(p.name) if p.is_dir() else None
        if parsed and (kind is None or parsed[1] == kind):
            found.append((parsed[0], parsed[2], p))
    return [p for _, _, p in sorted(found, key=lambda t: (t[0], t[1]))]
