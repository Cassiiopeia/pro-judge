# 근거 장부 evidence.yaml

검사: `python3 $SKILL/shared/scripts/evidence.py check <evidence.yaml> [--rubric <rubric.yaml>]`

```yaml
scope: target            # target(채점 대상) | contest(대회 정보)
subject: "팀 저장소 (2026-10-08)"
sources:
  - id: s1
    kind: repo           # file | repo | url | web | user | video
    ref: "https://github.com/team/app"
    how: "repo_facts.py --since 2025-05-20 --until 2025-12-05"
    trust: self          # official(공고·주최) | reported(보도·제3자) | self(팀 자료) | user(사용자 진술)
    status: ok           # ok | partial | failed
    note: ""             # failed·partial이면 이유
evidence:
  - item: community-potential   # 대상 모드: 점수표 항목 id 또는 "*"(두루 쓰이는 사실). 대회 모드: 주제 id
    type: numbers               # numbers | proper-nouns | demo | field-test | quote | observation
    source: s1
    text: "대회 기간 커밋 52개, 작성자 3명"
absent:                         # 찾아봤지만 없다고 확인된 것 — 빈칸에서 빠지고 다시 묻지 않는다
  - item: demo
    type: demo
    source: s2
    text: "사용자: 시연 영상 없음"
```

## 대회 모드 주제 id

| id | 무엇 |
| --- | --- |
| `announcement` | 공고 원문 |
| `criteria` | 심사 항목·배점 |
| `schedule` | 일정 |
| `submission` | 제출물·분량·형식 요건 |
| `penalties` | 감점·실격·제외 규정 |
| `judges` | 심사위원·평가자 구성 |
| `past-winners` | 역대 수상작 |

## 규칙

- `status: failed`인 출처의 근거는 빈칸을 채우지 않는다
- 근거 `text`는 자료에 있는 사실 한 줄. 판단("완성도가 높다")이 아니라 관찰("핵심 기능 3개가 배포 주소에서 작동")
- 사용자 진술(`trust: user`)은 빈칸을 채우지만, 보고서에 진술이라고 표시된다
