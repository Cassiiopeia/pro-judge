---
name: pro-judge-score
description: 자료 채점. 발표자료·기획서·레포·배포 URL을 등록된 대회의 심사위원 페르소나별로 독립 채점하고 합산해 총점·고칠 것 순위·편차 경보를 md·html 보고서로 낸다. 재채점이면 지난 회차와 비교한다. "몇 점이야", "채점해줘", "심사해줘", "다시 봐줘", "고쳤어 다시 봐", "점수 매겨줘" 같은 요청에 사용한다.
---

# 자료 채점

`$SKILL`은 이 SKILL.md가 있는 폴더다. 스크립트는 `python3 $SKILL/shared/scripts/<이름>.py`.

읽는다: `$SKILL/shared/references/judge-stance.md`, `persona-prompt.md`, `persona-output.md`, `common-caps.md`.

## 0. 대회 고르기

`docs/pro-judge/*/rubric.yaml`이 없으면 `pro-judge-setup`으로 보낸다. 둘 이상이면 묻는다.

## 1. 대상 받기

- 파일(PPT·PDF·md): 텍스트를 뽑아 읽는다. 이미지만 있는 슬라이드는 이미지로 읽는다.
- 레포 경로: README, 주요 코드, `git log --oneline | head -50`, 커밋 날짜 분포
  (`git log --format=%ad --date=short | sort | uniq -c`).
- 배포 URL: 실제로 열어 핵심 기능을 눌러 본다. 무엇을 눌렀고 무엇이 됐는지 적는다.
- 확인하지 못한 대상(죽은 URL 등)은 "확인 불가: 이유"로 적는다. 0점이 아니라 `claim-not-verified` 상한이다.

## 2. 비용 알리고 확인받기

"심사위원 N명 × 반복 3회 = 3N회 호출합니다. 반복을 줄일까요?" — 답을 받고 시작한다.

## 3. 런 폴더

```bash
python3 $SKILL/shared/scripts/contest_dirs.py new-run <대회 폴더> score
```

이어서 **채점 대상 원문을 `<런 폴더>/target/`에 텍스트로 저장한다.** 합산이 인용을 이 원문과 대조한다. 원문에 없는 인용은 지워지고,
폴더가 없으면 보고서에 "인용 원문 대조 안 함"이 찍힌다. 페르소나 프롬프트의 `<target>`에도 이 파일들을 준다.

파일(PDF·PPTX·DOCX·md)은 추출 도구로 넣는다:

```bash
python3 $SKILL/shared/scripts/extract_target.py <런 폴더> <파일...> [--pages 27-47]
```

- 슬라이드가 이미지인 PDF 쪽은 OCR한다 (macOS Vision, Windows 내장 OCR, tesseract 중 있는 것).
- `PDF를 읽을 도구가 없습니다`가 나오면 안내된 `pip install` 명령을 사용자에게 알리고 멈춘다.
- `이미지로 읽을 쪽` 목록이 나오면 그 PNG를 직접 열어 읽고, 읽은 글을 `<런 폴더>/target/<이름>-images.txt`에
  `--- <파일> p<쪽> ---` 머리를 달아 덧붙인다. 빈 간지·표지는 건너뛴다.
- OCR한 쪽도 이미지가 `<런 폴더>/target_images/`에 남는다. 앱 화면·도표·색 대비처럼 그림으로만 판단되는 것은
  페르소나가 이 이미지를 직접 연다 — 페르소나 프롬프트의 `<target>`에 이 폴더 경로를 넣는다.
- PPTX는 슬라이드의 글 상자만 읽힌다. 슬라이드 속 그림 글자까지 필요하면 PDF로 내보내 다시 넣는다.
- hwp·ppt·doc은 PDF로 저장해 달라고 한다.

레포는 `repo_facts.py`로 사실을 뽑아 `target/`에 저장하고(fork면 `--upstream`), 배포 URL은 화면에서 읽은 글과 누른 결과 기록을 `target/`에 직접 쓴다.

### 근거 장부

이어서 `pro-judge-gather`를 **대상 모드**로 따른다(장부: `<런 폴더>/evidence.yaml`). 위 수집도 그 절차의 1단계다.
빈칸은 웹에서 찾고, 남으면 사용자에게 배점 큰 항목부터 하나씩 묻는다(최대 5개). 장부가 없으면 보고서에 "근거 장부 없음"이 찍힌다.

## 4. 페르소나별 독립 실행

- `persona-prompt.md` 템플릿을 채워 **서브에이전트 하나 = 페르소나 한 명 × 1회**로 보낸다.
  반복도 각각 새 서브에이전트다. 서로 독립이니 한 번에 띄운다.
- 다른 페르소나의 결과는 절대 프롬프트에 넣지 않는다.
- 가능하면 페르소나마다 다른 모델을 쓴다 (Claude Code: Agent 도구의 `model`을 opus·sonnet·haiku로 돌린다).
  쓴 모델을 기록한다. 모델이 2종 이상이고 전원 5점 이하인 항목은 보고서에 "공통 약점"으로 찍힌다.
- 서브에이전트가 없는 환경이면 직접 차례대로 채점하고 `independent: false`로 기록한다.
  다음 페르소나로 넘어갈 때 앞 점수를 다시 보지 않는다.
- 회차 JSON이 깨지면 그 회차만 한 번 다시 돌린다. 또 깨지면 그 회차를 뺀다.
- 회차를 모아 `<런 폴더>/<persona>.json`으로 저장한다 (`persona-output.md` 형식).

## 5. 합산

```bash
python3 $SKILL/shared/scripts/aggregate.py <런 폴더> --target "<대상 한 줄 설명>"
```

보정용(역대 수상작·낙선작) 채점이면 `--calibration`을 붙인다. 그 회차는 지난 회차 비교와 대시보드 추이에서 빠진다.

`경고:`·`제외:` 줄은 보고할 때 그대로 전한다. 숫자는 손으로 고치지 않는다.

## 6. 총평 쓰기

`<런 폴더>/result.json`에서 `narrative.overall`(3~5문장)과 `narrative.personas.<name>`만 채운다.
총평은 점수와 가장 큰 구멍부터 쓴다. 칭찬으로 시작하지 않는다.

## 7. 보고서

```bash
python3 $SKILL/shared/scripts/render_report.py <런 폴더>
python3 $SKILL/shared/scripts/render_dashboard.py <대회 폴더>
```

## 8. 답하기

총점(이 점수는 진단 지표이지 실제 점수 예측이 아님을 함께), 지난 회차 대비 변화, 고칠 것 Top 3(항목·현재→목표·오를 점수·다음 앵커 문장),
회차마다 흔들린 항목,
편차 경보, `report.html` 경로. 다음 할 일 하나: "가장 약한 <항목>으로 질의응답 연습할까요?"

## 항의를 받으면

새 근거(숫자·고유명사·시연·실증)가 있으면 그 근거를 자료에 넣고 재채점하자고 한다.
새 근거가 없으면 점수를 바꾸지 않고, 무엇이 있으면 몇 점이 되는지만 말한다.
