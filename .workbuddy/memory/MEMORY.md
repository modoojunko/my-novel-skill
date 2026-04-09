# 工作记忆 - my-novel-skill 项目

## 项目信息

- **项目路径**: `d:\code\zhihu\my-novel-skill`
- **项目类型**: AI 辅助小说写作工作流 Skill
- **技术栈**: Python 3.x CLI

## 核心设计决策

### v3 Pipeline 流水线 (2026-04-09)

完整的人机协作写作流水线：

```
主线 → [AI生成卷纲] → [人审/讨论] → 卷纲定稿
     → [AI拆章节] → [人审/讨论] → 章节列表定稿
     → [AI写章节细纲] → [人审/讨论] → 细纲定稿
     → [AI写正文] → [人审/讨论/修改] → 章节完成
```

**核心命令**：
- `story:plan --volume N`：AI 生成卷纲草稿
- `story:plan --volume N --revise`：讨论修改
- `story:plan --volume N --confirm`：确认定稿
- `story:plan --chapters N`：AI 拆分章节
- `story:outline --draft N --all`：批量生成细纲
- `story:write N --draft`：AI 写正文

**Stage 状态**：
- 卷: `draft` → `confirmed`
- 章节: `outline-draft` → `outline-confirmed` → `writing` → `review` → `done`

**设计决策**：
- 不单独拆 pipeline.py，stage 管理逻辑写在 plan.py 里
- 两种入口都支持：读取主线文件 OR 交互式问答
- 两种讨论模式：直接编辑文件 + 对话讨论
- 自动引导下一步，批量 + 单个处理都支持

### 试水测试 (2026-04-09)

完成试水小说《子夜便利店》（都市奇幻），1卷5章，约10,449字。

**试水关键发现**：
1. **skill 核心定位是"管理"而非"生成"**——它负责结构、状态、文件组织，AI 内容生成需要外部 Agent
2. CLI 命令生成 Prompt 文件，Agent 读取 Prompt 生成内容，再由 skill 管理 stage
3. `find_project_root()` 基于 cwd，需 cd 到项目目录
4. PowerShell 下 init 命令有兼容性问题，手动创建更可靠
5. AI 生成质量综合评分 3.9/5，伏笔设计最强(4.5)，字数偏少是主要不足

**小说文件位置**: `d:\code\zhihu\my-novel-skill\stories\midnight-store\`

### 六层认知系统 (2026-04-09)

为角色设定增加六层认知模型，解决"角色缺少核心驱动力"的问题：

1. **我的世界观** → 影响角色面对事件时的态度和信念
2. **我对自己定义** → 影响角色的内心独白和行为动机
3. **我的价值观** → 影响角色在冲突中的选择
4. **我的能力** → 决定角色是直接解决问题还是需要学习成长
5. **我的技能** → 角色日常行为的基础
6. **我的环境** → 角色行为和认知的背景约束

**修改的文件**：
- `src/define.py` - CHARACTER_TEMPLATE 增加六层认知章节 + 交互式创建引导
- `src/write.py` - 新增 `read_character_cognition()` 和 `generate_cognition_prompt()`，在 Prompt 中注入认知驱动
- `SKILL.md` - 更新人物卡模板、写作规范、Agent Prompt 结构
- 三个角色文件（林夜、苏念、老周）补充六层认知内容

### v2 新增功能 (2026-04-08)

精简为 4 个核心功能：

1. **recall** - 章节回顾/摘要
2. **export** - 导出 txt/docx
3. **outline --expand** - 展开场景细节
4. **outline --swap** - 调整章节顺序

## 文件结构

```
src/
├── plan.py        # [NEW] 流水线命令
├── recall.py      # 章节回顾
├── export.py     # 导出功能
├── outline.py     # [增强] Pipeline 功能
├── write.py       # [增强] Pipeline 功能
├── __init__.py    # 注册 plan
story.py           # [更新] 注册 plan
SKILL.md          # [更新] Pipeline 文档
```

## 使用习惯

- 用户偏好直接给出需求，较少闲聊
- 关注代码安全性和可移植性
- 喜欢结构化的文档和更新记录
