---
name: skill-finder
description: "You MUST use this when the user asks to find, discover, search, or compare skills, tools, or open-source projects on GitHub. Triggered by: 帮我找一个XX的skill, GitHub上有什么好用的XX, 搜索XX项目, 比较这些工具, 推荐几个XX方面的skill, 有没有XX相关的skill, find a skill for XX, search GitHub for XX, what are the best tools for XX, compare these projects, any request to discover or evaluate GitHub-hosted skills/tools. Searches GitHub (gh CLI + code search) and the web (Exa) in parallel, scores candidates with weighted multi-factor scoring (matching ×0.6 + stars ×0.25 + activity ×0.15), then generates a structured comparison report with introductions, pros/cons, usage examples, feature matrix, quadrant chart, and scenario-based recommendations. Also triggered when the user provides a specific list of projects/skills to compare."
---

# Skill Finder -- GitHub 技能发现与对比报告

## 概述

当用户要寻找、发现、比较 GitHub 上的技能(Skill)、工具或开源项目时，
你必须执行以下强制性流水线。这不是建议 -- 即使用户只是模糊地说
"看看有没有"，也必须走完整流程。

**进度反馈**：每步开始和结束时必须输出状态：

```
🔍 [1/6] 需求翻译中...
✅ [1/6] 完成
🔍 [2/6] 四路并行搜索中...
✅ [2/6] 完成（找到 N 个候选）
...
```

**快速模式 vs 完整模式**：
根据用户意图自动选择流程深度：

| 触发模式 | 用户话术特征 | 流程 |
|---------|-------------|------|
| **完整模式** | "帮我找XX"、"搜索XX"、"对比XX"、"推荐几个" | 全部 6 步 |
| **快速模式** | "有没有XX"、"XX是什么"、"XX能用吗"、"XX有啥" | 跳过深度获取（第四步），跳过 HTML 输出（第六步），只输出终端 + MD |

快速模式的确认卡片加一行：`⚡ 快速模式 — 将跳过深度分析和 HTML 报告`

---

## 流水线

- [ ] 1. 需求翻译与确认
- [ ] 2. 四路并行搜索
- [ ] 3. 加权筛选
- [ ] 4. 深度获取 (top 5-8)
- [ ] 5. 报告生成
- [ ] 6. 三输出 (终端 + MD + HTML)

---

### 第一步：需求翻译与确认

当用户给出模糊/非技术性描述时，先翻译为技术表述，生成中英文关键词，
然后**必须出示确认卡片并等待用户确认**，不可跳过。

**确认卡片模板：**

```
📋 需求理解
用户原话："[原始描述]"
翻译为："[技术表述]"
📌 关键推断（请确认）：
- [推断1]
- [推断2]
- [推断3]
🔍 搜索关键词：
  中文：[A]、[B]、[C]
  英文：[X]、[Y]、[Z]
确认？(Y/N 或请修正)
```

翻译规则：
- 非技术词转技术词 (如"写代码帮手" -> "AI coding assistant / copilot")
- 宽泛需求加限定 (如"好用的工具" -> 追问场景后加 "CLI tool / VS Code extension")
- 始终产出 3-5 个中文关键词 + 3-5 个英文关键词
- 用户需求少于 5 字时，必须追问补充细节后重新确认

用户确认后才进入第二步。

---

### 第二步：四路并行搜索

**必须在同一回合内并行发起以下四路搜索**（缺一不可）：

#### 🔵 路 A：GitHub Repos 搜索

```bash
gh search repos "<英文关键词1> <英文关键词2>" --sort stars --limit 15 --json name,fullName,url,description,stargazersCount,forksCount,language,updatedAt,topics
```

如果英文关键词有多组，每组搜一次。合并所有结果。

#### 🟢 路 B：GitHub Code 搜索

```bash
gh search code "SKILL.md <关键词1>" --extension md --limit 10 --json repository,path
```

再加一组不带 SKILL.md 的宽泛 code 搜索：

```bash
gh search code "<关键词1> in:readme" --limit 5 --json repository,path
```

#### 🟡 路 C：Web 搜索 A

```
mcp__exa__web_search_exa query="github best <type> <need> 2025 2026"
```

#### 🟠 路 D：Web 搜索 B

```
mcp__exa__web_search_exa query="<need> claude code skill github"
```

