# 如何正确读取和使用 CLI 生成的 Prompt

**这是最重要的一章！** 作为 AI Agent，你不需要让用户复制粘贴 Prompt——你直接用！

## 两种使用模式

### 模式 A：JSON 模式（推荐，Agent 驱动）

**任何生成 Prompt 的命令都加 `--json` 选项：**

```bash
python story.py draft character 张三 --json
python story.py plan --volume 1 --json
python story.py outline --draft 5 --json
python story.py write 5 --draft --json
```

**JSON 输出格式：**

```json
{
  "type": "draft-character",
  "target": "张三",
  "prompt_file": "OUTLINE/prompts/draft-character-张三-prompt.md",
  "prompt_content": "...完整的 prompt 内容...",
  "next_step": "请基于这个 prompt 生成...",
  "import_command": "story:draft character 张三 --ai <你的输出文件>",
  "target_file": "SPECS/characters/张三.md"
}
```

**你的工作流程：**

1. **运行带 `--json` 的命令** → 拿到 JSON
2. **读取 `prompt_content`** → 这是给你的任务
3. **直接基于这个 Prompt 生成内容** → 用你自己的大模型能力
4. **提取需要的部分**（通常是 AI-EXPAND 区域）
5. **保存到临时文件** 或 **直接用下一步命令导入**

**不需要用户做任何事！你是 Agent，你直接做！**

---

### 模式 B：普通模式（用户交互）

如果不用 `--json`，CLI 会输出：

```
═══════════════════════════════════════════════════════════════
  🤖 给 AI Agent 的 Prompt
═══════════════════════════════════════════════════════════════

[...完整的 prompt...]

═══════════════════════════════════════════════════════════════
  📋 Agent 操作指南
═══════════════════════════════════════════════════════════════

1. 基于上面的 Prompt 生成 AI-EXPAND 内容
2. 只返回 <!-- AI-EXPAND:START --> 和 <!-- AI-EXPAND:END --> 之间的内容
3. 将你的输出保存到临时文件，或直接传递给 --ai 选项
4. 运行：story draft character 张三 --ai <your_output_file>

💡 Prompt 已保存到：OUTLINE/prompts/draft-character-张三-prompt.md
═══════════════════════════════════════════════════════════════
```

**你的工作流程：**

1. **读取上面的 Prompt 部分**（`🤖 给 AI Agent 的 Prompt` 下面）
2. **直接基于这个 Prompt 生成内容** → 用你自己的大模型能力
3. **告诉用户："我来帮你生成！"** → 不需要用户复制
4. **生成完后，自动运行下一步命令导入**

---

## 各命令的 Agent 操作流程

### 场景 1：draft 模块（设定补全）

**用户说："帮我补全张三的人物卡"**

```
你：
1. python story.py draft character 张三 --json
2. 拿到 JSON，读取 prompt_content
3. 基于这个 prompt 生成 AI-EXPAND 内容
4. 将生成的内容保存到临时文件
5. python story.py draft character 张三 --ai temp_file.md
6. 告诉用户："好了！张三的人物卡已补全！"
```

**关键点：**
- 只生成 `<!-- AI-EXPAND:START -->` 和 `<!-- AI-EXPAND:END -->` 之间的内容
- 或者直接把完整的内容（包含标记）给 `--ai`，它会自动提取

---

### 场景 2：plan 模块（卷纲/章节）

**用户说："帮我生成第一卷的卷纲"**

```
你：
1. python story.py plan --volume 1 --json
2. 拿到 JSON，读取 prompt_content
3. 基于这个 prompt 生成卷纲
4. 将生成的内容保存到 OUTLINE/volume-001/volume-001-outline.md
5. 告诉用户："卷纲已生成！需要讨论修改吗？"
```

---

### 场景 3：outline 模块（细纲）

**用户说："帮我生成第五章的细纲"**

```
你：
1. python story.py outline --draft 5 --json
2. 拿到 JSON，读取 prompt_content
3. 基于这个 prompt 生成细纲
4. 保存到 OUTLINE/volume-001/chapter-005.md
5. 告诉用户："细纲已生成！需要确认吗？"
```

---

### 场景 4：write 模块（正文）

**用户说："帮我写第五章"**

```
你：
1. python story.py write 5 --draft --json
2. 拿到 JSON，读取 prompt_content
3. 基于这个 prompt 生成正文（注意 POV 约束！）
4. 保存到 CONTENT/volume-001/chapter-005.md
5. 告诉用户："第五章已写好！请修改，然后我们来对比差异学习风格。"
```

---

## 关键提醒

### ❌ 绝对不要做的事：

1. **不要**告诉用户："请复制这个 prompt 给 AI"
2. **不要**让用户在你和另一个 AI 之间传话
3. **不要**只输出 prompt 就完事了

### ✅ 一定要做的事：

1. **直接**用你自己的能力生成内容
2. **直接**运行 CLI 命令保存/导入
3. **让用户只做决策**（确认/修改/否决），不做操作
