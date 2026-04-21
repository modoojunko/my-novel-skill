# my-novel-skill 安装指南

## 前置要求

- Python 3.8 或更高版本
- 仅使用 Python 标准库，无需 pip 安装任何依赖

## 安装方式

### WorkBuddy

```bash
git clone <repository-url> my-novel-skill
cd my-novel-skill
mkdir -p ~/.workbuddy/skills/my-novel-skill
cp SKILL.md ~/.workbuddy/skills/my-novel-skill/
cp story.py ~/.workbuddy/skills/my-novel-skill/
cp -r src_v2 ~/.workbuddy/skills/my-novel-skill/src
cp -r docs ~/.workbuddy/skills/my-novel-skill/docs 2>/dev/null || true
```

### Claude Code

```bash
git clone <repository-url> my-novel-skill
cd my-novel-skill
mkdir -p ~/.claude/skills/my-novel-skill
cp SKILL.md ~/.claude/skills/my-novel-skill/
cp story.py ~/.claude/skills/my-novel-skill/
cp -r src_v2 ~/.claude/skills/my-novel-skill/src
cp -r docs ~/.claude/skills/my-novel-skill/docs 2>/dev/null || true
```

### Hermes Agent

```bash
git clone <repository-url> my-novel-skill
cd my-novel-skill
./install.sh hermes
```

或者使用提供的安装脚本：

**Linux/macOS:**
```bash
./install.sh hermes
```

**Windows (PowerShell):**
```powershell
.\install.ps1 -Platform hermes
```

安装完成后，你就可以直接使用`story`命令了，不需要完整路径！

## 快速开始

1. 创建一个新目录作为你的小说项目
2. 在该目录中运行：`python /path/to/story.py init`
3. 按照提示输入小说信息
4. 开始创作！

## 命令列表

```bash
story init              # 初始化新项目
story status            # 查看项目状态
story collect core      # 收集核心信息
story collect protagonist # 创建主角
story plan volume 1     # 规划第1卷
story plan chapter 1 1  # 规划第1卷第1章
story write 1 --prompt  # 生成第1章提示词
story archive 1         # 归档第1章
story export            # 导出小说
```

## 项目结构

```
你的小说项目/
├── story.yaml          # 配置文件
├── process/            # 过程管理产物
│   ├── INFO/           # 收集到的信息
│   ├── OUTLINE/        # 大纲草稿
│   ├── PROMPTS/        # 生成的提示词
│   └── TEMPLATES/      # 提示词模板
└── output/             # 最终正文
    ├── CONTENT/        # 小说正文
    ├── EXPORT/         # 导出文件
    └── ARCHIVE/        # 已归档章节
```

## 零依赖设计

my-novel-skill 仅使用 Python 标准库：
- `pathlib` - 路径操作
- `json` - JSON 读写（默认）
- `yaml` - 可选，如果安装了 PyYAML 则使用

如果没有安装 PyYAML，会自动降级到 JSON 格式，功能完全可用。
