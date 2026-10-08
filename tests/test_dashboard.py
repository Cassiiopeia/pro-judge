from datetime import datetime

from _common import load_yaml, write_json
from aggregate import aggregate
from contest_dirs import new_run
import render_dashboard
from factories import base_results


def make_run(contest_dir, when, gate, with_report=True):
    run = new_run(contest_dir, "score", when)
    r = aggregate(load_yaml(contest_dir / "rubric.yaml"), base_results(gate=gate), run=run.name)
    write_json(run / "result.json", r)
    if with_report:
        (run / "report.html").write_text("x", encoding="utf-8")
    return run


def test_dashboard(contest_dir):
    a = make_run(contest_dir, datetime(2026, 10, 8, 9, 0), 5)
    b = make_run(contest_dir, datetime(2026, 10, 9, 9, 0), 8)
    (new_run(contest_dir, "score", datetime(2026, 10, 10, 9, 0)))  # result 없는 런은 건너뛴다
    history, html = render_dashboard.build(contest_dir)
    assert history.index(a.name) < history.index(b.name)
    assert "52.7" in history and "62.0" in history and "+9.3" in history
    assert f'href="runs/{b.name}/report.html"' in html
    assert html.index(b.name + "/report.html") < html.index(a.name + "/report.html")  # 최근 보고서가 위


def test_empty(contest_dir):
    history, html = render_dashboard.build(contest_dir)
    assert "아직 채점 회차가 없음" in history and "<!doctype html>" in html


def test_cli(contest_dir):
    make_run(contest_dir, datetime(2026, 10, 8, 9, 0), 8)
    assert render_dashboard.main([str(contest_dir)]) == 0
    assert (contest_dir / "history.md").is_file() and (contest_dir / "index.html").is_file()
