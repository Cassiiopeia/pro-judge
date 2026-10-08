# 제10회 공개SW 개발자대회 채점 보고서

2026-10-08T11:41 · 회차 20261008-0957_score · 대상 pro-judge 레포 (2026-10-08 커밋 3b1f52a 시점)

> **진단 지표** 이 점수는 아래 점수표로 잰 상대 진단이다. 실제 대회에서 받을 점수의 예측이 아니다. 같은 점수표로 고치기 전후를 비교하는 데 쓴다.

> **인용 원문 대조 안 함** 채점 대상 원문(target/)이 없어 인용이 실제 자료에 있는지 확인하지 못했다. 7점 이상 점수를 그대로 믿지 않는다.

> **보정 안 됨** 역대 수상작으로 점수표를 검증하지 않았다.

## 총점

31.7 / 100 (추정 규칙 민감도 26.3 ~ 37.7: 추정 규칙이 걸린 항목을 ±1점 움직인 값, 신뢰구간 아님 · 추정 규칙 비중 60%)

| 항목 | 점수 | |
|---|---|---|
| 코딩의 적절성 및 구조의 합리성 | 2.92 / 5 | ████████████░░░░░░░░ |
| 코드의 완성도 및 시연가능성 | 2.58 / 5 | ██████████░░░░░░░░░░ |
| 개발 문서의 구체성 | 2.58 / 5 | ██████████░░░░░░░░░░ |
| 프로젝트 수준 | 2.5 / 5 | ██████████░░░░░░░░░░ |
| 기능테스트 결과 | 2.5 / 5 | ██████████░░░░░░░░░░ |
| 작품 발표 | 0.33 / 10 | █░░░░░░░░░░░░░░░░░░░ |
| 공개SW 활용성 | 3.5 / 10 | ███████░░░░░░░░░░░░░ |
| 독창성 | 4.75 / 15 | ██████░░░░░░░░░░░░░░ |
| 커뮤니티로 발전가능성 | 2 / 20 | ██░░░░░░░░░░░░░░░░░░ |
| 작품 데모 | 8 / 20 | ████████░░░░░░░░░░░░ |

## 고칠 것 Top 5

다음 앵커(5점 또는 10점) 수준까지 올렸을 때 오르는 총점 순서다. '다음 앵커' 문장이 자료에 생기게 만드는 것이 할 일이다.

| 순위 | 항목 | 현재 → 목표 | 오르는 점수 | 다음 앵커 | 걸린 상한 | 해제 조건 |
|---|---|---|---|---|---|---|
| 1 | 커뮤니티로 발전가능성 | 1.0 → 5 | +8 | 기여 경로 문서는 있으나 외부 기여자·외부 이슈가 0건이다 | no-license | LICENSE, CONTRIBUTING 또는 이슈 템플릿, 대회 기간 전체에 걸친 커밋 이력(현재 14개 커밋이 하루, 작성자 1명), 외부 기여자·이슈 숫자, 담당과 기간이 적힌 유지 계획이 있어야 합니다. |
| 2 | 작품 발표 | 0.3 → 5 | +4.7 | 발표자료는 있으나 문제 규모나 결과에 숫자가 없다 | no-deck | 문제 규모와 결과 숫자, 시연 화면을 담은 발표자료(PPT/PDF)나 발표 영상이 제출돼야 합니다. |
| 3 | 독창성 | 3.2 → 5 | +2.8 | 차별점을 말하지만 비교한 기존 도구 이름이 없다 | - | 기존 도구(예: LLM-as-judge 평가 도구 2개 이상)를 이름으로 비교한 표와, 그 차이가 구현된 코드 위치가 있으면 8점 이상입니다. 근거는요? 비교 대상이 없습니다. |
| 4 | 프로젝트 수준 | 5.0 → 10 | +2.5 | 기술적 난점 2개 이상을 문서에서 설명하고 그 부분이 코드와 테스트로 확인된다 | - | 상한 규칙 합산과 같은 기술적 난점 2개 이상을 문서에서 설명하고 코드량·커밋 기간 숫자를 제시하면 8점 이상입니다. |
| 5 | 기능테스트 결과 | 5.0 → 10 | +2.5 | 명시 기능 전부가 통과하고 예외 입력에 오류 메시지 한 줄로 응답한다 | - | - |

## 편차 경보

- (없음)

## 회차마다 흔들린 항목

- (없음)

## 공통 약점 (모델 2종 이상, 전원 5점 이하)

- 프로젝트 수준
- 기능테스트 결과
- 작품 발표
- 공개SW 활용성
- 독창성
- 커뮤니티로 발전가능성
- 작품 데모

## 항목별

