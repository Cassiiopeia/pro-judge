# pro-judge — 대회 심사위원 하네스

- 작성일: 2026-10-08
- 상태: 스펙 검토 대기
- 원형: Hack-the-Beat(2026 I/O Extended, 최종 1위)에서 쓴 심사 역설계 방식
  (`~/Desktop/Programming/project/Hack-the-Beat/docs/judging-criteria.md`, `docs/personas/`, `docs/retrospective/ko.md`)

## 1. 목적

대회에 나가는 팀이 **제출 전에 실제 심사를 미리 받아 보는** 도구다.
어떤 레포에서든 대회 심사기준을 주면 에이전트가 그 대회의 심사위원이 되어
아이디어·발표자료·레포·배포 서비스를 **객관적으로** 채점하고, 날카로운 질문을 던지고,
점수를 올리는 순서를 보고서로 낸다. 목표는 우승이다.

### 성공 기준

1. 한 줄짜리 심사기준(예: "실제로 실현 가능한 내용을 제시하는가")도 Hack-the-Beat 공식 루브릭 수준
   (판정 질문·근거 종류·0/5/10 앵커·상한 규칙)으로 펼친다. 같은 입력이면 매번 같은 구조가 나온다.
2. 대회 **취지**(오픈소스 대회면 오픈소스 정신, 장애인 해커톤이면 그 취지)를 모든 채점에 반영한다.
3. 페르소나별로 독립 채점하고, 근거 인용 없는 고득점을 막는다.
4. 결과를 md와 html 보고서로 낸다.
5. `npx skills add <owner>/pro-judge`로 Claude Code·Codex·Cursor 등 여러 에이전트에 설치된다.

### 심사위원의 자세 (모든 skill 공통)

에이전트는 **팀의 조력자가 아니라 그 대회 심사석에 앉은 사람**으로 판단한다.

- 칭찬으로 시작하지 않는다. 점수와 근거부터 말한다.
- 자료에 없는 것은 없는 것이다. "아마 이런 뜻일 것"이라고 선의로 채워 주지 않는다.
- 주장은 근거가 있어야 점수가 된다. 근거는 원문에서 인용할 수 있어야 한다.
- 모든 팀에 같은 점수표를 같은 엄격도로 적용한다. 사용자가 만든 프로젝트라고 관대해지지 않는다.
- 사용자가 점수에 항의해도 새 근거가 없으면 점수를 바꾸지 않는다.

## 2. 형태와 배포

- **Agent Skills 표준**(`skills/<이름>/SKILL.md`) 레포 하나. caveman과 같은 구조다.
- 다른 에이전트: `npx skills add <owner>/pro-judge` (Vercel 오픈소스 skills CLI).
- Claude Code: `.claude-plugin/plugin.json` + `marketplace.json`으로 플러그인 설치. SessionStart 훅 사용.
- Claude Code 전용 기능(서브에이전트 병렬 실행, 모델 지정)은 **있으면 쓰고 없으면 차례대로** 돈다.
- 결정론이 필요한 일(검사·합산·보고서 생성)은 Python 스크립트(표준 라이브러리 + PyYAML)가 한다.
  판단·문장은 에이전트가 한다.

## 3. skill 구성

| skill | 하는 일 |
| --- | --- |
| `using-pro-judge` | 길잡이. 사용자 요청을 분류해 아래 skill을 부르고 다음 할 일을 제안한다 |
| `pro-judge-setup` | 대회 등록. 공고·심사기준 → 점수표 + 페르소나 + 취지 |
| `pro-judge-ideas` | 아이디어 비교. "완벽히 구현했다면"의 상한 점수로 순위 |
| `pro-judge-score` | 자료 채점. 발표자료·기획서·레포·배포 URL을 페르소나별 채점 |
| `pro-judge-grill` | 질의응답 연습. 약한 곳을 찌르는 질문 → 답변 판정 → 자료 수정 제안 |

재채점("고쳤어, 다시 봐줘")은 `pro-judge-score`를 다시 돌리고 지난 회차와 비교한다.

