# my-novel - AI 辅助小说写作项目指南

## 项目概述

my-novel 是一个 AI 辅助小说写作的结构化工作流工具，将小说创作拆解为：**概念 → 设定 → 大纲 → 写作 → 归档**五个清晰阶段。每个阶段有明确的输入输出，帮助作者建立规范的创作流程，避免结构崩坏。

**核心理念**：先结构后内容，先大纲后正文。参考软件工程实践，将小说创作标准化为可执行的工作流。

## 项目结构

```
my-novel-skill/
├── README.md              # 项目说明文档
├── SKILL.md               # AI 技能定义（详细工作流）
├── install.md             # 安装指南
├── install.ps1            # Windows 安装脚本
├── install.sh             # macOS/Linux 安装脚本
├── story.py               # CLI 入口文件
├── src/                   # 功能模块目录
│   ├── init.py            # 项目初始化
│   ├── propose.py         # 创作意图管理
│   ├── plan.py            # 卷纲生成与章节拆分
│   ├── define.py          # 设定库管理（人物/世界观）
│   ├── volume.py          # 卷管理
│   ├── outline.py         # 大纲编辑
│   ├── write.py           # 写作模式（生成 Agent Prompt）
│   ├── review.py          # 人机差异对比
│   ├── learn.py           # 风格学习引擎
│   ├── style.py           # 风格档案管理
│   ├── stats.py           # 学习进度统计
│   ├── update_specs.py    # 写作后更新设定
│   ├── recall.py          # 章节回顾
│   ├── snapshot.py        # 章节设定快照
│   ├── export.py          # 导出功能（txt/docx）
│   ├── archive.py         # 定稿归档
│   ├── status.py          # 项目状态查看
│   └── paths.py           # 路径管理
├── stories/               # 示例故事项目
├── test_define/           # 设定管理测试
├── test_novel/            # 小说创作测试
└── OpenSpec/              # 参考规范
```

## 核心功能模块

### 1. 项目初始化 (init)
- 创建标准化小说项目结构
- 交互式收集项目信息（书名、类型、字数、卷数等）
- 生成配置文件 `story.json` 和目录结构

### 2. 创作意图管理 (propose)
- 创建结构化创作意图文档
- 支持概念、卷、章节三个层级的提案
- 帮助明确写作方向和目标

### 3. 规划流水线 (plan)
- 卷纲生成：AI 辅助生成卷大纲（起承转合、核心事件、高潮设计）
- 章节拆分：将卷大纲拆分为具体章节列表
- 支持 "草稿 → 讨论 → 确认" 三阶段迭代

### 4. 设定库管理 (define)
- 人物设定：创建和管理详细的人物卡（含六层认知模型）
- 世界观设定：管理地理、历史、社会、魔法等设定
- 支持搜索和分类管理

### 5. 大纲编辑 (outline)
- 总纲、卷纲、章节大纲三级管理
- AI 辅助大纲生成和扩展
- 支持场景展开、章节交换等操作

### 6. 写作模式 (write)
- 生成结构化写作 Prompt（含人物设定、大纲、风格指南）
- 创建章节正文文件和任务清单
- 展示相关参考信息（上章回顾、人物设定、伏笔检查）

### 7. 人机差异对比 (review)
- 对比 AI 生成内容与用户修改的差异
- 统计修改率和高频替换词汇
- 分析写作质量和改进方向

### 8. 风格学习引擎 (learn)
- 从用户修改中提取写作风格模式
- 更新风格档案（词汇、句式、节奏偏好）
- 让 AI 输出更符合用户风格

### 9. 进度统计 (stats)
- 字数统计和目标进度追踪
- AI 学习进度和修改率趋势分析
- 可视化统计图表

### 10. 设定更新 (update-specs)
- 分析章节内容，自动更新角色设定
- 管理 POV 角色的认知状态（已知/未知信息）
- 支持状态快照和追踪

### 11. 章节回顾 (recall)
- 查看章节摘要和设定快照
- 支持连续章节回顾和最近章节查看
- 帮助保持剧情连贯性

### 12. 设定快照 (snapshot)
- 记录章节结束时的设定状态（人物心理、剧情进度、伏笔等）
- 为后续写作提供上下文参考
- 支持 AI 填充和查看功能

### 13. 导出功能 (export)
- 导出为 TXT 或 DOCX 格式
- 支持章节范围和卷级导出
- 自动格式化输出

### 14. 定稿归档 (archive)
- 章节完成后归档到 ARCHIVE 目录
- 保存完整上下文（正文、任务清单、大纲、变更记录）
- 更新项目进度和字数统计

### 15. 状态查看 (status)
- 展示项目整体进度和状态
- 包括字数、章节进度、设定库信息
- 提供下一步操作建议

## 安装与运行

### 环境要求
- Python 3.8+（仅使用标准库，无需额外依赖）
- 支持 Windows / macOS / Linux

### 安装方法

#### Windows (WorkBuddy)
```powershell
.\install.ps1
```

#### Windows (Claude Code)
```powershell
.\install.ps1 claude
```

