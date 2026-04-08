# my-novel - AI 辅助小说写作 Skill

把小说创作拆解为结构化的工作流：**概念 → 设定 → 大纲 → 写作 → 归档**。

每个层级有明确的输入输出，AI 在每一层发挥不同作用。灵感归灵感，结构归结构。

## 快速开始

### 安装

```powershell
# Windows (WorkBuddy)
.\install.ps1

# Windows (Claude Code)
.\install.ps1 claude

# Linux/macOS
./install.sh workbuddy
```

### 第一次使用

1. 告诉 AI："帮我初始化一个小说项目"
2. AI 会引导你填写书名、类型、卷数等信息
3. 初始化完成后，按 AI 的建议进入下一步

## 工作流概览

| 命令 | 用途 | 示例 |
|------|------|------|
| `init` | 初始化小说项目 | "新建一个玄幻小说项目" |
| `propose` | 创建创作意图 | "给第一章写个提案" |
| `volume` | 管理卷结构 | "查看所有卷的状态" |
| `outline` | 编辑大纲 | "写第一卷前5章的章节大纲" |
| `write` | 写正文 | "开始写第1章" |
| `archive` | 定稿归档 | "第1章写完了，归档" |
| `status` | 查看进度 | "写到哪了" |

## 项目结构

```
你的小说项目/
  story.json          # 核心配置
  SPECS/              # 设定库（人物、世界观）
  OUTLINE/            # 大纲（总纲 → 卷纲 → 章纲）
  CONTENT/            # 正文（按卷/章节组织）
  ARCHIVE/            # 归档（定稿 + 变更记录）
```

## 设计理念

参考 OpenSpec 的软件工程实践（proposal → specs → design → tasks → implement → archive），将小说创作映射为类似的分层流程：

- **概念**（proposal）→ 故事概要 / 核心主题
- **设定**（specs）→ 人物、世界观、元设定
- **大纲**（design）→ 总纲 → 卷纲 → 章节大纲
- **正文**（implement）→ 按卷/章节组织的正文
- **归档**（archive）→ 定稿 + 变更记录

## 核心文件

```
my-novel-skill/
  SKILL.md      # Skill 定义（AI 读取）
  story.py      # CLI 入口
  src/          # CLI 模块（init/propose/volume/outline/write/archive/status）
  install.ps1   # Windows 安装脚本
  install.sh    # Linux/macOS 安装脚本
```

## 许可

MIT
