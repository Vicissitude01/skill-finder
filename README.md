# Skill Finder

> 我用自然语言描述需求，它帮我在 GitHub 上找到最匹配的工具，并告诉我该选哪个。

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Superpowers](https://img.shields.io/badge/Superpowers-compatible-orange)](https://github.com/obra/superpowers)

一个 [Superpowers](https://github.com/obra/superpowers) 兼容的 Claude Code 技能。只需用自然语言描述需求，它自动搜索 GitHub、加权打分、生成三格式对比报告，帮你快速决定该用哪个开源项目。

---

## 演示

**输入**：`帮我找一个可以在终端里渲染 Markdown 的工具`

**确认卡片**：

```
📋 需求理解
用户原话："帮我找一个可以在终端里渲染 Markdown 的工具"
翻译为："Terminal Markdown 渲染器 / 查看器（CLI 工具，支持 TUI 或 stdout 输出）"

📌 关键推断：
- 终端 CLI 工具，非 VS Code 插件
- 支持代码高亮 + 表格 + 图片（可选）
- 轻量优先，开箱即用

🔍 搜索关键词：
  中文：终端 Markdown 渲染、CLI 文档查看器、命令行 Markdown
  英文：terminal markdown renderer、cli markdown viewer、md cat cli

确认？
```

**输出**：

```
┌─────────────────────────────────────────────────────┐
│ 📊 加权排名                    共 6 个候选，展示 5 个    │
├────┬────────────────┬────────┬────┬────┬──────┤
│  # │ 项目            │ ⭐ Stars │ 匹配 │ 活跃 │ 综合  │
├────┼────────────────┼────────┼────┼────┼──────┤
│ 🥇 │ glow           │  25K   │  5  │  5  │ 5.00 │
│ 🥈 │ mdcat-ng       │  新    │  5  │  4  │ 3.85 │
│ 🥉 │ markless       │  新    │  5  │  5  │ 4.10 │
│  4 │ mdink          │  新    │  4  │  3  │ 3.10 │
│  5 │ liham          │  新    │  5  │  4  │ 3.85 │
└────┴────────────────┴────────┴────┴────┴──────┘

🎯 推荐
🏆 最佳：glow — 25K Stars，社区最成熟，开箱即用
💎 冷门精品：markless — Mermaid 图表 + 内置编辑器 + 文件监听
```

同时生成 `skill-finder-report-terminal-markdown-renderer.md` 和 `.html`。

---

## 六步流水线

```
需求翻译与确认 → 四路并行搜索 → 加权筛选 → 深度获取 → 报告生成 → 三输出
```

### 第一步：需求翻译
用户即使用非专业术语描述（如"写代码帮手"），skill 会自动翻译为技术关键词（"AI coding assistant / copilot"），生成中英双语搜索词，并出示确认卡片等待你的确认。少于 5 个字的模糊描述会自动追问。

### 第二步：四路并行搜索
在同一回合发起 GitHub Repos + GitHub Code + Web 搜索 A + Web 搜索 B，去重合并后最多 15 个候选。

### 第三步：加权筛选

| 维度 | 权重 | 评分标准 |
|------|------|---------|
| 匹配度 | 60% | 5=直接命中 / 4=核心相关 / 3=部分相关 / 2=概念相关 / 1=不相关 |
| 星标分 | 25% | 5≥10K / 4≥1K / 3≥100 / 2≥10 / 1<10 |
| 活跃度 | 15% | 5=近1月 / 4=近3月 / 3=近6月 / 2=近12月 / 1=>1年 |

```
综合分 = 匹配度 × 0.6 + 星标分 × 0.25 + 活跃度 × 0.15
```

匹配度 < 3 直接淘汰。同义词引擎（如 `cli` ↔ `command-line`）减少漏判。

### 第四步：深度获取
对 top 5-8 并行获取：README、仓库元数据、最近 Issues、SKILL.md（如存在）。每条优缺点都有可验证出处。

### 第五步：报告生成
完整 Markdown 报告：排名表 + ASCII 象限图 + 逐个详评 + 功能矩阵 + 场景推荐。

### 第六步：三输出

| 输出 | 格式 | 用途 |
|------|------|------|
| 终端 | Unicode 框线表格 + 象限图 + 推荐 | 即时决策 |
| `.md` 文件 | 完整结构化报告 | 存档、分享 |
| `.html` 文件 | 响应式 UI 报告（内联 CSS） | 浏览器查看 |

---

## 快速模式 vs 完整模式

| 你说 | 流程 |
|------|------|
| "帮我找XX"、"搜索XX"、"对比XX" | 完整 6 步（含深度分析和 HTML） |
| "有没有XX"、"XX是什么"、"XX能用吗" | 快速模式（跳过深度获取和 HTML） |

---

## 安装

```bash
# 克隆
git clone https://github.com/<your-username>/skill-finder.git

# 安装为 Claude Code Skill
cp -r skill-finder ~/.claude/skills/skill-finder/
```

或通过插件市场：

```bash
/plugin marketplace add <marketplace-url>
/plugin install skill-finder@<marketplace>
```

## 依赖

| 优先级 | 工具 | 用途 | 必需 |
|--------|------|------|------|
| 1 | `gh` CLI | GitHub 搜索、元数据、Issues | 推荐 |
| 2 | Exa MCP | Web 搜索 + README 获取 | 是 |

`gh` 不可用时自动降级为纯 Web 搜索。

---

## 触发词

### 中文
- 帮我找一个可以 XX 的 skill
- GitHub 上有什么好用的 XX 工具
- 比较一下这几个项目
- 推荐几个 XX 方面的开源工具

### English
- find a skill for XX
- search GitHub for XX
- what are the best tools for XX
- compare these projects

---

## 边界处理

| 场景 | 行为 |
|------|------|
| `gh` 未安装 | 降级纯 Web 搜索，报告中标注 |
| 结果 < 3 个 | 英文关键词扩搜 |
| 结果 > 15 个 | 截断取 top 15 |
| 所有匹配度 < 3 | 如实告知，列最接近的 |
| API 限流 (429) | 等待 60 秒重试，失败则切 Web |
| README 获取失败 | 用 description + topics 替代 |
| 需求 < 5 字 | 追问补充细节 |
| 用户提供具体列表 | 跳过搜索，直接评分对比 |

---

## 文件结构

```
skill-finder/
├── SKILL.md                      核心技能定义（433 行）
├── README.md
├── LICENSE                       MIT
├── assets/
│   └── report.html               HTML 报告模板（内联 CSS，零依赖）
├── references/
│   └── report_template.md        报告结构与字段指南
└── scripts/
    └── search_github.py          GitHub 搜索 + 同义词评分 + 去重
```

---

## 常见问题

**Q: 和直接 `gh search` 有什么区别？**
A: `gh search` 只按 stars 排序。skill-finder 会翻译你的非技术描述、加权多维评分、深度获取每个项目的优缺点、给出场景化推荐。它是一个"搜索 + 分析 + 建议"的完整决策工具。

**Q: 评分权重能改吗？**
A: 当前默认 60/25/15。未来版本支持用户在确认卡片中指定偏好（如"我更看重活跃度"）动态调整。

**Q: 能搜 Gitee / GitLab 吗？**
A: 当前仅支持 GitHub。多平台搜索在规划中。

**Q: 生成的 HTML 报告需要网络吗？**
A: 不需要。纯 HTML + 内联 CSS，双击即看。

---

## 贡献

基于 [Superpowers](https://github.com/obra/superpowers) 技能规范构建。欢迎提 Issue 和 PR。

## 许可

MIT
