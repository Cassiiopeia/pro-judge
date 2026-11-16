---
name: pj-score
description: pro-judge 채점. 발표자료·기획서·레포·배포 URL을 등록된 대회의 심사위원 페르소나별로 독립 채점하고 합산해 총점·고칠 것 순위·편차 경보를 md·html 보고서로 낸다. 재채점이면 지난 회차와 비교한다. 아이디어 여러 개를 "명세대로 완벽히 구현했다면" 받을 상한 점수로 비교해 순위도 매긴다. "몇 점이야", "채점해줘", "심사해줘", "다시 봐줘", "고쳤어 다시 봐", "아이디어 뭐가 나아", "어떤 주제로 나갈까", "아이디어 비교해줘" 같은 요청에 사용한다.
---

# 채점

`$SKILL`은 이 SKILL.md가 있는 폴더. 스크립트는 `python3 $SKILL/shared/scripts/<이름>.py`.
PyYAML이 없다는 오류가 나면 `python3 -m pip install pyyaml`을 안내하고 멈춘다.
시작 전에 `$SKILL/shared/references/judge-stance.md`를 읽는다 — 너는 팀의 조력자가 아니라 심사석에 앉은 사람이다.

자료 채점(발표자료·기획서·레포·배포 URL)과 아이디어 비교("명세대로 완벽히 구현했다면" 받을 상한 점수).
아이디어 여러 개를 비교하려는 요청이면 아래 [아이디어 비교](#아이디어-비교) 절을 따른다.

읽는다: `$SKILL/shared/references/persona-run.md`, `persona-prompt.md`, `persona-output.md`, `common-caps.md`.

`docs/pro-judge/*/rubric.yaml`이 없으면 "먼저 대회를 등록해야 채점 기준이 생깁니다"라고 말하고 `pj-prepare`로 보낸다. 둘 이상이고 어느 대회인지 없으면 목록을 보여 주고 묻는다.

# 자료 채점

## 1. 대상 받기

파일·레포 경로·배포 URL을 받는다. 수집 방법은 3단계의 근거 수집을 따른다.

## 2. 비용 알리고 확인받기

"심사위원 N명 × 반복 3회 = 3N회 호출합니다. 반복을 줄일까요?" — 답을 받고 시작한다.

## 3. 런 폴더와 근거 장부

```bash
python3 $SKILL/shared/scripts/contest_dirs.py new-run <대회 폴더> score
```

이어서 `$SKILL/shared/references/collect-evidence.md`를 **대상 모드**로 따른다(장부: `<런 폴더>/evidence.yaml`).
채점 대상 원문이 `<런 폴더>/target/`에 텍스트로 저장된다. 원문에 없는 인용은 합산이 지우고, 폴더가 없으면 보고서에 "인용 원문 대조 안 함"이 찍힌다.
페르소나 프롬프트의 `<target>`에 `target/` 파일과 `target_images/` 폴더 경로를 준다.

## 4. 페르소나별 독립 실행

`persona-run.md`를 `<결과 폴더>` = 런 폴더로 따른다.

## 5. 합산

```bash
python3 $SKILL/shared/scripts/aggregate.py <런 폴더> --target "<대상 한 줄 설명>"
```

보정용(역대 수상작·낙선작) 채점이면 `--calibration`을 붙인다. 그 회차는 지난 회차 비교와 대시보드 추이에서 빠진다.

`경고:`·`제외:` 줄은 보고할 때 그대로 전한다. 숫자는 손으로 고치지 않는다.

## 6. 총평 쓰기

`<런 폴더>/result.json`에서 `narrative.overall`(3~5문장)과 `narrative.personas.<name>`만 채운다.
총평은 점수와 가장 큰 구멍부터 쓴다. 칭찬으로 시작하지 않는다.

## 7. 보고서

```bash
python3 $SKILL/shared/scripts/render_report.py <런 폴더>
python3 $SKILL/shared/scripts/render_dashboard.py <대회 폴더>
```

## 8. 답하기

총점(이 점수는 진단 지표이지 실제 점수 예측이 아님을 함께), 지난 회차 대비 변화, 고칠 것 Top 3(항목·현재→목표·오를 점수·다음 앵커 문장),
회차마다 흔들린 항목, 편차 경보, `report.html` 경로. 다음 할 일 하나: "가장 약한 <항목>으로 질의응답 연습할까요?"

## 항의를 받으면

새 근거(숫자·고유명사·시연·실증)가 있으면 그 근거를 자료에 넣고 재채점하자고 한다.
새 근거가 없으면 점수를 바꾸지 않고, 무엇이 있으면 몇 점이 되는지만 말한다.

# 아이디어 비교

취지를 벗어난 아이디어는 순위를 내린다. 막는 요인·바꾸면 오르는 점수·구현 비용을 함께 낸다.

## 1. 아이디어 받기

문서나 한 줄을 여러 개 받는다. 각각 `idea-1`, `idea-2` 식으로 id를 붙이고 제목을 정한다.
한 줄짜리는 그 한 줄만 채점 대상이다. 네가 살을 붙이지 않는다.

## 2. 비용 알리고 확인받기

"아이디어 M개 × 심사위원 N명 × 1회 = M·N회 호출합니다." 반복은 기본 1회. 사용자가 원하면 늘린다.

## 3. 런 폴더

```bash
python3 $SKILL/shared/scripts/contest_dirs.py new-run <대회 폴더> ideas
```

아이디어마다 `<런 폴더>/<idea id>/` 폴더를 만들고, 원문을 `<런 폴더>/<idea id>/target/idea.md`에 그대로 저장한다(인용 대조용).

## 4. 아이디어 × 페르소나 독립 실행

`persona-prompt.md`에 **아이디어 모드 문단을 넣어** `persona-run.md`를 `<결과 폴더>` = `<런 폴더>/<idea id>`로 따른다.

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

## 아이디어 비교 끝

순위표, 1위의 막는 요인, "이걸 바꾸면 몇 점" 제안 하나, 보고서 경로. 다음 할 일: 1위 아이디어로 자료를 만든 뒤 채점.
