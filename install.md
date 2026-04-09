# my-novel 安装指南

## 环境要求

- **Python 3.8+**（仅使用标准库，无需 pip install）
- 支持 Windows / macOS / Linux

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/modoojunko/my-novel-skill.git
cd my-novel-skill
```

### 2. 安装到 Agent 平台

技能支持三个平台，根据你使用的 Agent 选择对应命令：

#### WorkBuddy

```powershell
# Windows
.\install.ps1

# Linux/macOS
./install.sh workbuddy
```

安装路径：`~/.workbuddy/skills/my-novel/`

#### Claude Code

```powershell
# Windows
.\install.ps1 claude

# Linux/macOS
./install.sh claude
```

安装路径：`~/.claude/skills/my-novel/`

#### OpenClaw

```powershell
# Windows
.\install.ps1 openclaw

# Linux/macOS
./install.sh openclaw
```

安装路径：`~/.openclaw/skills/my-novel/`

### 3. 验证安装

安装脚本会复制以下文件到目标目录：

```
my-novel/
  SKILL.md      # 技能定义（Agent 读取）
  story.py      # CLI 入口
  src/          # CLI 模块
```

安装完成后，在小说项目目录下运行：

```bash
python ~/.workbuddy/skills/my-novel/story.py status
```

如果显示项目状态信息（或提示"未找到小说项目"），说明安装成功。

## 使用方式

安装后不需要额外配置。Agent 读取 SKILL.md 后会自动识别小说相关的请求。

### 基本用法

在任意目录下，告诉 Agent：

- "帮我初始化一个小说项目"
- "写第一章的大纲"
- "开始写正文"

Agent 会自动调用 `story.py` 的对应命令。

### 手动调用 CLI

如果你想在终端直接使用，进入小说项目目录后运行：

```bash
# Windows
python ~/.workbuddy/skills/my-novel/story.py <command> [options]

# Linux/macOS
python ~/.workbuddy/skills/my-novel/story.py <command> [options]
```

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `init <书名>` | 初始化小说项目 |
| `status` | 查看项目状态 |
| `plan --volume N` | 生成卷纲草稿 |
| `plan --chapters N` | 拆分章节 |
| `outline --draft N --all` | 批量生成细纲 |
| `write N --draft` | 写正文草稿 |
| `snapshot N` | 生成章节快照 |
| `recall N` | 回顾前 N 章 |
| `export` | 导出全文 |

## 卸载

删除对应的技能目录即可：

```bash
# WorkBuddy
rm -rf ~/.workbuddy/skills/my-novel/

# Claude Code
rm -rf ~/.claude/skills/my-novel/

# OpenClaw
rm -rf ~/.openclaw/skills/my-novel/
```

## 更新

重新运行安装脚本即可覆盖更新：

```bash
git pull
./install.ps1   # 或 ./install.sh workbuddy
```

> 注意：更新会清除目标目录后重新安装，不会影响你的小说项目数据（存储在 `stories/` 目录下）。
