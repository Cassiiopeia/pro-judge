---
name: pro-judge-grill
description: 질의응답 연습. 최근 채점 결과의 약한 항목·상한에 걸린 항목·편차 큰 항목을 골라 심사위원 페르소나 말투로 날카로운 질문을 던지고, 답을 판정하고 꼬리 질문을 이어 간다. 예상 질문지 20개와 모범 답변 뼈대도 만든다. "질의응답 연습하자", "예상 질문 뽑아줘", "심사위원처럼 물어봐", "Q&A 대비" 같은 요청에 사용한다.
---

# 질의응답 연습

`$SKILL`은 이 SKILL.md가 있는 폴더다.

읽는다: `$SKILL/shared/references/judge-stance.md`, `grill-output.md`, 대회의 `contest.md`·`rubric.yaml`·`personas/*.md`.

## 0. 최근 채점 찾기

`<대회 폴더>/runs/` 중 가장 최근 `_score` 런의 `result.json`. 없으면 "질문은 채점 결과의 약점에서 나옵니다. 채점부터 할까요?"라고 묻고 멈춘다.

## 1. 질문 재료 고르기

- 득점률(`earned / points_total`)이 낮은 항목 3개
- `caps`가 있는 항목 (해제 조건이 곧 질문)
- `deviation_alerts`, `consensus_gaps` 항목
- 대회 취지 질문: `rubric.yaml`의 `contest_types`마다 `$SKILL/shared/references/contest-types/<종류>.md`의 '취지 질문'에서 최소 1개를 고정으로 넣는다.

## 2. 모드 묻기

연습 모드(한 번에 하나씩 답하고 판정) 또는 질문지 모드(20개 한 번에).

## 3. 연습 모드

- 질문마다 페르소나를 정하고 그 페르소나 문서의 '말투'·'단골 질문'·엄격도로 묻는다. 누가 묻는지 밝힌다.
- 한 번에 질문 하나. 답을 받으면 판정한다.
  - `up`: 새 근거(숫자·고유명사·시연·실증)를 댔다
  - `same`: 자료에 있던 주장을 반복했다
  - `down`: 회피, 자료와 모순, 근거 없는 확언
- 판정과 이유를 한 줄로 말하고, 약하면 꼬리 질문을 최대 2번 이어 간다.
- 사용자가 그만하자고 하거나 질문 10개가 차면 끝낸다.

## 4. 질문지 모드

예상 질문 20개와 모범 답변 뼈대. 뼈대는 근거가 들어갈 자리를 `[숫자]`, `[기관 이름]`처럼 비워 둔다.
없는 근거를 지어내 채우지 않는다.

## 5. 자료 수정 제안

`up` 판정을 받은 답의 새 근거를 "자료에 넣으면 어느 항목이 앵커 기준 몇 점에서 몇 점이 되는지"로 바꾼다.

## 6. 기록과 보고서

```bash
python3 $SKILL/shared/scripts/contest_dirs.py new-run <대회 폴더> grill
```

`grill-output.md` 형식으로 `<런 폴더>/result.json`을 쓰고:

```bash
python3 $SKILL/shared/scripts/render_report.py <런 폴더>
python3 $SKILL/shared/scripts/render_dashboard.py <대회 폴더>
```

## 끝

가장 약했던 답 3개와 자료 수정 제안을 말하고, "수정 반영 뒤 재채점할까요?"를 제안한다.