| 항목 | 득점 / 배점 | 심사위원별 | 상한 | 인용 | 변화 |
|---|---|---|---|---|---|
| 코딩의 적절성 및 구조의 합리성 | 2.92 / 5 | academic 6, community-lead 5, industry-dev 6.5 | - | `skills/*/shared/`는 생성물이다. 직접 고치지 말고 `shared/`를 고친다. / class InputError(Exception):     """사용자가 고칠 수 있는 입력 오류. CLI는 메시지 한 줄만 찍고 끝낸다.""" | - |
| 코드의 완성도 및 시연가능성 | 2.58 / 5 | academic 5, community-lead 5.5, industry-dev 5 | - | python3 -m pytest              # 테스트 / 필요: Python 3.9+, PyYAML (`python3 -m pip install pyyaml`) | - |
| 개발 문서의 구체성 | 2.58 / 5 | academic 4.5, community-lead 5.5, industry-dev 5.5 | - | python3 $SKILL/shared/scripts/contest_dirs.py new-run &lt;대회 폴더&gt; score / # 설계·계획 문서는 로컬 전용 /docs/ | - |
| 프로젝트 수준 | 2.5 / 5 | academic 5, community-lead 5, industry-dev 5 | - | 같은 입력이면 같은 숫자가 나와야 하므로 점수 계산은 전부 여기서 한다. | - |
| 기능테스트 결과 | 2.5 / 5 | verifier 5 | - | (인용 없음) | - |
| 작품 발표 | 0.33 / 10 | academic 1, community-lead 0, industry-dev 0 | no-deck | (인용 없음) | - |
| 공개SW 활용성 | 3.5 / 10 | academic 4, community-lead 3, industry-dev 3.5 | no-license | npx skills add Cassiiopeia/pro-judge | - |
| 독창성 | 4.75 / 15 | academic 3, community-lead 2, industry-dev 4.5 | - | 대회에 나가기 전에 **실제 심사를 미리 받아 보는** Agent Skills 묶음이다. | - |
| 커뮤니티로 발전가능성 | 2 / 20 | academic 1, community-lead 0, industry-dev 2 | no-license | (인용 없음) | - |
| 작품 데모 | 8 / 20 | academic 3, community-lead 5, industry-dev 4 | no-demo-material | 이 대회 나갈 거야 &lt;공고 URL&gt; | - |

## 총평

코드와 테스트는 1차 평가에서 중간 점수를 받지만, 배점 75점인 2차 평가에서 LICENSE·기여 경로·발표자료·시연 영상이 없어 상한에 막혔다. 가장 큰 손실은 커뮤니티로 발전가능성(20점 중 2점)과 작품 데모(20점 중 8점)다. LICENSE와 CONTRIBUTING을 넣고, 설치부터 보고서까지 3분 시연 영상을 만들고, 기존 LLM 평가 도구와의 비교표를 README에 두는 것이 먼저다.

## 심사위원별 총평

- academic (judges, sonnet): 비교 대상 없는 독창성 주장도, 평가 숫자도, 설계 근거 문서도 커밋돼 있지 않습니다. 근거는요? 코드와 테스트(85 passed, 1 failed)는 있으나 LICENSE, CONTRIBUTING, 발표자료, 시연 영상이 없어 공개SW 활용성, 커뮤니티, 발표, 데모 항목이 상한에 걸립니다. 기존 도구와의 비교표, 설계 근거와 버린 대안, 정량 평가 결과가 문서로 들어오면 점수가 크게 오릅니다.
- community-lead (judges, haiku): LICENSE 파일이 레포 루트에 없고 CONTRIBUTING·이슈 템플릿도 없습니다. 커밋 14개가 2026-10-08 하루에 작성자 1명으로 쌓였고 외부 기여자와 외부 이슈는 0건입니다. 발표자료와 시연 영상이 없어 발표·데모 항목은 상한에 걸립니다.
- industry-dev (judges, opus): HEAD 기준 테스트 86개 통과는 직접 돌려서 확인했습니다. 모듈은 나뉘어 있고 입력 오류는 한 줄로 처리됩니다. 하지만 LICENSE, 기여 경로, 발표자료, 시연 영상이 없고 커밋은 하루 동안 1명이 했습니다. 그래서 2차 평가 항목은 상한에 막힙니다. 돌려 봤나요? skill 5종이 README 설치 절차대로 동작하는 것을 보여 주는 영상부터 내야 합니다.
- verifier (verification, opus): HEAD 348ac72를 따로 꺼내 테스트를 돌린 결과 86개 전부 통과했고, contest_dirs init/new-run → validate_rubric → validate_persona → aggregate → render_report → render_dashboard 순서로 실제로 돌려도 정상 동작했다(총점 62.0, report.md/html·index.html 생성). 예외 입력은 실패다. ideas.json·result.json·history.md가 없는 폴더를 넣으면 rank_ideas·render_report·render_dashboard가 FileNotFoundError traceback을 낸다. rubric.yaml 문법이 깨져 있으면 validate_rubric·validate_persona·render_dashboard·aggregate가 YAML traceback을 내고, 이 경우들은 모두 종료코드 0으로 끝난다. LICENSE·CONTRIBUTING 파일, 발표자료, 시연 영상은 없다.

## 부록

추정(inferred) 규칙 — 공고에 없어 에이전트가 정한 것