### 3.1 `using-pro-judge` 길잡이

| 사용자가 이렇게 말하면 | 부르는 skill |
| --- | --- |
| "이 대회 나갈 거야" + 공고 URL·캡처·PDF·붙여넣은 글 | `pro-judge-setup` |
| "아이디어 중 뭐가 점수 잘 나와?" | `pro-judge-ideas` |
| "이 자료 몇 점이야?" / "다시 봐줘" | `pro-judge-score` |
| "질의응답 연습하자" / "예상 질문 뽑아줘" | `pro-judge-grill` |

- `docs/pro-judge/`에 대회가 없는데 채점·질문·비교를 요청하면 먼저 등록으로 보낸다.
- 대회가 둘 이상이면 어느 대회인지 묻는다.
- 끝날 때 다음 할 일을 하나 제안한다 (예: 채점 뒤 "가장 약한 B2로 질의응답 연습할까요?").
- Claude Code SessionStart 훅은 **레포에 `docs/pro-judge/`가 있을 때만** 길잡이를 띄운다.

## 4. 대회 폴더 (심사받는 레포 안)

```
docs/pro-judge/
├── .gitignore              # 내용: "*" — 폴더 전체를 git에서 뺀다 (자기 자신 포함)
└── <대회이름>/
    ├── contest.md          # 공고 출처, 취지 원문, 주제, 일정, 제출물, 심사 단계
    ├── rubric.yaml         # 점수표
    ├── personas/<이름>.md  # 심사위원 한 명당 하나
    ├── runs/<YYYYMMDD-HHMM>_<score|grill|ideas>/
    │   ├── <페르소나>.json # 페르소나별 원자료
    │   ├── result.json     # 합산 결과
    │   ├── report.md
    │   └── report.html
    ├── history.md          # 회차별 총점 추이
    └── index.html          # 대회 대시보드
```

- `.gitignore`는 `pro-judge-setup`이 `docs/pro-judge/`를 처음 만들 때 함께 만든다.
  심사 전략·점수가 공개 레포에 올라가지 않게 하기 위해서다. 공유하려면 사용자가 이 파일을 지운다.
- 이미 추적 중인 파일이 그 아래 있으면 알리고 건드리지 않는다.

## 5. 점수표 하네스 (객관성의 핵심)

### 5.1 `rubric.yaml` 스키마

```yaml
contest: 2026-장애인해커톤
purpose:                     # 대회 취지
  official: "장애인의 삶의 질 향상을 위한 ..."   # 공고 원문 (없으면 null)
  contest_types: [disability, social-impact]    # 프로필 (5.3)
gate:                        # 취지·주제 게이트 — 공고에 근거가 있을 때만 multiplier
  source: official | inferred | none
  bands: [{min: 8, multiplier: 1.0}, {min: 5, multiplier: 0.85}, ...]
evaluator_groups:
  - id: judges
    weight: 70
    source: official
    personas: [welfare-expert, developer, policy]
  - id: citizens
    weight: 30
    source: official
    personas: [citizen-family]
items:
  - id: feasibility
    name: 적용 가능성
    points: {judges: 14, citizens: 6}
    source: official             # 항목 자체는 공고에 있다
    official_text: "실제로 실현 가능한 내용을 제시하고 있는가 / 장애 현장에서 적용 가능성이 높은가"
    questions:                   # 5.2 절차로 펼친 판정 질문 (2~3개)
      - text: "지금 작동하는 것을 보여 주는가"
        source: inferred
    evidence_types: [demo, numbers, field-test]
    anchors:
      0: "..."
      5: "..."
      10: "..."
    caps:
      - rule: no-field-test
        cap: 6
        unlock: "현장 실증 결과(누가·몇 명·언제)가 원문에 있어야 넘는다"
        source: inferred
common_caps: [intent-not-evidence, no-specifics, claim-not-verified, claim-failed]
```