#### macOS/Linux
```bash
./install.sh workbuddy  # WorkBuddy
./install.sh claude     # Claude Code
./install.sh openclaw   # OpenClaw
```

### 基本用法

1. **初始化项目**
   ```bash
   python story.py init
   ```

2. **查看状态**
   ```bash
   python story.py status
   ```

3. **生成卷纲**
   ```bash
   python story.py plan --volume 1
   ```

4. **批量生成细纲**
   ```bash
   python story.py outline --draft 1 --all
   ```

5. **AI 写正文**
   ```bash
   python story.py write 5 --draft
   ```

6. **导出小说**
   ```bash
   python story.py export 1-10 --format docx
   ```

## 工作流示例

### Pipeline 自动化流程
```bash
# 1. 初始化项目
python story.py init

# 2. 生成卷1大纲（AI 辅助）
python story.py plan --volume 1

# 3. 讨论修改卷纲
python story.py plan --volume 1 --revise

# 4. 确认卷纲定稿
python story.py plan --volume 1 --confirm

# 5. 拆分章节
python story.py plan --chapters 1

# 6. 批量生成章节细纲
python story.py outline --draft 1 --all

# 7. AI 写正文
python story.py write 5 --draft

# 8. 人机差异对比
python story.py review 5

# 9. 学习用户风格
python story.py learn 5

# 10. 更新设定
python story.py update-specs 5

# 11. 归档章节
python story.py archive 5
```

### 项目目录结构

```
你的小说项目/
├── story.json              # 核心配置文件
├── SPECS/                  # 设定库
│   ├── characters/         # 人物设定
│   ├── world/              # 世界观设定
│   └── meta/               # 元设定
├── OUTLINE/                # 大纲
│   ├── meta.md             # 总大纲
│   ├── volume-001.md       # 卷大纲
│   └── volume-001/         # 章节细纲
├── STYLE/                  # 风格学习数据
│   ├── profile.json        # 用户风格档案
│   └── prompts/            # 风格提示词
├── CONTENT/                # 正文
│   └── volume-001/         # 卷正文
├── EXPORT/                 # 导出文件
├── ARCHIVE/                # 归档
└── templates/              # 写作模板
```

## 核心设计特点

### 1. 分层架构
- **概念阶段**：story-concept.md（故事概要）
- **设定阶段**：SPECS/（人物、世界观）
- **大纲阶段**：OUTLINE/（总纲 → 卷纲 → 章节大纲）
- **写作阶段**：CONTENT/（正文）
- **归档阶段**：ARCHIVE/（定稿 + 变更记录）

### 2. 风格学习系统
- 从用户修改中提取词汇、句式、节奏偏好
- 生成风格档案，让 AI 输出更符合用户风格
- 目标：将 AI 内容修改率从 50% 降低到 15%

### 3. POV 视角管理
- 严格的 POV（视角）约束系统
- 角色认知状态追踪（已知/未知信息）
- 防止出现视角跳跃和信息泄露

### 4. 状态管理
- 卷状态：draft → confirmed
- 章节状态：outline-draft → outline-confirmed → writing → review → done
- 完整的状态流转和验证

### 5. 多目录支持
- **项目根目录**：设定、大纲、风格数据
- **过程文件目录**：AI 生成的中间产物（快照、摘要、提案）
- **最终输出目录**：小说正文、导出文件、归档

## 技术架构

### 技术栈
- **Python 3.8+**：核心开发语言
- **标准库**：无第三方依赖，兼容性好
- **CLI 框架**：argparse 用于命令解析
- **Markdown**：文档格式（易于阅读和编辑）
- **JSON**：配置文件格式

### 设计原则
1. **简单性**：仅使用标准库，无需复杂配置
2. **兼容性**：支持 Windows/macOS/Linux 多平台
3. **可扩展性**：模块化设计，易于添加新功能
4. **易用性**：清晰的命令结构和文档
5. **稳定性**：向后兼容旧项目结构

## 常见问题

### 1. 如何开始新项目？
```bash
python story.py init
```

### 2. 如何处理已存在的项目？
- 项目根目录有 story.json 文件即可直接使用
- 支持向后兼容旧项目结构

### 3. 如何修改已归档章节？
- 归档章节保存在 ARCHIVE/ 目录中
- 可直接在 ARCHIVE/ 中编辑，但不会自动同步到 CONTENT/

### 4. 如何自定义目录结构？
- 修改 story.json 中的 paths 字段
- 支持单独配置过程文件目录和最终输出目录

### 5. 如何处理不同的小说类型？
- init 阶段可选择类型：玄幻/都市/科幻/悬疑/言情/武侠/历史/游戏/轻小说/其他
- 不同类型有对应的默认配置

## 开发与测试

### 功能测试
- 项目包含 test_define/ 和 test_novel/ 测试目录
- 可运行 _test_init.py 进行初始化测试
- 输出结果保存在 _test_output.txt

### 开发流程
1. 克隆仓库
2. 安装依赖（无需额外依赖）
3. 运行测试
4. 修改代码
5. 提交 PR

## 许可证

MIT License

## 相关资源

- **README.md**：项目详细说明
- **SKILL.md**：AI 技能定义（详细工作流）
- **install.md**：安装指南

