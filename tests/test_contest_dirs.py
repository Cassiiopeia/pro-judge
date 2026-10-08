import subprocess
from datetime import datetime

import pytest

from _common import InputError, list_runs, parse_run_name
import contest_dirs
from contest_dirs import init_contest, new_run, slugify

NOW = datetime(2026, 10, 8, 14, 5)


def test_slugify():
    assert slugify("  2026 장애인/해커톤: 본선 ") == "2026-장애인-해커톤-본선"
    with pytest.raises(InputError):
        slugify(" / ")


def test_init_creates_gitignore(tmp_path):
    contest, notices = init_contest(tmp_path, "테스트 대회")
    assert contest == tmp_path / "docs" / "pro-judge" / "테스트-대회"
    assert (contest / "personas").is_dir() and (contest / "runs").is_dir()
    assert (tmp_path / "docs" / "pro-judge" / ".gitignore").read_text() == "*\n"
    assert notices == []


def test_init_keeps_existing_gitignore(tmp_path):
    base = tmp_path / "docs" / "pro-judge"
    base.mkdir(parents=True)
    (base / ".gitignore").write_text("custom\n")
    init_contest(tmp_path, "a")
    assert (base / ".gitignore").read_text() == "custom\n"


def test_init_warns_tracked_files(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    f = tmp_path / "docs" / "pro-judge" / "old.md"
    f.parent.mkdir(parents=True)
    f.write_text("x")
    subprocess.run(["git", "-C", str(tmp_path), "add", "docs/pro-judge/old.md"], check=True)
    _, notices = init_contest(tmp_path, "a")
    assert notices and "추적 중" in notices[0]
    assert f.read_text() == "x"


def test_new_run_same_minute(tmp_path):
    a = new_run(tmp_path, "score", NOW)
    b = new_run(tmp_path, "score", NOW)
    c = new_run(tmp_path, "score", NOW)
    assert [a.name, b.name, c.name] == ["20261008-1405_score", "20261008-1405_score-2", "20261008-1405_score-3"]
    assert [p.name for p in list_runs(tmp_path, "score")] == [a.name, b.name, c.name]


def test_new_run_bad_kind(tmp_path):
    with pytest.raises(InputError):
        new_run(tmp_path, "vote", NOW)


def test_list_runs_order_and_filter(tmp_path):
    new_run(tmp_path, "score", datetime(2026, 10, 9, 9, 0))
    new_run(tmp_path, "grill", datetime(2026, 10, 8, 9, 0))
    new_run(tmp_path, "score", datetime(2026, 10, 8, 9, 0))
    (tmp_path / "runs" / "잡동사니").mkdir()
    assert [p.name for p in list_runs(tmp_path, "score")] == ["20261008-0900_score", "20261009-0900_score"]
    assert len(list_runs(tmp_path)) == 3


def test_parse_run_name():
    assert parse_run_name("20261008-1405_ideas-2") == ("20261008-1405", "ideas", 2)
    assert parse_run_name("20261008-1405_score") == ("20261008-1405", "score", 1)
    assert parse_run_name("x_score") is None


def test_cli(tmp_path, capsys):
    assert contest_dirs.main(["init", str(tmp_path), "대회"]) == 0
    path = capsys.readouterr().out.strip().splitlines()[-1]
    assert contest_dirs.main(["new-run", path, "grill"]) == 0
    assert capsys.readouterr().out.strip().endswith("_grill")
