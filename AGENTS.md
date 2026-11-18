# AGENTS.md

pro-judge에서 일하는 코딩 에이전트용 안내. 사람용 규칙의 원본은 [CONTRIBUTING.md](CONTRIBUTING.md)이고, 여기는 에이전트가 자주 놓치는 것만 적는다.

## 구조

| 경로 | 내용 |
| --- | --- |
| `skills/pj-prepare/`, `skills/pj-score/`, `skills/pj-qna/` | skill 3개 (대회 준비, 채점, 질의응답). 본문은 각 `SKILL.md` |
| `shared/scripts/`, `shared/references/` | 공용 스크립트·참고 문서의 **원본** |
| `skills/*/shared/` | `shared/`의 **생성된 사본** (`npx skills`가 skill 폴더 하나만 복사하기 때문) |
| `hooks/` | 세션 시작 시 길잡이(`pro-judge-guide.md`) 주입 |
| `tests/` | pytest. 사본 일치·skill 참조 경로·대회 종류 목록도 여기서 검사 |
| `examples/`, `assets/` | 예시 보고서와 캡처 (생성물, 사이트 빌드 때 복사) |
| `site/content/` | 문서 사이트(VitePress) 원본 |

## 반드시 지킬 것

1. **`skills/*/shared/`를 직접 고치지 않는다.** `shared/`를 고친 뒤 `python3 tools/sync_shared.py`를 돌린다.
2. **끝내기 전에 두 명령이 통과해야 한다.** PR에서도 같은 검사가 돈다 (`.github/workflows/PROJECT-TEST.yaml`).
   ```bash
   python3 tools/sync_shared.py --check
   python3 -m pytest -q
   ```
3. **Python 3.9에서도 돌아야 한다.** 3.12 이상 전용 문법(f-string 안 역슬래시·같은 따옴표 중첩 등)을 쓰지 않는다.
4. **새 외부 의존성을 넣지 않는다.** 필수는 PyYAML 하나. AGPL·GPL 도구(PyMuPDF·poppler)를 skill 폴더에 넣지 않는다.
5. **숫자를 지어내지 않는다.** 검증 결과·점수 기대값은 측정하거나 손으로 계산한 것만 쓰고, 방법을 PR에 적는다.
6. PR은 `develop`으로. `main`은 릴리스 전용이다.

## 자주 하는 변경

- 대회 종류 추가, 점수 계산 변경, 보고서 모양 변경: [CONTRIBUTING.md](CONTRIBUTING.md) '자주 하는 변경' 절을 따른다.
- 보고서 모양을 바꾸면 `examples/` 보고서를 다시 만들어 함께 커밋한다.
