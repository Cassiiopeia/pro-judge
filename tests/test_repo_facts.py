"""저장소 사실 추출 — 임시 git 저장소로 기간·작성자·건강 파일·fork 원본 대비 팀 커밋을 확인한다."""
import os
import subprocess

import pytest

from _common import InputError
import repo_facts as rf


def git(d, *a, date=None, author="Kim"):
    env = {**os.environ, "GIT_AUTHOR_NAME": author, "GIT_AUTHOR_EMAIL": f"{author}@x", "GIT_COMMITTER_NAME": author,
           "GIT_COMMITTER_EMAIL": f"{author}@x"}
    if date:
        env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True, env=env)


def commit(d, name, body, date, author="Kim"):
    p = d / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    git(d, "add", name)
    git(d, "commit", "-q", "-m", name, date=date, author=author)


@pytest.fixture
def repo(tmp_path):
    d = tmp_path / "team"
    d.mkdir()
    git(d, "init", "-q", "-b", "main")
    commit(d, "README.md", "# 팀 프로젝트\n설치: npm i\n", "2025-04-01T10:00:00")
    commit(d, "LICENSE", "MIT License\nCopyright", "2025-06-01T10:00:00", author="Lee")
    commit(d, "tests/test_a.py", "def test(): pass\n", "2025-07-01T10:00:00")
    commit(d, ".github/workflows/ci.yml", "on: push\n", "2025-07-02T10:00:00", author="Lee")
    return d


def test_facts_period_authors_and_health_files(repo):
    text = rf.facts(repo, since="2025-05-20", until="2025-12-05")
    assert "전체 커밋 4개" in text
    assert "기간 커밋 3개, 작성자 2명" in text and "Lee 2" in text
    assert "LICENSE: LICENSE" in text and "MIT License" in text
    assert "테스트로 보이는 파일 1개" in text and ".github/workflows/ci.yml" in text
    assert "CONTRIBUTING: 없음" in text
    assert "# 팀 프로젝트" in text  # README 원문이 들어가야 인용 대조가 된다


def test_fork_counts_only_team_commits(tmp_path):
    up = tmp_path / "upstream"
    up.mkdir()
    git(up, "init", "-q", "-b", "main")
    for n in range(5):
        commit(up, f"core{n}.c", "x", f"2025-06-0{n + 1}T10:00:00", author="Upstream")
    fork = tmp_path / "fork"
    subprocess.run(["git", "clone", "-q", str(up), str(fork)], check=True)
    for n in range(3):
        commit(fork, f"port{n}.c", "y", f"2025-08-0{n + 1}T10:00:00", author="Team")
    text = rf.facts(fork, since="2025-05-20", until="2025-12-05", upstream=str(up))
    assert "원본 대비 팀 커밋 3개" in text and "Team 3" in text
    assert "기간 커밋 8개" in text  # 원본 커밋까지 섞인 숫자 — 그래서 원본 비교를 따로 보여 준다


def test_bad_upstream_is_noted_not_fatal(repo, tmp_path):
    text = rf.facts(repo, upstream=str(tmp_path / "없음"))
    assert "fork 원본 비교 실패" in text and "전체 커밋 4개" in text


def test_not_a_git_repo(tmp_path):
    with pytest.raises(InputError, match="git 저장소"):
        rf.facts(tmp_path)


def test_cli_writes_out(repo, tmp_path):
    out = tmp_path / "run" / "target" / "team.txt"
    assert rf.main([str(repo), "--out", str(out)]) == 0
    assert "전체 커밋 4개" in out.read_text(encoding="utf-8")


def test_fork_team_work_on_other_branches(tmp_path):
    # 실측(tsnlab/zephyr): 기본 브랜치는 원본과 같고 팀 작업은 별도 브랜치 수십 개에 있다 — HEAD만 비교하면 0개가 된다
    up = tmp_path / "upstream"
    up.mkdir()
    git(up, "init", "-q", "-b", "main")
    commit(up, "core.c", "x", "2025-06-01T10:00:00", author="Upstream")
    team_remote = tmp_path / "team-remote"
    subprocess.run(["git", "clone", "-q", str(up), str(team_remote)], check=True)
    git(team_remote, "checkout", "-q", "-b", "rpi5-port")
    for n in range(3):
        commit(team_remote, f"port{n}.c", "y", f"2025-08-0{n + 1}T10:00:00", author="Team")
    git(team_remote, "checkout", "-q", "main")
    fork = tmp_path / "fork"
    subprocess.run(["git", "clone", "-q", str(team_remote), str(fork)], check=True)
    text = rf.facts(fork, upstream=str(up))
    assert "원본 대비 팀 커밋 3개" in text and "Team 3" in text
    assert "rpi5-port 3" in text  # 어느 브랜치에 팀 작업이 있는지
