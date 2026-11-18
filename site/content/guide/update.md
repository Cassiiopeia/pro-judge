# 업데이트와 제거

## 업데이트

::: code-group

```bash [npx skills]
npx skills update                                  # 바뀐 skill만 다시 받는다
npx skills add Cassiiopeia/pro-judge#v2.1.0        # 특정 릴리스로 고정
```

```text [Claude Code 플러그인]
/plugin marketplace update pro-judge
```

:::

::: warning v2.0.0 — 이전 버전과 호환되지 않음
skill 6개가 `pj-prepare`·`pj-score`·`pj-qna` 3개로 합쳐졌다. npx skills로 설치했다면 옛 skill을 지우고 다시 설치한다.

```bash
npx skills remove using-pro-judge pro-judge-setup pro-judge-gather pro-judge-ideas pro-judge-score pro-judge-grill
npx skills add Cassiiopeia/pro-judge
```

질의응답 결과 폴더는 `runs/*_qna`로 바뀌었다. 이전 버전의 `runs/*_grill` 결과는 보고서·대시보드에서 읽지 않는다.
:::

릴리스마다 `v<버전>` 태그와 [CHANGELOG](https://github.com/Cassiiopeia/pro-judge/blob/main/CHANGELOG.md)가 남는다.
[Releases](https://github.com/Cassiiopeia/pro-judge/releases)를 Watch하면 새 버전 알림을 받는다.

## 제거

::: code-group

```bash [npx skills]
npx skills remove pj-prepare pj-score pj-qna
```

```text [Claude Code 플러그인]
/plugin uninstall pro-judge@pro-judge
```

:::

대회 자료(`docs/pro-judge/`)는 지워지지 않는다.
