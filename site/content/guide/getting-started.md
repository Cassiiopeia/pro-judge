# 시작하기

## 준비

Python 3.9 이상과 PyYAML이 필요하다.

```bash
python3 -m pip install pyyaml
```

PDF 발표자료를 채점하려면 PDF 도구가 하나 있어야 한다. 아래 중 하나를 고른다.

| 도구 | 설치 | 라이선스 | 이미지 쪽(OCR) |
| --- | --- | --- | --- |
| PyMuPDF | `pip install pymupdf` | AGPL-3.0 (상용 라이선스 별도) | 지원 |
| poppler | `brew install poppler` / `apt install poppler-utils` | GPL (별도 프로그램으로 호출) | 지원 |
| pypdf | `pip install pypdf` | BSD | 글자만, 이미지 쪽은 못 읽음 |

이 도구들은 pro-judge에 들어 있지 않다. 사용자가 고른 것을 설치하면 그것을 쓴다.
슬라이드가 그림인 쪽은 OCR로 읽는다 — macOS는 Vision, Windows는 내장 OCR을 쓰므로 따로 설치할 것이 없다.

## 설치

방법은 두 가지다. **하나만 고른다.** 둘 다 설치하면 같은 skill이 두 번 잡힌다.

| | Claude Code 플러그인 | `npx skills` |
| --- | --- | --- |
| 쓰는 곳 | Claude Code | Claude Code, Codex, Cursor 등 [지원 에이전트](https://github.com/vercel-labs/skills#supported-agents) |
| 설치 범위 | 사용자 전체 | 현재 프로젝트(기본) 또는 전체(`-g`) |
| 길잡이 자동 로드 | 대회가 등록된 레포를 열면 켜진다 | 없음. "pro-judge"라고 부른다 |

::: code-group

```text [Claude Code 플러그인]
/plugin marketplace add Cassiiopeia/pro-judge
/plugin install pro-judge@pro-judge
```

```bash [npx skills]
npx skills add Cassiiopeia/pro-judge          # 현재 프로젝트
npx skills add Cassiiopeia/pro-judge -g       # 모든 프로젝트
```

:::

## 처음 쓰기

<video src="/assets/conversation-demo.mp4" controls muted playsinline poster="/assets/conversation-demo.png" style="width:100%;border-radius:10px;border:1px solid var(--vp-c-divider)"></video>

명령어를 외울 필요는 없다. 심사받을 레포에서 에이전트에게 말로 시킨다.

### 1. 대회 등록

```text
이 대회 나갈 거야 https://example.com/공고.pdf
```

공고를 읽고 점수표와 심사위원을 만든다. 공고에 없는 정보(제출 요건·감점 규정·역대 수상작)는 웹에서 찾고, 그래도 없으면 묻는다.

### 2. 아이디어 비교 — 아직 만들기 전이라면

```text
아이디어 3개 중 뭐가 점수 잘 나와?
```

"완벽하게 구현했다면 받을 수 있는 최고 점수"로 순위를 낸다. 대회 취지에서 벗어난 아이디어는 점수가 높아도 아래로 내린다.

### 3. 자료 채점

```text
발표자료 몇 점이야? ./slides.pdf
이 레포 채점해줘
```

자료를 모으고, 빠진 근거가 있으면 배점이 큰 항목부터 하나씩 묻는다.

> 작품 데모 항목에 시연 근거가 없습니다. 시연 영상 링크가 있나요?

그다음 심사위원마다 따로 채점하고 합산해 보고서를 만든다. 고친 뒤 다시 채점하면 지난번 대비 변화도 보여 준다.

### 4. 질의응답 연습

```text
질의응답 연습하자
예상 질문지만 뽑아줘
```

점수가 낮은 곳을 찌르는 질문을 심사위원 말투로 던지고, 답변을 판정한다.

## 결과가 생기는 곳

```text
docs/pro-judge/<대회>/
├── contest.md        공고 요약·취지·제출 요건
├── rubric.yaml       점수표
├── personas/         심사위원
├── evidence.yaml     대회 정보를 어디서 확인했나
├── index.html        회차별 점수 추이
└── runs/<날짜-시각>_score/
    ├── report.html   보고서 (파일 하나, 외부 요청 없음)
    ├── evidence.yaml 무엇을 봤고 무엇을 못 봤나
    └── target/       채점한 원문
```

이 폴더는 기본으로 git에 올라가지 않는다. 팀과 공유하려면 `docs/pro-judge/.gitignore`를 지운다.