- 모든 칸에 `source: official | inferred`를 단다. inferred에는 근거 한 줄(`why`)을 단다.
- 점수는 항목마다 0~10 정수로 매기고, 합산 때 배점으로 환산한다.

### 5.2 한 줄 기준을 펼치는 고정 절차

모든 항목에 같은 순서를 적용한다.

1. 공고 문장을 심사위원이 실제로 묻는 질문 2~3개로 바꾼다.
2. 질문마다 "그렇다"로 인정하는 근거 종류를 정한다 (숫자·고유명사·시연·실증·인용 가능한 관찰).
3. 0/5/10 앵커를 관찰 가능한 말로 쓴다. "잘했다"·"충분하다" 같은 말은 금지다.
4. 상한 규칙과 해제 조건을 붙인다.

### 5.3 대회 종류 프로필 (`references/contest-types/*.md`)

공고에 없어도 심사위원이 당연히 기대하는 것과 보이지 않는 감점을 담는다.
등록 때 시작점으로 쓰고, 공고·주최 기관에 맞춰 고친다.

| 종류 | 기대 | 보이지 않는 감점 |
| --- | --- | --- |
| open-source | OSI 라이선스, 기여 경로(CONTRIBUTING·이슈 템플릿), 문서, 재사용성, 공개 커밋 이력 | 라이선스 없음, 제출 직전 일괄 커밋, 외부 기여 불가 구조 |
| disability / social-impact | 당사자 참여·실증, 존중 용어, 접근성, 현장 적용 경로 | 의료·치료 표현, 대상화 서사, 실증 없음 |
| startup | 타깃, 첫 고객 획득, 수익 모델, 단위 경제성 | TAM 인용만, "광고·구독" 일반론 |
| public-data | 데이터 출처, 정책 연계, 기관 적용 경로 | 출처 불명, 실현 주체 없음 |
| ai-tech | 실제 작동, 기술 난이도, 배포 | 데모 영상만, localhost |

### 5.4 공통 상한 규칙 (`references/common-caps.md`)

Hack-the-Beat 공식 규칙을 일반화했다. 모든 대회에 기본 적용한다.

| id | 규칙 | 상한 |
| --- | --- | --- |
| intent-not-evidence | "~할 계획/예정/하면 된다"는 의도다 | 5 |
| no-specifics | 숫자·고유명사·관찰이 없는 주장 | 5 |
| claim-not-verified | 주장한 기능이 시연·배포에서 확인 안 됨 | 6 |
| claim-failed | 주장한 기능이 확인 중 실패 | 4 |
| quote-for-seven | 7점 이상은 인용 가능한 근거가 있을 때만 | — |
| length-neutral | 분량은 점수에 영향 없음 | — |

### 5.5 페르소나 (`personas/<이름>.md`)

필수 칸: 누구인가(경력·소속 유형), **왜 이 사람이 심사위원이라고 보는가**(주최·심사 구성·평가자 그룹 근거),
무겁게 보는 항목, 인정하는 근거, 감점 트리거, 단골 질문, 엄격도, 말투.

- 상상으로 만들지 않는다. 주최 기관, 공고의 심사위원 구성, 평가자 그룹, 역대 수상작에서 끌어낸다.
- 평가자 그룹(예: 시민평가단)마다 최소 한 명.
- 형식 본보기: Hack-the-Beat `docs/personas/*.md`를 `skills/pro-judge-setup/references/example-hack-the-beat/`에 복사해 둔다.

### 5.6 검사기

- `scripts/validate_rubric.py` — 스키마 위반, 빈 앵커, 금지 단어 앵커, `source` 누락, inferred의 `why` 누락,
  배점 합 불일치, 페르소나가 없는 평가자 그룹을 거부한다.
- `scripts/validate_persona.py` — 필수 칸 누락을 거부한다.
- 에이전트는 통과할 때까지 고친다. 3회 실패하면 빈칸 목록을 사용자에게 보여 준다.

### 5.7 보정

