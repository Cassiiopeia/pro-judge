# 업데이트와 제거

## 업데이트

::: code-group

```bash [npx skills]
npx skills update                                  # 바뀐 skill만 다시 받는다
npx skills add Cassiiopeia/pro-judge#v0.3.1        # 특정 릴리스로 고정
```

```text [Claude Code 플러그인]
/plugin marketplace update pro-judge
```

:::

릴리스마다 `v<버전>` 태그와 [CHANGELOG](https://github.com/Cassiiopeia/pro-judge/blob/main/CHANGELOG.md)가 남는다.
[Releases](https://github.com/Cassiiopeia/pro-judge/releases)를 Watch하면 새 버전 알림을 받는다.

## 제거

::: code-group

```bash [npx skills]
npx skills remove using-pro-judge pro-judge-setup pro-judge-gather pro-judge-ideas pro-judge-score pro-judge-grill
```

```text [Claude Code 플러그인]
/plugin uninstall pro-judge@pro-judge
```

:::

대회 자료(`docs/pro-judge/`)는 지워지지 않는다.