**结果合并与去重：**
- 按 `fullName` 去重（同仓库多条命中只保留一条）
- 合并为统一候选列表，最多保留 15 个
- 如果候选不足 3 个，用英文宽泛关键词再加搜一轮
- 如果候选超过 15 个，截断取 top 15 并在报告中标注总数

**gh CLI 不可用时的降级：**
所有 gh 搜索路替换为 `mcp__exa__web_search_exa` 加倍搜索：
- `"github <keywords> stars"`
- `"github awesome <topic>"`
- `"<keywords> github repo best"`
并在最终报告中标注"数据来源：仅 Web 搜索（gh CLI 不可用）"。

---

### 第三步：加权筛选

对每个候选按三个维度打分（1-5 整数），计算综合分：

**维度定义：**

| 维度 | 5 | 4 | 3 | 2 | 1 |
|------|---|---|---|---|---|
| **匹配度** | 直接命中，README 明确列出 | 核心相关，功能对得上 | 部分相关，需插件/配置 | 仅概念相关 | 不相关 |
| **活跃度** | 最近 1 个月有更新 | 最近 3 个月 | 最近 6 个月 | 6-12 个月 | >1 年或已归档 |
| **星标分** | >= 10K stars | 1K - 9.9K | 100 - 999 | 10 - 99 | < 10 |

**综合分计算公式：**

```
综合分 = 匹配度 × 0.6 + 星标分 × 0.25 + 活跃度 × 0.15
```

**筛选规则：**
- 匹配度 < 3 的项目直接丢弃（不进入后续步骤）
- 按综合分降序排序
- 前 5-8 名进入第四步深度获取
- 如果所有项目匹配度 < 3，如实告知用户"未找到高匹配项目"，列出最接近的 3-5 个

---

### 第四步：深度获取

对筛选后的 top 5-8 个项目，**并行获取以下信息**：

**4.1 README 内容：**
```
mcp__exa__web_fetch_exa urls=["https://github.com/<owner>/<repo>"] maxCharacters=3000
```
如果 README 获取失败，用 repo description + topics 替代。

**4.2 仓库元数据：**
```bash
gh repo view <owner/repo> --json name,description,stargazersCount,forksCount,openIssues,licenseInfo,createdAt,updatedAt,latestRelease
```
如果 gh 不可用，改用 `mcp__exa__web_fetch_exa` 获取 GitHub API 返回的 JSON：
```
https://api.github.com/repos/<owner>/<repo>
```

**4.3 最近 Issues（取最近 5 条）：**
```bash
gh issue list --repo <owner/repo> --limit 5 --json title,state,createdAt,labels
```
这用于发现已知问题，作为"缺点"的证据来源。

**4.4 SKILL.md（如存在）：**
```bash
gh api repos/<owner>/<repo>/contents/SKILL.md --jq .content 2>/dev/null | base64 -d 2>/dev/null
```
如果失败则跳过 -- 不是所有项目都是 skill。

**证据原则：**
报告中每一条优点(✅)和缺点(❌)都必须有可验证的来源：
- README 中列出的功能特性
- Issues 中的已知限制/bug
- 提交记录中的活跃度
- 仓库 description/topics 的官方说明

严禁凭空编造优缺点。

---

### 第五步：报告生成

按以下结构生成完整报告。**必须包含每一节，不得省略。**

#### 报告结构