역대 수상작·본선 자료가 있으면 등록 직후 그것을 먼저 채점한다.
수상작이 낙선작보다 높게 나와야 점수표가 그 대회를 읽은 것이다. 순서가 뒤집히면 앵커를 고친다.
보정 자료가 없으면 보고서에 "보정 안 됨"을 적는다.

## 6. `pro-judge-setup` 흐름

1. 입력을 받는다 (URL·이미지·PDF·붙여넣은 글, 여러 개 가능).
2. URL이 JS 렌더링 등으로 읽히지 않으면 읽은 것/못 읽은 것을 말하고 캡처·글을 요청한다.
3. `contest.md` 작성 — 취지 원문, 주제, 일정, 제출물, 심사 단계, 평가자 그룹.
4. 대회 종류를 고른다 (복수 가능). 애매하면 묻는다.
5. 5.2 절차로 `rubric.yaml` 작성 → `validate_rubric.py` 통과.
6. 5.5 규칙으로 페르소나 작성 → `validate_persona.py` 통과.
7. **inferred 값만 모아 사용자에게 보여 주고 확인받는다.** 공식 기준이 아예 없으면 맨 위에 "공식 기준 없음"이라고 적는다.
8. 보정 자료가 있으면 5.7을 제안한다.

## 7. `pro-judge-score` 흐름

1. 채점 대상을 받는다 — 파일(PPT·PDF·md), 레포 경로, 배포 URL.
2. 시작 전에 호출 수(페르소나 수 × 반복 횟수, 기본 3)를 알린다. 사용자는 반복을 줄일 수 있다.
3. **페르소나마다 독립 실행** — 서브에이전트 하나에 한 명. 서로의 결과를 보지 않는다.
   서브에이전트가 없으면 차례대로 돌리고 "독립 실행 아님"을 표시한다.
4. 가능하면 페르소나마다 다른 모델로 돌린다. 모델이 달라도 같은 지적이 나오면 "진짜 구멍"으로 표시한다.
5. 각 실행은 항목별 `{score, quotes[], cap_applied, unlock_hint}` json을 낸다. 형식이 깨지면 그 실행만 다시 돌린다.
6. `scripts/aggregate.py` — 항목별 중앙값 → 그룹 안 페르소나 평균 → 배점 환산·그룹 가중 → 게이트 배율.
   inferred 규칙 비중이 크면 총점을 범위로 낸다.
7. 편차 경보 — 페르소나 사이 3점 이상 벌어진 항목.
8. 고칠 것 순위 — (해제 시 오르는 점수 × 배점)이 큰 순서.
9. 지난 회차가 있으면 항목별 변화를 붙인다. 보고서 생성(10절).

확인 못 한 대상(배포 URL이 죽음 등)은 0점이 아니라 `claim-not-verified` 상한을 적용하고 "확인 불가"로 적는다.

## 8. `pro-judge-grill` 흐름

1. 최근 채점 결과에서 낮은 항목, 상한에 걸린 항목, 편차 큰 항목을 고른다. 채점 결과가 없으면 채점부터 제안한다.
2. 대회 취지 질문을 고정으로 포함한다 (예: "이게 왜 오픈소스여야 하나요?", "당사자가 직접 써 봤나요?").
3. 페르소나마다 말투·집요함을 다르게 한다.
4. 두 모드.
   - 연습 모드: 한 번에 하나씩. 답을 판정(올림·그대로·깎음 + 이유)하고 꼬리 질문을 최대 2번 이어 간다.
   - 질문지 모드: 예상 질문 20개 + 모범 답변 뼈대.
5. 좋은 답에서 나온 새 근거를 "자료에 넣으면 어느 항목이 몇 점이 되는지"로 바꿔 제안한다.

## 9. `pro-judge-ideas` 흐름

1. 아이디어 여러 개를 받는다 (문서 또는 한 줄).
2. 취지 적합성을 먼저 판정한다. 벗어난 아이디어는 순위를 내린다.
3. "명세대로 완벽히 구현했다면" 전제로 상한 점수를 잰다. 아이디어마다 독립 실행한다.
4. 아이디어별 점수를 막는 요인, "이걸 바꾸면 몇 점" 제안, 구현 비용(대회 일정 대비)을 낸다.

