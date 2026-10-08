---
name: pro-judge-ideas
description: 아이디어 비교. 여러 아이디어를 등록된 대회 기준으로 "명세대로 완벽히 구현했다면" 받을 상한 점수로 채점해 순위를 매기고, 점수를 막는 요인·바꾸면 오르는 점수·구현 비용을 낸다. 취지를 벗어난 아이디어는 순위를 내린다. "아이디어 뭐가 나아", "어떤 주제로 나갈까", "아이디어 비교해줘", "이 중에 뭐가 점수 잘 나와" 같은 요청에 사용한다.
---

# 아이디어 비교

`$SKILL`은 이 SKILL.md가 있는 폴더다.

읽는다: `$SKILL/shared/references/judge-stance.md`, `persona-prompt.md`, `persona-output.md`, `common-caps.md`.

## 1. 아이디어 받기

문서나 한 줄을 여러 개 받는다. 각각 `idea-1`, `idea-2` 식으로 id를 붙이고 제목을 정한다.
한 줄짜리는 그 한 줄만 채점 대상이다. 네가 살을 붙이지 않는다.

## 2. 비용 알리고 확인받기

"아이디어 M개 × 심사위원 N명 × 1회 = M·N회 호출합니다." 반복은 기본 1회. 사용자가 원하면 늘린다.

## 3. 런 폴더

```bash
python3 $SKILL/shared/scripts/contest_dirs.py new-run <대회 폴더> ideas
```

아이디어마다 `<런 폴더>/<idea id>/` 폴더를 만든다.

## 4. 아이디어 × 페르소나 독립 실행

`persona-prompt.md`에 **아이디어 모드 문단을 넣어** 서브에이전트로 보낸다. 아이디어끼리, 페르소나끼리 결과를 섞지 않는다.
아이디어 원문은 `<런 폴더>/<idea id>/target/idea.md`에 그대로 저장한다(인용 대조용). 결과는 `<런 폴더>/<idea id>/<persona>.json`. 그 밖의 규칙은 `pro-judge-score`의 4단계와 같다:
서브에이전트가 없으면 차례대로 돌리고 `independent: false`, 깨진 회차는 한 번 재시도.

## 5. 아이디어별 합산

```bash
python3 $SKILL/shared/scripts/aggregate.py <런 폴더>/<idea id> --target "<아이디어 제목>"
```

## 6. 구현 비용

`contest.md`의 일정 대비 `low`(일정의 1/3 이하) · `mid`(1/3~2/3) · `high`(그 이상)로 판정하고 근거를 한 줄로 쓴다.
`<런 폴더>/ideas.json`:

```json
[{"id": "idea-1", "title": "제목", "cost_level": "mid", "cost_note": "지도 API 연동 1주 + 데이터 정제 3일"}]
```

## 7. 순위와 보고서

```bash
python3 $SKILL/shared/scripts/rank_ideas.py <런 폴더>
```

`<런 폴더>/result.json`의 `narrative.overall`에 비교 총평을 쓰고:

```bash
python3 $SKILL/shared/scripts/render_report.py <런 폴더>
python3 $SKILL/shared/scripts/render_dashboard.py <대회 폴더>
```

## 끝

순위표, 1위의 막는 요인, "이걸 바꾸면 몇 점" 제안 하나, 보고서 경로. 다음 할 일: 1위 아이디어로 자료를 만든 뒤 채점.