```
# 🔍 Skill Finder -- 技能搜索对比报告

> **搜索需求**：[用户原始描述]
> **技术翻译**：[技术表述]
> **搜索关键词**：中文: A,B,C / 英文: X,Y,Z
> **搜索时间**：[当前日期]
> **数据来源**：GitHub API + Web Search / 仅 Web Search
> **候选数量**：[总数] 个，经筛选展示 [N] 个

---

## 📊 加权排名表

| # | 项目 | ⭐ Stars | 匹配度 | 活跃度 | 综合分 | 象限 |
|---|------|---------|--------|--------|--------|------|
| 1 | [name](url) | 1.2K | 5 | 4 | 4.35 | ⭐热门精准 |
| ...（按综合分降序）| ... | ... | ... | ... | ... | ... |

> 综合分 = 匹配度×0.6 + 星标分×0.25 + 活跃度×0.15

---

## 📈 双轴象限图

\`\`\`
           高 Stars
             │
   🔥热门但偏  │  ⭐热门精准
   (匹配<3.5) │  (匹配≥3.5)
             │
  ───────────┼─────────── 匹配度 ──→
             │
     淘汰     │  💎冷门精品
   (匹配<3.5) │  (匹配≥3.5)
             │
           低 Stars
\`\`\`

> 各项目按 (匹配度, 星标分) 坐标标注。象限分界线：匹配度=3.5, 星标分=3 (1000 stars)。

---

## 📋 逐个详评

### 1. [项目名称]

**仓库地址**：[url]
**Stars**：[N] | **Forks**：[N] | **许可证**：[license]
**最后更新**：[日期] | **维护状态**：🟢活跃 / 🟡低活跃 / 🔴已归档

#### 📖 介绍
[2-3 段：项目背景、核心功能介绍、设计理念和目标用户。基于 README 和仓库描述，不用编造。]

#### ✅ 优点
- [具体优点 1 -- 有出处]
- [具体优点 2 -- 有出处]
- [具体优点 3 -- 有出处，至少 3 条]

#### ❌ 缺点
- [具体缺点 1 -- 有出处，如 open issue、长期未更新、功能缺失等]
- [至少 1 条，最多 3 条。如果项目确实优秀，可只说 1 条轻微不足]

#### 📖 用法
\`\`\`bash
# 安装
[实际可运行的命令]

# 基本使用
[实际可运行的命令]
\`\`\`

---
### 2. [项目名称]
[重复以上结构，每个项目都必须有完整的 介绍/优点/缺点/用法 四部分]
---

## ⚖️ 功能矩阵

| 功能特性 | [项目1] | [项目2] | [项目3] |
|----------|---------|---------|---------|
| [核心功能 A] | ✅ | ✅ | ❌ |
| [核心功能 B] | ❌ | ✅ | ✅ |
| [核心功能 C] | ✅ | ⚠️ | ❌ |
| [核心功能 D] | ✅ | ❌ | ✅ |

> ✅ = 原生支持  ❌ = 不支持  ⚠️ = 部分支持/需插件/需配置

---

## 🎯 场景推荐

**🏆 综合最佳推荐：[项目名称]**
[2-3 句推荐理由，结合用户需求说明为什么选它]

**💎 冷门精品：[项目名称]**
[如果有 stars < 100 但匹配度 >= 4 的项目，在此提及]

| 使用场景 | 推荐项目 | 理由 |
|----------|----------|------|
| [场景 A] | [项目 X] | [一句话理由] |
| [场景 B] | [项目 Y] | [一句话理由] |
| [场景 C] | [项目 Z] | [一句话理由] |

---

## 💡 最终建议

[2-3 句总结性建议，帮助用户做决策。语言简洁有力，不要重复已有内容。]
```

---

### 第六步：三输出

**必须同时生成三种输出：**

#### 输出 1：终端展示（对话中直接输出）

终端版本使用 Unicode 框线字符绘制，控制在 40 行以内：

```
┌─────────────────────────────────────────────────────┐
│ 📊 加权排名                 共 [N] 个候选，展示 [M] 个    │
├────┬──────────────────────┬────────┬────┬────┬──────┤
│  # │ 项目                  │ ⭐ Stars │ 匹配 │ 活跃 │ 综合  │
├────┼──────────────────────┼────────┼────┼────┼──────┤
│ 🥇 │ [name](url)           │  25K   │  5  │  5  │ 5.00 │
│ 🥈 │ [name](url)           │  1.2K  │  5  │  4  │ 3.85 │
│ 🥉 │ [name](url)           │   800  │  4  │  4  │ 3.40 │
│  4 │ [name](url)           │   新   │  5  │  5  │ 4.10 │
└────┴──────────────────────┴────────┴────┴────┴──────┘

📈 象限分布
  高 Stars
   │  🔥热门但偏：[项目列表]
   │  ⭐热门精准：[项目列表]
  ─┼────────────────── 匹配度 →
   │  淘汰：[如有]
   │  💎冷门精品：[项目列表]
  低 Stars

🎯 推荐
🏆 最佳：[项目名] — [理由]
💎 冷门精品：[项目名] — [理由]

| 场景 | 推荐 | 理由 |
|------|------|------|
| ... | ... | ... |

💡 [2-3句最终建议]
```

Stars < 10 显示"新"，≥ 10 用原始数字。前三名用 🥇🥈🥉 标记。

#### 输出 2：Markdown 文件

将完整报告保存到当前工作目录：

```
skill-finder-report-<topic_slug>.md
```

