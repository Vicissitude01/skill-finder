# Skill Finder

A [Superpowers](https://github.com/obra/superpowers)-compatible skill that translates your natural-language needs into structured GitHub searches, then generates weighted comparison reports with introductions, pros/cons, usage guides, feature matrices, and visual quadrant charts.

## What It Does

Describe what you need in plain language, and this skill will:

1. **Translate** your non-technical description into precise technical terms and bilingual search keywords
2. **Search** GitHub via 4 parallel channels (gh CLI repos + code + dual web searches)
3. **Score** candidates with weighted multi-factor scoring (match ×0.6 + stars ×0.25 + activity ×0.15)
4. **Generate** a structured comparison report with:
   - Weighted ranking table
   - 2D quadrant chart (relevance vs popularity)
   - Individual deep-dives (intro, pros, cons, usage)
   - Feature comparison matrix
   - Scenario-based recommendations
5. **Output** in three formats: terminal summary + Markdown file + styled HTML report

## Pipeline

```
需求翻译确认 → 四路并行搜索 → 加权筛选 → 深度获取 → 报告生成 → 三输出
```

## Output Examples

- **Terminal**: Compact ranking table + quadrant chart + top picks
- **Markdown**: Full structured report saved to `skill-finder-report-<topic>.md`
- **HTML**: Styled responsive report saved to `skill-finder-report-<topic>.html`

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/skill-finder.git
cp -r skill-finder/ ~/.claude/skills/skill-finder/
```

Or via Claude Code plugin marketplace:

```bash
/plugin marketplace add YOUR_MARKETPLACE
/plugin install skill-finder@YOUR_MARKETPLACE
```

## Dependencies

| Priority | Tool | Purpose |
|----------|------|---------|
| 1 | `gh` CLI | GitHub repo/code search, metadata, issues |
| 2 | Exa (web search) | Supplementary web search, fallback when gh unavailable |
| 3 | Exa (web fetch) | README content fetching |

## Trigger Phrases

- "帮我找一个可以XX的skill"
- "GitHub上有什么好用的XX工具"
- "比较一下这几个项目"
- "推荐几个XX方面的开源工具"
- "find a skill for XX"
- "search GitHub for XX"

## Skill Structure

```
skill-finder/
├── SKILL.md                    # Core skill (6-step pipeline)
├── README.md
├── LICENSE                     # MIT
├── assets/
│   └── report.html             # HTML report template (inline CSS, zero deps)
├── references/
│   └── report_template.md      # Report structure reference
└── scripts/
    └── search_github.py        # GitHub search + scoring helper
```

## License

MIT
