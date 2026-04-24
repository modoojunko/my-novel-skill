---
name: my-novel-v2
description: 所有小说创作相关操作必须通过此 skill 处理。当用户说要写小说、创建项目、写大纲、写章节、发布章节、管理角色认知时，立即激活此技能。
---

# my-novel-v2 -- AI 辅助小说写作工作流

## 🚨 最重要：技能使用规范（先看这里）

### 🔒 强制使用 Skill 的原则

**所有小说创作相关操作必须通过 `story` 命令进行！绝对不要直接读/写文件！**

- ❌ 不要直接读取或修改 story.yaml、process/、output/ 等文件
- ✅ 所有操作都用 `story <command>` 完成
- ✅ **所有命令必须加 `--non-interactive --json` 参数！**

---

## 🧠 主 Agent 工作流程

像小说创作者一样思考，按以下步骤工作：

### 第一步：理解意图 & 诊断状态

先搞清楚用户要做什么，然后运行 `story status` 查看当前项目状态：

```bash
story status --non-interactive --json
```

根据状态判断下一步：
- 没有项目 → 询问是否初始化新项目
- 有项目但没核心信息 → 引导 collect core
- 有核心信息但没主角 → 引导 collect protagonist
- 准备好了 → 继续下一步

### 第二步：按阶段推进创作

```
【阶段 1：初始化】
story init → story collect core → story collect protagonist → story world basic

【阶段 2：每卷开始前】
直接编辑 story.yaml 规划卷大纲和章节大纲

【阶段 3：每章写作循环】
（可选）story character update → story write N --prompt → 子 Agent 写正文 → story verify N → story archive N

【阶段 4：发布（可选）】
story publish N feishu 或 story publish all feishu
```

### 第三步：用自然语言与用户对话

不要展示命令行输出，而是用自然语言解释结果并询问下一步。

---

## 📖 完整命令参考

| 命令 | 功能 | 常用场景 |
|------|------|----------|
| `story init` | 初始化新项目 | 用户说"我想写本小说" |
| `story status` | 查看项目状态 | 每次开始时先运行这个 |
| `story collect core` | 收集小说核心信息 | 新项目刚初始化后 |
| `story collect protagonist` | 创建主角 | 核心信息收集后 |
| `story world basic` | 设定基础世界观 | 主角创建后 |
| `story world faction <name>` | 设定势力 | 需要添加势力时 |
| `story world list` | 列出所有世界观设定 | 查看已有设定时 |
| `story character list` | 列出所有角色认知 | 查看角色状态时 |
| `story character view <角色名>` | 查看角色详细认知 | 检查某角色知道什么时 |
| `story character update <角色名>` | 更新角色认知 | 某章写完后更新角色记忆 |
| `story character check <角色名>` | 检查POV一致性 | 验证角色设定时 |
| `story write <num> --prompt` | 生成章节提示词 | 准备写第N章时 |
| `story verify <num>` | 验证章节是否符合大纲 | 第N章写完后 |
| `story archive <num>` | 归档已完成章节 | 第N章验证通过后 |
| `story unarchive <num>` | 取消归档，恢复到content | 重新创作已归档章节 |
| `story export` | 导出小说 | 完成后导出 |
| `story publish status` | 查看发布状态 | 检查哪些章节已发布 |
| `story publish <num> feishu` | 发布单章到飞书 | 发布第N章 |
| `story publish all feishu` | 发布所有未发布章节 | 批量发布 |
| `story github list` | 列出GitHub Issues | 查看工具问题时 |
| `story migrate` | 迁移旧项目结构 | 有旧版本项目时 |

---

## ⚙️ story character 角色认知管理详解

**目的：** 防止角色OOC，确保每个角色只知道他应该知道的事。

### 常用子命令：

```bash
# 查看所有角色认知状态
story character list --non-interactive --json

# 查看某角色详细认知
story character view "张三" --non-interactive --json

# 更新角色认知（写完某章后常用）
story character update "张三" \
  --event "张三在酒馆见到了李四，李四透露了他是卧底" \
  --world "张三发现城东有个秘密据点" \
  --character "张三认识了赵六" \
  --unaware "张三还不知道王五已经背叛了" \
  --relationship "张三现在信任李四" \
  --pov "从张三视角写时，只能写他亲眼看到的" \
  --non-interactive --json

# 检查POV一致性
story character check "张三" --chapter 1 --non-interactive --json

# 导出认知给提示词（很少手动运行，write命令会自动处理）
story character export "张三" --non-interactive --json
```

---

## 🎯 writing-principles.yaml 写作原则配置

**说明：** 每个项目都有这个文件，包含写作风格、技巧、禁忌规则。

**使用方式：** 
- 项目初始化时自动从模板复制
- 用户可以手动编辑此文件
- `story write` 命令会自动读取并集成到提示词中

**主要配置项：**
- `style`: 整体写作风格描述、语气、叙事视角
- `core_principles`: 核心原则（按优先级排序）
- `techniques`: 写作技巧（自然表达、展示而非告知等）
- `taboos`: 禁忌规则列表
- `word_count`: 字数要求
- `output_format`: 输出格式

---

## 📁 目录结构（了解即可，不要直接操作文件）

```
{项目根}/
  story.yaml                    # 配置 + 总进度
  writing-principles.yaml       # 写作原则配置
  process/                      # 过程管理产物
    INFO/                       # 收集到的信息
    OUTLINE/                    # 大纲草稿
    PROMPTS/                    # 生成的提示词
  output/                       # 最终正文
    CONTENT/                    # 章节正文
    ARCHIVE/                    # 已归档章节
```

---

## 💡 Agent 提示示例

**用户说："我想写本玄幻小说"**
→ Agent 回应：好的！我来帮你创建一个玄幻小说项目。先运行 `story init`...

**用户说："我想写第三章"**
→ Agent 回应：先让我看看当前进度...（运行 story status）然后生成第三章提示词

**用户说："帮我看看张三现在知道什么"**
→ Agent 回应：我来查看一下张三的认知状态...（运行 story character view "张三"）

**用户说："这章写完了，张三现在知道了李四的秘密"**
→ Agent 回应：好的，我来更新张三的认知...（运行 story character update "张三" --event "..."）
