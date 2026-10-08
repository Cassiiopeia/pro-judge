# 질의응답 결과 형식

`<런 폴더>/result.json`으로 저장하고 `render_report.py`로 보고서를 만든다.

```json
{
  "kind": "grill",
  "contest": "대회 이름",
  "created_at": "2026-10-08T15:00",
  "mode": "practice",
  "questions": [
    {
      "persona": "developer",
      "item": "feasibility",
      "question": "지금 이 주소에서 핵심 기능을 눌러 볼 수 있나요?",
      "answer": "사용자 답 원문",
      "verdict": "up",
      "reason": "판정 이유 한 줄",
      "follow_ups": [{"question": "...", "answer": "...", "verdict": "down", "reason": "..."}],
      "model_answer": null
    }
  ],
  "suggestions": [{"evidence": "베타 사용자 12명 설문", "item": "impact", "from_score": 5, "to_score": 7}],
  "narrative": {"overall": "총평"}
}
```

- `mode`: `practice`(연습) 또는 `sheet`(질문지).
- `verdict`: `up`(새 근거로 점수가 오름) · `same`(주장 반복) · `down`(회피·자료와 모순·근거 없는 확언) · 질문지 모드는 `null`.
- 질문지 모드는 `answer`가 null이고 `model_answer`에 모범 답변 뼈대를 쓴다. 숫자가 들어갈 자리는 `[숫자]`처럼 비워 둔다.
- `suggestions`: 좋은 답에서 나온 새 근거를 자료에 넣으면 어느 항목이 몇 점에서 몇 점이 되는지 (앵커 기준).
