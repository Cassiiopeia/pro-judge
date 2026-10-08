#!/usr/bin/env bash
# 대회가 등록된 레포(docs/pro-judge/ 있음)에서만 길잡이를 주입한다 — 다른 레포의 컨텍스트를 낭비하지 않게
set -euo pipefail
project="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -d "$project/docs/pro-judge" ] || exit 0
guide="${CLAUDE_PLUGIN_ROOT:-}/skills/using-pro-judge/SKILL.md"
[ -f "$guide" ] || exit 0
# 본문 안의 따옴표·줄바꿈을 안전하게 JSON으로 감싸려고 python을 쓴다
python3 - "$guide" <<'PY'
import json, sys
body = open(sys.argv[1], encoding="utf-8").read()
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": body}},
                 ensure_ascii=False))
PY
