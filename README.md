# pro-judge

**대회에 내기 전에 그 대회의 심사위원에게 먼저 채점받는다.**

공고와 심사기준을 주면 에이전트가 심사위원 몇 명이 된다.
각자 따로 내 아이디어·발표자료·레포를 채점하고, **어디를 고치면 몇 점이 오르는지** 순서대로 알려 준다.
예상 질문으로 질의응답 연습도 시킨다. Claude Code·Codex·Cursor 같은 코딩 에이전트에서 쓰는 Agent Skills다.

<p align="center">
  <img src="assets/report-desktop.png" alt="채점 보고서 화면 — 총점, 항목별 막대, 고칠 것 순위" width="720">
</p>

> 위 화면은 이 레포를 「제10회 공개SW 개발자대회」 심사기준으로 채점한 실제 결과다.
> 전체 보고서: [`examples/공개SW-개발자대회/`](examples/공개SW-개발자대회/runs/20261008-0957_score/report.md)

## 무엇이 다른가

LLM에게 "심사위원처럼 채점해 줘"라고 한 줄로 시키면 점수가 70~85점에 몰리고, 무엇이 없어서 깎였는지 알 수 없다
([검증 결과](#검증-결과) 참고). pro-judge는 판단은 에이전트에게, 숫자는 스크립트에게 맡긴다.

- **점수표를 먼저 만든다.** 한 줄짜리 심사기준도 판정 질문, 0·5·10점 기준 문장, 상한 규칙을 갖춘 점수표로 펼친다. 공고에 없는 규칙은 "추정"으로 표시한다.
- **심사위원마다 따로 채점한다.** 서로의 점수를 보지 않고 매기고, 의견이 크게 갈린 항목은 경보로 알린다.
- **규칙은 합산 단계에서 강제한다.** 7점 이상에는 자료에서 그대로 옮긴 인용이 필요하고, 자료에 없는 인용은 지운다. 시연 영상이 없으면 데모 점수는 상한에 묶인다. 같은 채점 원자료를 넣으면 늘 같은 숫자가 나온다.
- **할 일을 점수로 말한다.** "커뮤니티 항목을 다음 기준 문장까지 올리면 +8점, 그 기준 문장은 이것"처럼 고칠 것을 오르는 점수 순으로 보여 준다.

## 설치

필요한 것: Python 3.9 이상, PyYAML

```bash
python3 -m pip install pyyaml
python3 -m pip install pymupdf   # 선택: PDF 발표자료를 채점할 때 (Windows·macOS·Linux 공통)
```

슬라이드가 이미지인 PDF는 쪽마다 OCR한다. macOS는 Vision, Windows는 내장 OCR을 쓰므로 따로 설치할 것이 없다.
OCR을 쓸 수 없는 환경에서는 그 쪽을 이미지로 저장해 에이전트가 직접 읽는다.

설치 방법은 두 가지다. **하나만 고른다.** 둘 다 설치하면 같은 skill이 두 번 잡힌다.

| | Claude Code 플러그인 | `npx skills` |
| --- | --- | --- |
| 쓰는 곳 | Claude Code | Claude Code, Codex, Cursor 등 [지원 에이전트](https://github.com/vercel-labs/skills#supported-agents) |
| 설치 범위 | 사용자 전체 | 현재 프로젝트(기본) 또는 사용자 전체(`-g`) |
| 길잡이 자동 로드 | 대회가 등록된 레포를 열면 자동으로 켜진다 | 없음. "pro-judge"라고 부르면 된다 |
| 업데이트 | `/plugin marketplace update pro-judge` | `npx skills update` |

### Claude Code 플러그인

Claude Code 안에서:

```
/plugin marketplace add Cassiiopeia/pro-judge
/plugin install pro-judge@pro-judge
```

### npx skills ([vercel-labs/skills](https://github.com/vercel-labs/skills))

```bash
npx skills add Cassiiopeia/pro-judge                 # 현재 프로젝트에 설치 (에이전트를 고르라고 묻는다)
npx skills add Cassiiopeia/pro-judge -g              # 모든 프로젝트에서 쓰기
npx skills add Cassiiopeia/pro-judge -a codex -y     # 에이전트를 지정해 묻지 않고 설치
```

## 처음 쓰기

설치한 뒤 심사받을 레포(또는 아무 폴더)에서 에이전트에게 말로 시킨다. 명령어를 외울 필요는 없다.

### 1. 대회 등록

```
이 대회 나갈 거야 https://example.com/공고.pdf
```

에이전트가 공고를 읽고 점수표와 심사위원 페르소나를 만든 뒤 보여 준다.
공고에 심사기준이 없으면 대회 종류(오픈소스, 장애인 정보접근, 사회문제 해결, 창업, 공공데이터, AI 기술)에 맞춘 기본 기준에서 시작하고, 그 사실을 보고서에 표시한다.

### 2. 아이디어 비교 (아직 만들기 전이라면)

```
아이디어 3개 중 뭐가 점수 잘 나와?
1) ... 2) ... 3) ...
```

"완벽하게 구현했다면 받을 수 있는 최고 점수"로 순위를 낸다. 대회 취지에서 벗어난 아이디어는 점수가 높아도 아래로 내린다.

### 3. 자료 채점

```
발표자료 몇 점이야? ./slides.pdf
이 레포 채점해줘
```

심사위원마다 따로 채점한 뒤 합산해 보고서를 만든다. 자료를 고친 뒤 다시 채점하면 지난번 대비 몇 점이 바뀌었는지도 보여 준다.

### 4. 질의응답 연습

```
질의응답 연습하자
예상 질문지만 뽑아줘
```

점수가 낮은 곳을 찌르는 질문을 심사위원 말투로 던지고, 내 답변을 판정한다. 질문지만 뽑으면 질문마다 모범 답변 뼈대를 붙인다.

## 결과는 어디에 생기나

```
docs/pro-judge/
└── <대회 이름>/
    ├── contest.md          공고 요약, 대회 취지
    ├── rubric.yaml         점수표
    ├── personas/           심사위원 페르소나
    ├── index.html          회차별 점수 추이 (브라우저로 연다)
    ├── history.md
    └── runs/
        └── 20261008-1405_score/
            ├── report.html     보고서 (외부 요청 없는 파일 하나)
            ├── report.md
            └── result.json
```

이 폴더는 처음 만들 때 `.gitignore`가 함께 생겨 **기본으로 git에 올라가지 않는다.** 팀과 공유하려면 그 `.gitignore`를 지운다.

## 점수를 어떻게 읽나

- **진단 지표다. 실제 대회 점수 예측이 아니다.** 같은 점수표로 고치기 전과 후를 비교하는 데 쓴다.
- 총점 옆 범위는 "공고에 없어 추정한 규칙을 ±1점 움직였을 때"의 폭이다. 통계적 신뢰구간이 아니다.
- 보고서 맨 위의 주황색 안내를 먼저 본다. "인용 원문 대조 안 함"이 있으면 7점 이상 점수를 그대로 믿지 않는다.
- 역대 수상작을 같은 점수표로 채점해 두면("작년 대상작 보정용으로 채점해줘") 내 점수를 어디에 견줄지 감을 잡을 수 있다. 보정 채점은 내 회차 비교와 추이에 섞이지 않는다.

## 검증 결과

실제 수상 결과가 공개된 대회로 맞혀 봤다. 2025 장애인 분야 해커톤 「장애 플러스 기술」(한국장애인재단) 본선 8팀의
공개 자료집(개발제안서·개발노트·본선 발표 PPT·실증보고서, PPT는 OCR)을 팀마다 따로 채점했다.
심사위원 3명(장애 현장 전문가·기술 전문가·시민평가단) × 1회, 같은 자료를 한 줄 프롬프트로 3회 채점한 것과 비교했다.

| 분야 | 실제 장관상 | pro-judge | 한 줄 프롬프트 |
| --- | --- | --- | --- |
| 디지털 포용 (5팀) | 센소리아 | 4위 (51.2점) | 4위 (평균 74.7점) |
| 자립생활 지원 (3팀) | 토닥이 | 1위 (57.3점, 2위와 0.1점 차) | 2위 (평균 76.3점) |

- **순위는 맞히지 못했다.** 2개 분야 중 1개만 맞았고 그것도 동점에 가깝다. 한 줄 프롬프트와 순위도 거의 같았다.
- **점수 폭은 넓다.** pro-judge는 47~67점, 한 줄 프롬프트는 69~85점이었다. 한 줄 프롬프트는 3회 반복해도 폭이 1~4점으로 안정적이었지만, 모든 팀을 비슷하게 높게 줬다.
- **빗나간 이유가 보인다.** 센소리아는 출처 있는 통계·기획 단계 인터뷰·접근성 점검이 자료에 없어 필요성과 기대효과에서 깎였다. 실제 심사는 현장 시연과 발표를 본다. pro-judge는 자료에 적힌 근거만 본다.

그래서 pro-judge는 **수상 여부를 맞히는 도구가 아니다.** "심사위원이 자료에서 무엇을 찾지 못하는가"를 항목별로 짚고,
고친 뒤 같은 점수표로 다시 재는 진단 도구로 쓴다. 시연·발표의 인상은 질의응답 연습(`pro-judge-grill`)과 사람의 리허설로 채운다.

## 업데이트와 버전

```bash
npx skills update                                    # 바뀐 skill만 다시 받는다
npx skills add Cassiiopeia/pro-judge#v0.1.1          # 특정 릴리스로 고정
```

Claude Code 플러그인은 `/plugin marketplace update pro-judge`로 갱신한다.
릴리스마다 `v<버전>` 태그와 [CHANGELOG](CHANGELOG.md)가 남는다.

## 제거

```bash
npx skills remove using-pro-judge pro-judge-setup pro-judge-ideas pro-judge-score pro-judge-grill
```

플러그인은 `/plugin uninstall pro-judge@pro-judge`. 대회 자료(`docs/pro-judge/`)는 지워지지 않는다.

## 구성

| skill | 하는 일 |
| --- | --- |
| `using-pro-judge` | 길잡이. 요청을 알아듣고 아래 skill을 부른다 |
| `pro-judge-setup` | 대회 등록. 공고·심사기준 → 점수표 + 페르소나 + 취지 |
| `pro-judge-ideas` | 아이디어 비교. 완벽히 구현했다면 받을 상한 점수로 순위 |
| `pro-judge-score` | 자료 채점. 페르소나별 독립 채점, 고칠 것 순위 |
| `pro-judge-grill` | 질의응답 연습. 약한 곳을 찌르는 질문과 답변 판정 |

## 개발

```bash
python3 -m pytest              # 테스트
python3 tools/sync_shared.py   # shared/ 를 고친 뒤 각 skill로 복사
```

`skills/*/shared/`는 `shared/`의 사본이다. `npx skills`는 skill 폴더 하나만 복사하므로 공용 스크립트를 각 skill에 넣어 둔다.
직접 고치지 말고 `shared/`를 고친 뒤 `tools/sync_shared.py`를 돌린다. 사본이 어긋나면 테스트가 실패한다.

## 라이선스

[Apache-2.0](LICENSE)

---

<!-- AUTO-VERSION-SECTION: DO NOT EDIT MANUALLY -->
## 최신 버전 : v0.2.0 (2026-10-08)

[전체 버전 기록 보기](CHANGELOG.md)
