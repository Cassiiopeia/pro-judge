# 페르소나 독립 실행

채점·아이디어 비교 공통. `<결과 폴더>`는 채점이면 런 폴더, 아이디어 비교면 `<런 폴더>/<idea id>/`.

## 실행 단위
- `persona-prompt.md` 템플릿을 채워 **서브에이전트 하나 = 페르소나 한 명 × 1회**로 보낸다. 반복도 각각 새 서브에이전트. 서로 독립이니 한 번에 띄운다.
- 다른 페르소나의 결과는 절대 프롬프트에 넣지 않는다 (아이디어 비교는 아이디어끼리도 섞지 않는다).
- 가능하면 페르소나마다 다른 모델을 쓴다 (Claude Code: Agent 도구의 `model`을 opus·sonnet·haiku로 돌린다). 쓴 모델을 기록한다.
  모델이 2종 이상이고 전원 5점 이하인 항목은 보고서에 "공통 약점"으로 찍힌다.
- 서브에이전트가 없는 환경이면 직접 차례대로 채점하고 `independent: false`로 기록한다. 다음 페르소나로 넘어갈 때 앞 점수를 다시 보지 않는다.

## 회차 기록 (채팅으로 JSON을 옮겨 적지 않음 — 잘리거나 바뀜)
- 서브에이전트가 자기 회차를 `<결과 폴더>/rounds/<persona>-<회차 번호>.json`에 직접 쓰고 검사한다:
  ```bash
  python3 $SKILL/shared/scripts/score_rounds.py check <결과 폴더> <persona> <회차 파일>
  ```
- 끝내 통과하지 못한 회차는 그 회차만 한 번 다시 돌린다. 또 깨지면 그 회차 파일을 지운다.
- 회차를 모아 `<결과 폴더>/<persona>.json`으로 만든다 (`persona-output.md` 형식):
  ```bash
  python3 $SKILL/shared/scripts/score_rounds.py merge <결과 폴더>
  ```