## 10. 보고서

- `scripts/render_report.py`가 `result.json`으로 `report.md`와 `report.html`을 만든다.
  에이전트는 총평·설명 문장만 쓰고, 숫자·표·차트는 스크립트가 찍는다.
- html은 파일 하나 — CSS·SVG 차트 내장, 외부 요청 없음. 메일·메신저로 그대로 보낼 수 있다.
- json에서 언제든 다시 만들 수 있다.

| 보고서 | 내용 |
| --- | --- |
| 채점 | 총점(범위)·지난 회차 대비·취지 경보 → 고칠 것 Top 5 → 편차 경보 → 항목별 표(페르소나 점수·중앙값·인용·상한 사유) → 페르소나별 총평 → 부록(inferred 규칙, 실행 정보) |
| 질의응답 | 질문별 답·판정·꼬리 질문, 약한 답변 순위, 자료 수정 제안, 예상 질문지 |
| 아이디어 비교 | 순위표, 상한 점수, 막는 요인, 구현 비용 |
| 대시보드 `index.html` | 회차별 총점 추이, 항목별 변화, 최근 보고서 링크 |

## 11. 오류 처리

| 상황 | 동작 |
| --- | --- |
| 공고 URL을 읽지 못함 | 읽은 것/못 읽은 것을 말하고 캡처·글 요청 |
| 심사기준 없음 | 대회 종류 프로필로만 만들고 전부 inferred, 보고서 맨 위 "공식 기준 없음" |
| 검사기 3회 실패 | 빈칸 목록을 사용자에게 보여 주고 멈춤 |
| 페르소나 실행 실패·형식 깨짐 | 그 실행만 재시도. 끝내 실패하면 빼고 합산, "N명 중 M명" 표시 |
| 채점 대상 확인 불가 | `claim-not-verified` 상한, "확인 불가" 표시 |
| 서브에이전트 없음 | 차례대로 실행, "독립 실행 아님" 표시 |
| 대회 폴더 없음 | 등록으로 안내 |

## 12. 레포 구조

```
pro-judge/
├── .claude-plugin/{plugin.json, marketplace.json}
├── hooks/session-start.*            # docs/pro-judge/ 있을 때만 길잡이 주입
├── skills/
│   ├── using-pro-judge/SKILL.md
│   ├── pro-judge-setup/{SKILL.md, references/}
│   ├── pro-judge-ideas/SKILL.md
│   ├── pro-judge-score/SKILL.md
│   └── pro-judge-grill/SKILL.md
├── shared/
│   ├── references/{common-caps.md, contest-types/, judge-stance.md, rubric-schema.md, persona-schema.md}
│   └── scripts/{validate_rubric.py, validate_persona.py, aggregate.py, render_report.py, templates/}
├── tests/                           # pytest
└── README.md
```

skills CLI가 skill 폴더 단위로 복사하는지, 공유 폴더를 함께 가져가는지는 구현 계획 첫 단계에서 확인한다.
공유가 안 되면 빌드 스크립트가 `shared/`를 각 skill 폴더로 복사한다.

## 13. 테스트

- **단위(pytest)**: 검사기(정상·결함 픽스처), 합산(중앙값·그룹 가중·게이트·범위), 보고서 생성(정답 json → md/html 스냅샷).
- **Hack-the-Beat 재현**: 공식 루브릭을 입력해 등록 → 12항목·앵커·상한이 `judging-criteria.md`와 맞는지 대조.
- **보정 시험(수동, AI 비용 발생)**: 이룸 `docs/hackathon/raw/역대자료집/` 수상작이 낙선작보다 높게 나오는지.
- **설치**: `npx skills add`로 Claude Code·Codex에 설치 후 skill이 보이는지.

## 14. 범위 밖

- 실제 발표 음성·영상 분석.
- 웹 서비스(호스팅·계정·결제).
- 대회 공고 자동 수집·크롤링.
