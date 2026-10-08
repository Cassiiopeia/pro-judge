# pro-judge

대회에 나가기 전에 **실제 심사를 미리 받아 보는** Agent Skills 묶음이다.

심사기준을 주면 에이전트가 그 대회의 심사위원이 된다.
한 줄짜리 기준도 판정 질문·0/5/10 앵커·상한 규칙을 갖춘 점수표로 펼치고,
대회 취지에 맞춘 심사위원 페르소나를 만들어 아이디어·발표자료·레포·배포 서비스를 채점한다.
날카로운 질문으로 질의응답을 연습시키고, 결과를 md·html 보고서로 낸다.

## 구성

| skill | 하는 일 |
| --- | --- |
| `using-pro-judge` | 길잡이 — 요청을 알아듣고 아래 skill을 부른다 |
| `pro-judge-setup` | 대회 등록 — 공고·심사기준 → 점수표 + 페르소나 + 취지 |
| `pro-judge-ideas` | 아이디어 비교 — 완벽히 구현했다면 받을 상한 점수로 순위 |
| `pro-judge-score` | 자료 채점 — 페르소나별 독립 채점, 고칠 것 순위 |
| `pro-judge-grill` | 질의응답 연습 — 약한 곳을 찌르는 질문과 답변 판정 |

## 설치

필요: Python 3.9+, PyYAML (`python3 -m pip install pyyaml`)

Claude Code·Codex·Cursor 등 ([vercel-labs/skills](https://github.com/vercel-labs/skills)):

```bash
npx skills add Cassiiopeia/pro-judge
```

Claude Code 플러그인(대회가 등록된 레포에서 길잡이 자동 로드):

```
/plugin marketplace add Cassiiopeia/pro-judge
/plugin install pro-judge@pro-judge
```

## 업데이트

```bash
npx skills update                                  # 바뀐 skill만 다시 받는다
npx skills add Cassiiopeia/pro-judge#v0.1.0        # 특정 릴리스로 고정
```

Claude Code 플러그인은 `/plugin marketplace update pro-judge`로 갱신한다.
릴리스마다 `v<버전>` 태그와 [CHANGELOG](CHANGELOG.md)가 남는다. 버전은 `version.yml`이 기준이다.

## 사용

```
이 대회 나갈 거야 <공고 URL>
아이디어 3개 중 뭐가 점수 잘 나와?
발표자료 몇 점이야? ./slides.pdf
질의응답 연습하자
```

대회 자료는 심사받는 레포의 `docs/pro-judge/<대회>/`에 쌓인다. 이 폴더는 기본으로 git에서 빠진다.

## 개발

```bash
python3 -m pytest              # 테스트
python3 tools/sync_shared.py   # shared/ 를 고친 뒤 각 skill로 복사
```

`skills/*/shared/`는 생성물이다. 직접 고치지 말고 `shared/`를 고친다.

---

<!-- AUTO-VERSION-SECTION: DO NOT EDIT MANUALLY -->
## 최신 버전 : v0.1.0 (2026-10-08)

[전체 버전 기록 보기](CHANGELOG.md)