其中 `<topic_slug>` 是搜索关键词的英文 slug（小写，连字符分隔）。
如果同名文件已存在，追加序号：`skill-finder-report-<topic_slug>-2.md`。

#### 输出 3：HTML 文件

1. 用 Read 工具读取 `assets/report.html` 获取 HTML 模板
2. 将报告数据填入模板（替换以下占位符，注意所有用户文本先做 HTML 转义：`&` → `&amp;`，`<` → `&lt;`，`>` → `&gt;`）：

| 占位符 | 替换内容 |
|--------|---------|
| `{{SEARCH_QUERY}}` | 用户原始搜索需求（已转义） |
| `{{SEARCH_DATE}}` | 当前日期 |
| `{{CANDIDATE_COUNT}}` | 候选数量 |
| `{{RANKING_TABLE_ROWS}}` | 排名表完整 `<tr>` 行（每行 7 个 `<td>`：序号、项目链接、Stars、匹配度、活跃度、综合分、象限标签） |
| `{{QUADRANT_STAR}}` | ⭐热门精准象限内的项目标签 HTML |
| `{{QUADRANT_HOT_BIAS}}` | 🔥热门但偏象限内的项目标签 HTML |
| `{{QUADRANT_COLD_GEM}}` | 💎冷门精品象限内的项目标签 HTML |
| `{{QUADRANT_ELIMINATE}}` | 淘汰象限内的项目标签 HTML（可为空） |
| `{{FEATURE_MATRIX}}` | 完整功能矩阵 `<table class="matrix-table">...</table>` |
| `{{RECOMMENDATIONS}}` | 推荐卡片 `<div class="rec-cards">...</div>` |
| `{{DETAILED_REVIEWS}}` | 每个项目的 `<div class="review-item"><details>...</details></div>` |

3. 象限项目标签格式：`<span class="q-tag q-tag-star">项目名</span>`（star/hot-bias/cold-gem/eliminate）
4. 用 Write 工具保存为 `skill-finder-report-<topic_slug>.html`
5. 该模板纯 HTML + 内联 CSS，零外部依赖，双击即可在浏览器中查看

---

## 边界处理

以下场景必须按指定方式处理，不得自由发挥：

| 场景 | 处理方式 |
|------|----------|
| `gh` CLI 不可用 | 全部降级为 Web 搜索（加倍搜索量），报告中标注"仅 Web 搜索结果" |
| 搜索结果 < 3 个 | 用英文宽泛关键词再搜一轮；仍不足则在报告中说明覆盖不足 |
| 搜索结果 > 15 个 | 截断保留 top 15，报告中标注"共找到 [N] 个，展示 top 15" |
| 所有匹配度 < 3 | 如实告知，列出最接近的 3-5 个并说明差距 |
| API 限流 (429) | 等待 60 秒重试 1 次；仍失败则切纯 Web 搜索 |
| README 获取失败 | 使用 description + topics 字段替代 |
| 重复仓库 | fullName 去重，保留 stars 最高的那条 |
| 用户需求 < 5 字 | 不进入流水线，先请求用户补充更多细节 |
| 用户提供具体列表 | 跳过第一、二步，直接从第三步评分开始 |

---

## 工具依赖

| 优先级 | 工具 | 用途 |
|--------|------|------|
| 1 | `gh` CLI | 仓库搜索、元数据、Issue、SKILL.md 内容 |
| 2 | `mcp__exa__web_search_exa` | Web 搜索、gh 不可用时的降级方案 |
| 3 | `mcp__exa__web_fetch_exa` | README 全文获取、仓库页面抓取 |
| 4 | `assets/report.html` | HTML 报告模板（本地文件，用 Read 工具读取） |

---

## 约束

- [ ] **MUST** 在开始搜索前先确认需求（出示卡片 + 等待确认）
- [ ] **MUST** 四路并行搜索，不得串行
- [ ] **MUST** 用加权公式计算综合分，不得凭感觉排序
- [ ] **MUST** 每条优缺点都要有可验证出处
- [ ] **MUST** 同时生成终端输出 + MD 文件 + HTML 文件
- [ ] **MUST NOT** 跳过确认卡片直接搜索
- [ ] **MUST NOT** 编造 README 中未提及的功能
- [ ] **MUST NOT** 只输出一种格式就结束
- [ ] **MUST NOT** 对匹配度 < 3 的项目深度分析
