import json
import os
import subprocess
import sys

from conftest import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import sync_shared  # noqa: E402


def make_tree(root):
    (root / "shared" / "scripts").mkdir(parents=True)
    (root / "shared" / "scripts" / "a.py").write_text("print(1)\n")
    for s in sync_shared.TARGET_SKILLS:
        (root / "skills" / s).mkdir(parents=True)


def test_sync_and_check(tmp_path):
    make_tree(tmp_path)
    assert sync_shared.check(tmp_path)  # 아직 사본 없음
    sync_shared.sync(tmp_path)
    assert sync_shared.check(tmp_path) == []
    (tmp_path / "shared" / "scripts" / "a.py").write_text("print(2)\n")
    assert any(d.endswith("scripts/a.py") for d in sync_shared.check(tmp_path))


def test_repo_copies_in_sync():
    assert sync_shared.check(ROOT) == [], "python3 tools/sync_shared.py 를 실행할 것"


def test_plugin_manifests():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert plugin["name"] == "pro-judge"
    assert market["plugins"][0]["name"] == "pro-judge" and market["plugins"][0]["source"] == "./"
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())
    assert "SessionStart" in hooks["hooks"]


def test_plugin_version_not_pinned():
    # 버전의 기준은 version.yml 하나다. plugin.json에 version이 남으면 릴리스 때 올라가지 않아
    # Claude Code가 같은 버전으로 보고 새 커밋을 업데이트로 받지 않는다 — 비워 두면 커밋 SHA로 판단한다
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert "version" not in plugin
    assert "version" not in market["plugins"][0]
    assert (ROOT / "version.yml").is_file()


def run_hook(project_dir):
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(ROOT), "CLAUDE_PROJECT_DIR": str(project_dir)}
    return subprocess.run(["bash", str(ROOT / "hooks" / "session-start.sh")],
                          capture_output=True, text=True, env=env, check=True).stdout


def test_hook_silent_without_contest(tmp_path):
    assert run_hook(tmp_path) == ""


def test_hook_injects_guide(tmp_path):
    (tmp_path / "docs" / "pro-judge").mkdir(parents=True)
    out = json.loads(run_hook(tmp_path))
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "pro-judge 길잡이" in ctx


def contest_type_sources(root):
    """대회 종류 목록이 적힌 세 곳 — 하나만 고치면 검사기와 문서가 어긋난다."""
    import re
    profiles = {p.stem for p in (root / "shared" / "references" / "contest-types").glob("*.md")}
    schema_line = next(l for l in (root / "shared" / "references" / "rubric-schema.md").read_text(encoding="utf-8").splitlines()
                       if "purpose.contest_types" in l)
    schema = set(re.findall(r"[a-z]+(?:-[a-z]+)*", schema_line.split("|")[3])) - {"중"}
    validator = set(re.search(r"CONTEST_TYPES = \{([^}]*)\}",
                              (root / "shared" / "scripts" / "validate_rubric.py").read_text(encoding="utf-8")).group(1)
                    .replace('"', "").replace(" ", "").split(","))
    return profiles, schema, validator


def test_contest_types_listed_everywhere():
    profiles, schema, validator = contest_type_sources(ROOT)
    assert profiles == schema == validator, "대회 종류를 추가했으면 CONTRIBUTING.md의 '대회 종류 추가' 세 곳을 모두 고칠 것"


def test_contest_type_check_catches_drift(tmp_path):
    import shutil
    for d in ("shared/references", "shared/scripts"):
        shutil.copytree(ROOT / d, tmp_path / d)
    (tmp_path / "shared/references/contest-types/sports.md").write_text("# sports\n", encoding="utf-8")
    profiles, schema, validator = contest_type_sources(tmp_path)
    assert profiles != schema


def test_every_script_skill_gets_shared_copy():
    # SKILL.md가 $SKILL/shared/를 쓰는데 동기화 대상에서 빠지면 설치본에 스크립트가 없다
    using = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md") if "$SKILL/shared/" in p.read_text(encoding="utf-8")}
    assert using <= set(sync_shared.TARGET_SKILLS), using - set(sync_shared.TARGET_SKILLS)
    assert "pro-judge-gather" in using
