# 페르소나 채점 결과 형식

서브에이전트 한 번 = 페르소나 한 명 × 1회. 서브에이전트는 아래 **한 회차 JSON**만 낸다.

```json
{
  "gate_score": 7,
  "items": {
    "<item id>": {"score": 5, "quotes": ["원문 그대로"], "cap_applied": null, "unlock_hint": null}
  },
  "summary": "이 심사위원의 총평 2~3문장"
}
```

- `score`: 0~10 정수. `quotes`: 대상 원문을 그대로 복사한 문장. 7점 이상이면 1개 이상 필수.
- `cap_applied`: 걸린 상한 규칙 id (rubric 항목 caps의 rule 또는 공통 규칙 id), 없으면 null.
- `unlock_hint`: 상한을 넘으려면 원문에 무엇이 있어야 하는지, 없으면 null.
- 자기 평가자 그룹에 배점이 있는 항목 id는 모두 있어야 한다. 빠지면 그 페르소나는 합산에서 빠진다.
  배점이 없는 항목은 넣지 않는다 — 넣어도 합산에서 쓰지 않는다.

오케스트레이터(skill을 돌리는 에이전트)는 회차 JSON을 모아 `<런 폴더>/<persona>.json`으로 저장한다.

```json
{
  "persona": "developer",
  "model": "sonnet",
  "independent": true,
  "runs": [ {한 회차}, {한 회차}, {한 회차} ]
}
```

- `model`: 그 페르소나를 돌린 모델 이름. 모르면 null.
- `independent`: 서브에이전트로 따로 돌렸으면 true, 한 맥락에서 차례대로 돌렸으면 false.
- 형식이 깨진 회차는 그 회차만 한 번 다시 돌린다. 또 깨지면 그 회차를 뺀다.
