"""에이전트가 손으로 쓰는 JSON이 틀려도 traceback 없이 사람이 읽는 오류나 부분 합산으로 끝나는지."""
import copy

import pytest

from _common import InputError, load_json, load_yaml, run_cli, write_json
import aggregate
from aggregate import aggregate as agg
from contest_dirs import new_run
from render_report import render
from factories import base_results
from test_render_grill_ideas import GRILL


def test_broken_json_file_excludes_only_that_persona(contest_dir):
    run = new_run(contest_dir, "score")
    for res in base_results():
        write_json(run / f"{res['persona']}.json", res)
    (run / "domain-expert.json").write_text('{"persona": "domain-expert", "runs": [', encoding="utf-8")
    assert aggregate.main([str(run)]) == 0
    out = load_json(run / "result.json")
    assert out["participation"] == {"expected": 3, "succeeded": 2}
    assert "JSON 문법 오류" in out["failed"]["domain-expert"][0]


def test_quotes_string_is_one_quote(contest_dir):
    rubric = load_yaml(contest_dir / "rubric.yaml")
    results = base_results()
    results[0]["runs"][0]["items"]["impact"]["quotes"] = "베타 사용자 12명"
    r = agg(rubric, results)
    impact = next(i for i in r["items"] if i["id"] == "impact")
    assert impact["by_persona"]["developer"] == 8
    assert "베타 사용자 12명" in impact["quotes"]


def test_quotes_wrong_type_is_format_error(contest_dir):
    rubric = load_yaml(contest_dir / "rubric.yaml")
    results = base_results()
    results[0]["runs"][0]["items"]["impact"]["quotes"] = 3
    r = agg(rubric, results)
    assert any("quotes" in e for e in r["failed"]["developer"])


def test_aggregate_rejects_invalid_rubric(contest_dir, capsys):
    p = contest_dir / "rubric.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace("        cap: 4\n", ""), encoding="utf-8")
    run = new_run(contest_dir, "score")
    for res in base_results():
        write_json(run / f"{res['persona']}.json", res)
    with pytest.raises(SystemExit) as e:
        run_cli(lambda: aggregate.main([str(run)]))
    assert e.value.code == 2
    assert "cap" in capsys.readouterr().err


@pytest.mark.parametrize("mutate", [
    lambda g: g["questions"][0].pop("persona"),
    lambda g: g.__setitem__("questions", ["문자열 질문"]),
    lambda g: g.pop("created_at"),
    lambda g: g["suggestions"][0].pop("from_score"),
    lambda g: g.__setitem__("narrative", "총평 문자열"),
])
def test_grill_bad_shapes_are_input_errors(mutate):
    g = copy.deepcopy(GRILL)
    mutate(g)
    with pytest.raises(InputError):
        render(g)


def test_score_narrative_wrong_type(contest_dir):
    r = agg(load_yaml(contest_dir / "rubric.yaml"), base_results())
    r["narrative"] = {"overall": "x", "personas": ["리스트"]}
    with pytest.raises(InputError, match="narrative"):
        render(r)
