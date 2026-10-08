# 페르소나 작성법

검사: `python3 $SKILL/shared/scripts/validate_persona.py <대회 폴더>`.
파일: `personas/<name>.md`, 파일명 = `name`.

```markdown
---
name: developer
group: judges            # rubric.yaml evaluator_groups의 id
strictness: strict       # lenient | normal | strict
---

# 제목

## 누구인가
## 심사위원 근거
## 무겁게 보는 항목
## 인정하는 근거
## 감점 트리거
## 단골 질문
## 말투
```

## 규칙
- 상상으로 만들지 않는다. 주최 기관, 공고의 심사위원 구성, 평가자 그룹, 역대 수상작에서 끌어낸다.
- `## 심사위원 근거`에는 그 근거(공고 문장, 주최 기관 성격)를 쓴다. 근거가 추정이면 "추정:"으로 시작한다.
- 평가자 그룹마다 최소 한 명. 심사위원이 3명 이상 공개되어 있으면 전문 분야별로 나눈다. 보통 3~5명이 적당하다.
- `## 무겁게 보는 항목`에는 rubric 항목 id를 쓴다.
- `## 단골 질문`은 그 사람이 실제로 할 법한 문장으로 3개 이상.
- 실존 인물 이름을 쓰지 않는다. 역할과 경력으로만 쓴다.
