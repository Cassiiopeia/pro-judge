---
layout: home

hero:
  name: pro-judge
  text: 내기 전에, 그 대회 심사위원에게 먼저
  image:
    src: /assets/report-mobile.png
    alt: pro-judge 채점 보고서 모바일 화면
  tagline: 공고와 심사기준을 주면 에이전트가 심사위원이 되어 내 자료를 채점하고, 어디를 고치면 몇 점이 오르는지 순서대로 알려 준다.
  actions:
    - theme: brand
      text: 시작하기
      link: /guide/getting-started
    - theme: alt
      text: 실제 보고서 보기
      link: /guide/reading-report
    - theme: alt
      text: GitHub
      link: https://github.com/Cassiiopeia/pro-judge

features:
  - title: 점수표부터 만든다
    details: 한 줄짜리 심사기준도 판정 질문·0/5/10점 기준 문장·상한 규칙으로 펼친다. 공고에 없는 규칙은 "추정"으로 표시한다.
  - title: 심사위원마다 따로 채점
    details: 대회 구성에 맞춘 심사위원 페르소나가 서로의 점수를 보지 않고 매긴다. 의견이 크게 갈린 항목은 경보로 알린다.
  - title: 규칙은 코드로 강제
    details: 7점 이상은 자료에서 그대로 옮긴 인용이 있어야 한다. 자료에 없는 인용은 지운다. 같은 채점 원자료를 넣으면 늘 같은 숫자가 나온다.
  - title: 할 일을 점수로
    details: "\"커뮤니티 항목을 다음 기준까지 올리면 +8점, 그 기준 문장은 이것\" — 고칠 것을 오르는 점수 순으로 보여 준다."
  - title: 못 본 것도 남긴다
    details: 채점 전에 자료를 모으고 빠진 근거를 웹에서 찾거나 하나씩 묻는다. 끝까지 비는 칸은 보고서에 그대로 드러난다.
  - title: 실제 수상 결과로 검증
    details: 2025 오픈소스 개발자대회에서 수상팀이 미수상팀보다 높게 나온 쌍 36쌍 중 29쌍. 맞히지 못한 결과도 공개한다.
---

<div class="vp-doc" style="max-width: 960px; margin: 48px auto 0; padding: 0 24px;">

## 이런 보고서가 나온다

![채점 보고서 — 총점, 항목별 막대, 고칠 것 순위](/assets/report-desktop.png)

이 레포를 「제10회 공개SW 개발자대회」 심사기준으로 채점한 실제 결과다. <a href="/pro-judge/examples/공개SW-개발자대회/runs/20261008-0957_score/report.html" target="_blank">전체 보고서 열기 →</a>

## 설치는 한 줄

```bash
npx skills add Cassiiopeia/pro-judge
```

Claude Code·Codex·Cursor 등에서 쓴다. Claude Code 플러그인 설치와 차이는 [시작하기](/guide/getting-started)에 있다.

</div>
