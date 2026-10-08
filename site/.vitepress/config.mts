import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'
import { cpSync, existsSync } from 'node:fs'
import { join, resolve } from 'node:path'

// 문서 원본은 site/content/ 하나뿐이다. 저장소의 docs/ 는 로컬 산출물(git 제외)이라 쓰지 않는다.
// 예시 보고서(examples/)와 화면(assets/)은 저장소 원본 하나로 두고, 설정을 읽을 때 public/ 으로 복사한다.
// (빌드 끝에 복사하면 본문의 이미지 경로를 빌드가 못 찾아 실패한다. public/ 사본은 git에서 뺀다)
const REPO = resolve(__dirname, '../..')
const PUBLIC = resolve(__dirname, '../content/public')
for (const dir of ['examples', 'assets']) {
  const from = join(REPO, dir)
  if (existsSync(from)) cpSync(from, join(PUBLIC, dir), { recursive: true })
}
const GITHUB = 'https://github.com/Cassiiopeia/pro-judge'

// 흐름도는 mermaid 코드 블록으로 쓴다 — GitHub 이슈·보고서와 같은 문법
export default withMermaid(defineConfig({
  title: 'pro-judge',
  description: '대회에 내기 전에 그 대회의 심사위원에게 먼저 채점받는다',
  lang: 'ko',
  base: '/pro-judge/',
  srcDir: 'content',
  // public/ 사본의 보고서 md·rubric 등은 정적 파일일 뿐 문서 페이지가 아니다
  srcExclude: ['public/**'],
  cleanUrls: true,
  lastUpdated: false,
  // 저장소 파일(../README.md 등)을 가리키는 링크는 사이트 안에 없다
  ignoreDeadLinks: true,
  // 링크를 메신저·SNS에 붙였을 때 미리보기가 보이게 한다
  head: [
    ['meta', { name: 'theme-color', content: '#b4232a' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'pro-judge — 내기 전에, 그 대회 심사위원에게 먼저' }],
    ['meta', { property: 'og:description', content: '공고와 심사기준으로 심사위원을 만들어 내 자료를 채점하고, 어디를 고치면 몇 점이 오르는지 알려 주는 Agent Skills' }],
    ['meta', { property: 'og:image', content: 'https://cassiiopeia.github.io/pro-judge/assets/report-desktop.png' }],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
  ],
  sitemap: { hostname: 'https://cassiiopeia.github.io/pro-judge/' },
  themeConfig: {
    nav: [
      { text: '시작하기', link: '/guide/getting-started' },
      { text: '작동 방식', link: '/guide/how-it-works' },
      { text: '검증 결과', link: '/validation' },
      { text: '예시 보고서', link: '/guide/reading-report' },
      { text: '기여하기', link: `${GITHUB}/blob/main/CONTRIBUTING.md` },
    ],
    sidebar: [
      {
        text: '쓰기',
        items: [
          { text: '시작하기', link: '/guide/getting-started' },
          { text: '보고서 읽는 법', link: '/guide/reading-report' },
          { text: '업데이트와 제거', link: '/guide/update' },
        ],
      },
      {
        text: '이해하기',
        items: [
          { text: '작동 방식', link: '/guide/how-it-works' },
          { text: 'skill 6개', link: '/guide/skills' },
          { text: '비슷한 도구와의 차이', link: '/guide/compare' },
          { text: '검증 결과', link: '/validation' },
        ],
      },
    ],
    socialLinks: [{ icon: 'github', link: GITHUB }],
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '검색', buttonAriaLabel: '검색' },
          modal: {
            noResultsText: '결과가 없습니다',
            resetButtonTitle: '지우기',
            footer: { selectText: '선택', navigateText: '이동', closeText: '닫기' },
          },
        },
      },
    },
    outline: { level: [2, 3], label: '이 페이지 목차' },
    docFooter: { prev: '이전', next: '다음' },
    darkModeSwitchLabel: '테마',
    sidebarMenuLabel: '메뉴',
    returnToTopLabel: '맨 위로',
    footer: { message: 'Apache-2.0', copyright: 'Cassiiopeia' },
  },
}))
