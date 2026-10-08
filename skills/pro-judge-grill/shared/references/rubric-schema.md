# rubric.yaml 작성법

검사: `python3 $SKILL/shared/scripts/validate_rubric.py <대회 폴더>` — `OK`가 나올 때까지 고친다.
본보기: `skills/pro-judge-setup/references/example/rubric.yaml`.

## 필드

| 필드 | 뜻 | 규칙 |
| --- | --- | --- |
| `contest` | 대회 이름 | 비우지 않는다 |
| `purpose.official` | 공고의 취지 문장 원문 | 없으면 `null` |
| `purpose.contest_types` | 대회 종류 | open-source, disability, social-impact, startup, public-data, ai-tech 중 1개 이상 |
| `gate` | 취지·주제 게이트 | `source: official`이면 `bands`(min 0~10, multiplier 0~1, min 0 구간 필수). 공고에 근거가 없으면 `inferred`/`none` — 배율은 걸지 않고 경보만 낸다 |
| `calibration.status` | 보정 여부 | `done` 또는 `none` |
| `evaluator_groups[]` | 평가자 그룹 | `id`, `weight`(합 100), `source`, `personas`(1명 이상) |
| `items[]` | 심사 항목 | 아래 |
| `common_caps` | 공통 상한 규칙 id | `common-caps.md` 참고 |

`items[]`: `id`, `name`, `points`(그룹 id → 배점, 그룹별 합 = 그룹 weight), `source`, `official_text`(official이면 필수),
`questions`(2~3개), `evidence_types`(numbers, proper-nouns, demo, field-test, quote, observation),
`anchors`(0, 5, 10), `caps`(rule, cap 0~9, unlock, source).

모든 `source: inferred`에는 `why` 한 줄을 단다. 왜 그렇게 정했는지 사용자가 확인할 수 있어야 한다.

## 한 줄 기준을 펼치는 고정 절차

모든 항목에 같은 순서를 적용한다. 같은 입력이면 같은 구조가 나와야 한다.

1. 공고 문장을 심사위원이 실제로 묻는 질문 2~3개로 바꾼다.
   - 예: "실제로 실현 가능한 내용을 제시하는가" → "지금 작동하는 것을 보여 주는가", "누가 언제 운영하는가"
2. 질문마다 "그렇다"로 인정하는 근거 종류를 정한다 (`evidence_types`).
3. 0/5/10 앵커를 관찰 가능한 말로 쓴다.
   - 금지: 잘했다, 충분하다, 적절하다, 우수하다, 훌륭하다 (검사기가 거부한다)
   - 좋음: "배포 주소에서 핵심 기능 3개가 작동하고 운영 기관 이름이 있다"
4. 상한 규칙과 해제 조건을 붙인다. 해제 조건은 "원문에 무엇이 있어야 넘는다"로 쓴다.

## 배점 환산

공고가 "심사위원 70% + 시민 30%"이고 항목이 "적용 가능성 20점"이면 그룹 weight 비율로 나눈다:
`points: {judges: 14, citizens: 6}`. 공고가 그룹별 배점을 따로 주면 그 숫자를 그대로 쓴다.
