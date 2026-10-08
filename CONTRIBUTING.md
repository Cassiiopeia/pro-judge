# 기여 안내

pro-judge에 이슈나 PR을 보내 주셔서 고맙습니다. 아래만 지키면 바로 리뷰할 수 있습니다.

## 환경

```bash
python3 -m pip install pyyaml pytest
python3 -m pip install pymupdf      # 선택: PDF 추출을 실제 파일로 돌려 볼 때 (AGPL-3.0 — pro-judge에 포함하지 않는다)
python3 -m pytest                    # 모두 통과해야 PR을 받는다
```

Python 3.9 이상. 새 외부 의존성은 넣지 않는다 — PyYAML 하나만 필수다. PDF·OCR 도구는 있으면 쓰고 없으면 대체 경로로 간다.
PyMuPDF(AGPL-3.0)·poppler(GPL)를 skill 폴더에 넣거나 함께 배포하지 않는다 — 사용자가 고른 도구를 설치해 쓰게 둔다.

## 흐름

1. 이슈를 먼저 연다. 버그는 재현 절차, 기능은 "어떤 대회 준비자가 무엇을 못 해서" 필요한지 적는다.
2. `develop`에서 브랜치를 만든다. PR도 **`develop`으로** 연다. `main`은 릴리스 전용이다.
3. 테스트를 먼저 쓰고(고치기 전에 실패하는 것을 확인), 고친 뒤 `python3 -m pytest`를 통과시킨다.
4. PR 본문에 이슈 링크와 테스트 결과를 적는다.

커밋 메시지 형식: `<이슈 제목> : <feat|fix|docs|refactor|test|chore> : <무엇을 왜> <이슈 URL>`

## 자주 하는 변경

### 스크립트·참고 문서를 고칠 때

`skills/*/shared/`는 `shared/`의 사본이다. `npx skills`가 skill 폴더 하나만 복사하기 때문에 사본을 커밋한다.

```bash
# shared/ 를 고친 뒤
python3 tools/sync_shared.py
```

사본을 직접 고치거나 sync를 빠뜨리면 `test_repo_copies_in_sync`가 실패한다.

### 대회 종류를 추가할 때 (예: 스포츠 대회)

세 곳을 함께 고친다. 하나라도 빠지면 `test_contest_types_listed_everywhere`가 실패한다.

1. `shared/references/contest-types/<id>.md` — 기대, 보이지 않는 감점, 추천 상한 규칙, 취지 질문, 페르소나 후보
   (`disability.md`를 본보기로)
2. `shared/references/rubric-schema.md` — `purpose.contest_types` 줄의 목록
3. `shared/scripts/validate_rubric.py` — `CONTEST_TYPES`

그리고 `python3 tools/sync_shared.py`.

상한 규칙과 기준 문장에는 **관찰 가능한 말**만 쓴다("잘했다·충분하다·적절하다·우수하다·훌륭하다"는 검사기가 거부한다).
근거가 공고가 아니라 경험이면 `source: inferred`와 `why`를 단다.

### 점수 계산을 바꿀 때

`aggregate.py`의 숫자는 테스트(`tests/test_aggregate.py`, `tests/test_design_fixes.py`)에 손으로 계산한 기대값이 있다.
계산을 바꾸면 기대값을 어떻게 다시 계산했는지 PR에 적는다. 같은 원자료에 다른 숫자가 나오는 변경은 이유가 필요하다.

### 보고서 모양을 바꿀 때

`examples/`의 보고서와 `assets/` 캡처는 생성물이다. 바꾼 뒤 다시 만들어 함께 커밋한다.

```bash
X=examples/공개SW-개발자대회
python3 shared/scripts/render_report.py $X/runs/20261008-0957_score
python3 shared/scripts/render_report.py $X/runs/20261008-1000_grill
python3 shared/scripts/render_dashboard.py $X
```

### 문서 사이트를 고칠 때

사이트(https://cassiiopeia.github.io/pro-judge/)의 원본은 `site/content/`의 md다. main에 반영되면 자동으로 배포된다.

```bash
cd site && npm ci && npm run docs:dev     # http://localhost:5173/pro-judge/
```

예시 보고서(`examples/`)와 캡처(`assets/`)는 빌드할 때 사이트로 복사된다. 사본(`site/content/public/`)을 고치지 않는다.

## AI 기여 정책

코딩 에이전트(Claude Code, Codex, Cursor 등)로 만든 이슈·PR을 받는다. 이 레포 자체가 에이전트로 만들어졌다. 다만:

- **사람이 책임진다.** PR을 연 사람이 변경 전체를 읽고 이해한 상태여야 한다. 리뷰 질문에 "에이전트가 그렇게 했다"는 답이 되지 않는다.
- **테스트가 증거다.** 동작을 바꾸는 PR은 고치기 전에 실패하는 테스트가 있어야 한다. 테스트 없는 대량 변경은 닫는다.
- **실측을 적는다.** OCR·PDF·설치처럼 환경을 타는 변경은 어떤 OS에서 무엇을 실제로 돌렸는지 적는다. 돌려 보지 못했으면 "미실측"이라고 쓴다.
- **숫자를 지어내지 않는다.** README·문서의 수치(검증 결과, 지원 수 등)는 측정한 것만 쓴다. 측정 방법을 PR에 적는다.
- **범위를 지킨다.** 이슈와 무관한 리팩터링·포맷 변경을 섞지 않는다.
- AI 서명 줄(`Co-Authored-By` 등)은 넣어도 되고 빼도 된다.

## 신고

보안 문제(예: 채점 대상 파일로 임의 명령이 실행되는 경우)는 공개 이슈에 쓰지 않고 GitHub의
[비공개 취약점 신고](https://github.com/Cassiiopeia/pro-judge/security/advisories/new)로 알려 준다.