- evaluator_groups(verification): 제10회 문서는 기능테스트를 '발표 평가 전 별도 진행'으로만 적고 수행 주체가 없다. 2026 공고의 '전문 검증기관' 표현을 따라 별도 그룹으로 뒀다
- items[code-structure] 질문 '모듈·파일이 책임 단위로 나뉘어 있고 중복이 없는가': 구조의 합리성은 책임 분리와 중복으로 관찰된다
- items[code-structure] 질문 '코드 규칙(이름·주석·에러 처리)이 레포 전체에서 일관된가': 코딩의 적절성을 관찰 가능한 일관성으로 바꿨다
- items[code-completeness] 질문 'README 절차만으로 외부인이 설치·실행할 수 있는가': 시연가능성의 1차 근거는 재현 가능한 실행 절차
- items[code-completeness] 질문 '자동 테스트가 있고 통과하는가': 완성도를 숫자로 확인할 수 있는 근거
- items[code-completeness] 상한 no-run-instructions(4): 실행 절차가 없으면 심사위원이 시연가능성을 확인할 방법이 없다
- items[doc-specificity] 질문 '설계·구조·사용법이 문서로 있는가': 프로젝트 Document가 1차 제출물이다
- items[doc-specificity] 질문 '문서에 숫자·명령·파일 경로처럼 따라 할 수 있는 내용이 있는가': 구체성은 따라 할 수 있는 내용의 양으로 관찰된다
- items[project-level] 질문 '기술적 난이도가 있는 부분이 무엇이고 그것이 동작하는가': 수준은 어려운 문제를 실제로 풀었는지로 판단된다
- items[project-level] 질문 '규모(코드량·기능 수·커밋 기간)가 숫자로 드러나는가': 수준 비교는 숫자로만 가능하다
- items[function-test] 질문 '명시된 기능을 테스트 절차대로 돌렸을 때 통과하는가': 기능테스트는 명시 기능 대비 통과 여부
- items[function-test] 질문 '실패·예외 입력에서 오류 메시지가 나오는가': 검증기관 테스트는 예외 경로도 본다
- items[presentation] 질문 '10분 안에 문제·해결·결과를 숫자와 함께 전달하는가': 발표 10분 + Q&A 5분 형식
- items[presentation] 질문 'Q&A에서 근거를 들어 답하는가': 15분 PT에 Q&A 5분이 포함된다
- items[presentation] 상한 no-deck(3): 발표 항목은 발표자료 없이는 평가 대상이 없다
- items[oss-usage] 질문 'OSI 승인 라이선스로 공개되어 있는가': 공개SW의 전제 조건
- items[oss-usage] 질문 '다른 사람이 가져다 쓸 수 있는 단위(라이브러리·CLI·플러그인)로 나와 있는가': 활용성은 재사용 단위가 있는지로 관찰된다
- items[oss-usage] 질문 '사용한 오픈소스 의존성과 그 라이선스를 밝히는가': 라이선스 검증(분석보고서)이 대회 절차에 있다
- items[oss-usage] 상한 no-license(4): 라이선스 없는 코드는 재사용이 불가능해 오픈소스로 볼 수 없다
- items[originality] 질문 '기존 도구 이름을 들고 무엇이 다른지 밝히는가': 독창성은 비교 대상이 있어야 판단된다
- items[originality] 질문 '그 차이가 코드에 실제로 구현돼 있는가': 주장만 있는 차별점은 의도다
- items[community-potential] 질문 '외부 기여자가 첫 PR을 보낼 경로(CONTRIBUTING·이슈 템플릿·테스트 방법)가 있는가': 커뮤니티의 입구는 기여 경로
- items[community-potential] 질문 '이미 외부 사용자·기여자·이슈가 있는가': 발전가능성의 가장 직접적인 근거는 현재 참여자 수
- items[community-potential] 질문 '대회 뒤 누가 유지보수하는지 밝히는가': 유지 주체가 없으면 커뮤니티가 자라지 않는다
- items[community-potential] 상한 no-contribution-path(6): 외부 기여 경로가 없으면 공개된 코드일 뿐 오픈소스 프로젝트가 아니다
- items[community-potential] 상한 no-license(4): 라이선스 없이는 외부인이 법적으로 기여·재사용할 수 없다
- items[community-potential] 상한 last-minute-commits(6): 일괄 커밋은 공개 개발 과정이 없었다는 신호다
- items[demo] 질문 '핵심 기능을 실제 입력으로 시연하는가': 데모는 실제 동작으로만 확인된다
- items[demo] 질문 '시연 결과를 심사위원이 재현할 수 있는가': 재현 불가한 데모는 녹화본과 같다
- items[demo] 상한 no-demo-material(5): 1차 제출물에 시연 동영상이 필수로 들어 있다

실행 정보

- academic: 모델 sonnet, 독립 실행 예
- community-lead: 모델 haiku, 독립 실행 예
- industry-dev: 모델 opus, 독립 실행 예
- verifier: 모델 opus, 독립 실행 예

경고

- industry-dev runs[1].items.code-completeness: claim-not-verified 상한 4을 넘는 6점 → 4
