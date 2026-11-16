# 근거 수집

대회 준비(대회 모드)·채점(대상 모드) 공용. 읽는다: `gather-sources.md`, `evidence-schema.md` (같은 폴더).

목표는 채점 전에 **무엇을 봤고 무엇을 못 봤는지**를 장부로 남기는 것. 못 본 것을 선의로 채우지 않는다.
빈칸은 빈칸으로 남겨 보고서에 드러나게 한다.

| 모드 | 부르는 곳 | 장부 위치 | 빈칸 기준 |
| --- | --- | --- | --- |
| 대회(contest) | pj-prepare 3단계 | `docs/pro-judge/<대회>/evidence.yaml` | 고정 주제 7개 (공고·배점·일정·제출 요건·감점 규정·심사위원·역대 수상작) |
| 대상(target) | pj-score 3단계(런 폴더를 만든 직후) | `<런 폴더>/evidence.yaml` | 점수표 항목별 `evidence_types` |

## 1. 자동 수집

받은 것을 모두 연다. 원문은 `<런 폴더>/target/`에 텍스트로 저장한다(합산이 인용을 이 원문과 대조).
출처마다 `sources`에 한 줄씩 적는다 — 어디서(`ref`), 어떻게(`how`), 신뢰 등급(`trust`), 결과(`status`).

- 파일(PDF·PPTX·DOCX·md): `python3 $SKILL/shared/scripts/extract_target.py <런 폴더> <파일...> [--pages 27-47]`
  - 이미지인 PDF 쪽은 OCR한다 (macOS Vision, Windows 내장 OCR, tesseract 중 있는 것)
  - `PDF를 읽을 도구가 없습니다`가 나오면 안내된 `pip install` 명령을 사용자에게 알리고 멈춘다
  - `이미지로 읽을 쪽` 목록이 나오면 그 PNG를 직접 열어 읽고, `<런 폴더>/target/<이름>-images.txt`에
    `--- <파일> p<쪽> ---` 머리를 달아 덧붙인다. 빈 간지·표지는 건너뛴다
  - OCR한 쪽 이미지는 `<런 폴더>/target_images/`에 남는다. 앱 화면·도표·색 대비처럼 그림으로만 판단되는 것은 페르소나가 직접 연다
  - PPTX는 글 상자만 읽힌다. 그림 속 글자까지 필요하면 PDF로 내보내 다시 넣는다. hwp·ppt·doc은 PDF로 저장해 달라고 한다
- 저장소: `python3 $SKILL/shared/scripts/repo_facts.py <저장소> --since <대회 시작> --until <제출 마감> --out <런 폴더>/target/<이름>.txt`
  - README에 "forked from", 원본 저장소 이름, 커밋이 수만 개면 fork다. 원본을 `--upstream`으로 넘겨 팀 커밋만 센다.
    원본을 모르면 사용자에게 묻는다(5단계)
  - 코드·설치·테스트를 실행하지 않는다
- URL·배포 서비스: 가진 도구로 열어 핵심 기능을 눌러 본다. 읽은 글과 누른 것·된 것을 `<런 폴더>/target/<이름>.txt`에 적는다.
  열지 못했으면 `status: failed`와 이유(`note`)를 적는다 — 0점이 아니라 `claim-not-verified` 상한의 근거가 된다
- 시연 영상: 링크와 길이, 볼 수 있었는지만 적는다. 볼 수 없으면 `status: failed`

대회 모드에서는 `<런 폴더>` 대신 `<대회 폴더>/source`를 쓴다.

## 2. 근거 기록

읽은 내용에서 점수표 항목별 근거를 `evidence`에 적는다. 한 줄에 하나. 근거 종류는 점수표의 `evidence_types`와 같은 6가지다.
여러 항목에 두루 쓰이는 사실(커밋 수 등)은 `item: "*"`로 적는다. 의도("~할 예정")는 근거가 아니다 — 적지 않는다.

## 3. 빈칸 계산

```bash
python3 $SKILL/shared/scripts/evidence.py gaps <evidence.yaml> --rubric <대회 폴더>/rubric.yaml   # 대상 모드
python3 $SKILL/shared/scripts/evidence.py gaps <evidence.yaml>                                    # 대회 모드
```

## 4. 웹에서 찾기

웹 검색 도구가 있으면 빈칸마다 `gather-sources.md`의 검색어 틀로 찾는다. 공식 출처(주최 기관·공고)를 먼저, 보도를 다음으로.
찾은 것은 `kind: web`, 출처 URL과 신뢰 등급을 적는다. 도구가 없으면 건너뛰고 장부 맨 위 출처의 `note`에 "웹 검색 도구 없음"을 적는다.

## 5. 사용자에게 묻기

남은 빈칸을 **배점이 큰 항목부터** 한 번에 하나씩 묻는다. 최대 5개. 사용자가 "그만", "몰라"라고 하면 멈춘다.

- 질문은 빈칸을 그대로 말로 바꾼다: "작품 데모 항목에 시연 근거가 없습니다. 시연 영상 링크나 배포 주소가 있나요?"
- 자료를 주면 1단계로 돌아가 그 자료만 수집한다(`kind: user` 진술이 아니라 자료의 종류로 적는다)
- "없다"는 답은 `absent`에 적는다(`source`는 `kind: user` 출처). 같은 것을 다시 묻지 않는다
- 사용자 진술만 있고 자료가 없으면 `kind: user, trust: user`로 적는다. 진술은 7점 이상 인용 근거가 되지 않는다

## 6. 마감

```bash
python3 $SKILL/shared/scripts/evidence.py check <evidence.yaml> --rubric <대회 폴더>/rubric.yaml
```

`OK`가 나올 때까지 고친다. 남은 빈칸 목록을 사용자에게 보여 주고 부른 skill로 돌아간다.
대상 모드의 장부는 합산(`aggregate.py`)이 읽어 보고서의 "확인한 자료와 빈칸" 절에 싣는다. 장부가 없으면 보고서에 "근거 장부 없음"이 찍힌다.

## 하지 않는 것

- 빈칸을 추측으로 채우기 — "아마 있을 것"은 근거가 아니다
- 남의 저장소 코드·설치 스크립트 실행
- 자동으로 찾을 수 있는 것을 사용자에게 묻기 — 1·4단계를 먼저 끝낸다
