import copy


def persona_result(name, scores, *, gate=8, quotes=True, model=None, independent=True,
                   runs=1, caps=None):
    """페르소나 원자료 한 건. scores: {item_id: 점수}, caps: {item_id: 상한 규칙}."""
    caps = caps or {}
    items = {
        iid: {
            "score": s,
            "quotes": [f"{iid} 근거 원문"] if quotes else [],
            "cap_applied": caps.get(iid),
            "unlock_hint": f"{iid} 해제 조건" if iid in caps else None,
        }
        for iid, s in scores.items()
    }
    return {
        "persona": name,
        "model": model,
        "independent": independent,
        "runs": [{"gate_score": gate, "items": copy.deepcopy(items), "summary": f"{name} 총평"}
                 for _ in range(runs)],
    }


BASE = {
    "developer": {"feasibility": 6, "impact": 8},
    "domain-expert": {"feasibility": 4, "impact": 6},
    "citizen": {"feasibility": 8, "impact": 6},
}


def base_results(**kw):
    return [persona_result(n, s, **kw) for n, s in BASE.items()]
