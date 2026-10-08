---
name: pro-judge-setup
description: 대회 등록. 공고·심사기준(URL·캡처·PDF·붙여넣은 글)을 받아 그 대회의 점수표(rubric.yaml)·심사위원 페르소나·취지를 docs/pro-judge/<대회>/에 만든다. 한 줄짜리 심사기준도 판정 질문·0/5/10 앵커·상한 규칙으로 펼친다. "이 대회 나갈 거야", "공고 등록해줘", "심사기준 이거야", "대회 세팅해줘", "점수표 만들어줘" 같은 요청에 사용한다.
---

# 대회 등록

`$SKILL`은 이 SKILL.md가 있는 폴더다. 스크립트는 `python3 $SKILL/shared/scripts/<이름>.py`로 부른다.
PyYAML이 없다는 오류가 나면 `python3 -m pip install pyyaml`을 안내하고 멈춘다.

시작 전에 읽는다:
- `$SKILL/shared/references/judge-stance.md`
- `$SKILL/shared/references/rubric-schema.md`
- `$SKILL/shared/references/persona-schema.md`
- `$SKILL/shared/references/common-caps.md`
- 본보기: `$SKILL/references/example/`

## 1. 입력 받기

URL·이미지·PDF·붙여넣은 글을 받는다. 여러 개를 받을 수 있다.
URL이 JS 렌더링 등으로 읽히지 않으면 읽은 것과 못 읽은 것을 나눠 말하고 캡처나 글을 요청한다.
짐작으로 빈칸을 채우지 않는다.

## 2. 폴더 만들기

```bash
python3 $SKILL/shared/scripts/contest_dirs.py init <레포 루트> "<대회 이름>"
```

마지막 줄이 대회 폴더 경로다. `알림:` 줄(이미 git이 추적 중인 파일)은 그대로 사용자에게 전하고, 그 파일은 건드리지 않는다.
`docs/pro-judge/.gitignore`(`*`) 때문에 심사 자료는 커밋되지 않는다고 알려 준다. 공유하려면 사용자가 그 파일을 지우면 된다.

## 3. contest.md 쓰기

공고가 회차·출처별로 나뉘어 있으면(예: 올해 공고엔 총점만, 작년 심사기준엔 항목 배점) 어느 문서의 어느 부분을 썼는지 '출처'에 모두 적고, 올해 공고와 다른 점을 '읽지 못한 것'에 적는다.

```markdown
# <대회 이름>

## 출처
- <URL 또는 파일명> (확인일 YYYY-MM-DD)

## 취지 원문
> 공고 문장 그대로. 없으면 "공고에 취지 문장 없음"

## 주제
## 일정
## 제출물
## 심사 단계
## 평가자 그룹
## 주최·심사 구성
## 읽지 못한 것
```

## 4. 대회 종류 고르기

`$SKILL/shared/references/contest-types/`에서 맞는 종류를 고른다 (복수 가능). 애매하면 사용자에게 묻는다.
고른 종류 문서의 '추천 상한 규칙'·'페르소나 후보'를 시작점으로 쓰고, 공고와 주최 기관에 맞게 고친다.

## 5. rubric.yaml 쓰기

`rubric-schema.md`의 고정 절차(질문 → 근거 종류 → 앵커 → 상한)를 모든 항목에 똑같이 적용한다.
공고에 있는 것은 `source: official`, 네가 정한 것은 `source: inferred` + `why`.

```bash
python3 $SKILL/shared/scripts/validate_rubric.py <대회 폴더> --skip-personas
```

페르소나는 다음 단계에서 쓰므로 여기서는 `--skip-personas`로 점수표만 검사한다. `OK`가 나올 때까지 고친다. 3번 고쳐도 실패하면 남은 오류 목록을 사용자에게 보여 주고 멈춘다.

## 6. 페르소나 쓰기

`persona-schema.md` 규칙으로 `personas/<name>.md`를 쓴다. 평가자 그룹마다 최소 한 명.
상상으로 만들지 않는다 — 주최 기관, 공고의 심사위원 구성, 평가자 그룹, 역대 수상작에서 끌어낸다.

```bash
python3 $SKILL/shared/scripts/validate_persona.py <대회 폴더>
```

이번에는 `--skip-personas` 없이 rubric 검사를 다시 돌린다(그룹마다 페르소나 파일이 있는지 확인). 3번 실패하면 멈추고 보여 준다.

## 7. 추정값 확인받기

inferred 값만 모아 표로 보여 주고 확인받는다. 공식 기준이 아예 없으면 맨 위에 "공식 기준 없음"이라고 적는다.

| 위치 | 정한 값 | 이유(why) |
| --- | --- | --- |

사용자가 고치라고 한 것을 반영하고 5·6의 검사를 다시 돌린다.

## 8. 보정 제안

역대 수상작·본선 자료가 있는지 묻는다. 있으면 `pro-judge-score`로 수상작과 낙선작을 **`--calibration`을 붙여** 채점해,
수상작이 더 높게 나오는지 확인하자고 제안한다. 순서가 맞으면 `rubric.yaml`의 `calibration.status`를 `done`으로 바꾼다.
순서가 뒤집히면 어느 항목 앵커가 원인인지 짚어 고치고, `validate_rubric.py`를 다시 통과시킨다.
수상작·낙선작 한 쌍의 순서는 우연으로도 절반은 맞는다 — 가능하면 여러 쌍으로 보고, 몇 쌍 중 몇 쌍이 맞았는지 사용자에게 말한다. 자료가 없으면 `none`으로 두고 보고서에 "보정 안 됨"이 찍힌다고 알린다.

## 끝

대회 폴더 경로, 항목 수, 페르소나 목록, 추정 비중을 말하고 다음 할 일 하나를 제안한다.
