import pytest

from _common import InputError, load_json, load_yaml, write_json
from aggregate import aggregate
import rank_ideas
from rank_ideas import rank_ideas as rank
from factories import base_results


@pytest.fixture
def results(contest_dir):
    rubric = load_yaml(contest_dir / "rubric.yaml")
    return {
        "idea-1": aggregate(rubric, base_results()),            # 62.0
        "idea-2": aggregate(rubric, base_results(gate=4)),      # 37.2, 취지 경보
        "idea-3": aggregate(rubric, base_results(gate=5)),      # 52.7
    }


META = [
    {"id": "idea-1", "title": "A", "cost_level": "high", "cost_note": "3주"},
    {"id": "idea-2", "title": "B", "cost_level": "low", "cost_note": "3일"},
    {"id": "idea-3", "title": "C", "cost_level": "mid", "cost_note": "1주"},
]


def test_rank_order(results):
    out = rank(META, results)
    assert [i["id"] for i in out["ideas"]] == ["idea-1", "idea-3", "idea-2"]
    assert [i["rank"] for i in out["ideas"]] == [1, 2, 3]
    assert out["ideas"][0]["cost"] == {"level": "high", "note": "3주"}
    assert out["ideas"][0]["blockers"][0].startswith("실현 가능성")


def test_gate_warning_sinks(results):
    results["idea-2"]["total"] = 99.0
    assert rank(META, results)["ideas"][-1]["id"] == "idea-2"


def test_bad_meta(results):
    with pytest.raises(InputError, match="cost_level"):
        rank([{**META[0], "cost_level": "huge"}], results)
    with pytest.raises(InputError, match="idea-9"):
        rank([{"id": "idea-9", "title": "X", "cost_level": "low"}], results)


def test_cli(tmp_path, results):
    write_json(tmp_path / "ideas.json", META)
    for iid, r in results.items():
        (tmp_path / iid).mkdir()
        write_json(tmp_path / iid / "result.json", r)
    assert rank_ideas.main([str(tmp_path)]) == 0
    assert load_json(tmp_path / "result.json")["kind"] == "ideas"
