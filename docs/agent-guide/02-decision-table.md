# 状态机决策表

**根据当前项目状态，Agent 应该建议什么下一步？**

## 如何读取状态

```bash
python story.py status
```
→ 看输出中的信息：
- 基本信息（书名、类型、目标字数）
- 写作进度（完成度、章节进度）
- 设定库（人物数、世界观条目数）
- 待补全列表（draft 部分）

## 决策表

| 当前状态 | Agent 应该建议 |
|----------|----------------|
| **刚 init，什么都没有** | "我们先来完善故事概念吧！" → 引导填 story-concept |
| **有 concept，但没设定** | "需要创建人物和世界观设定吗？" → define |
| **有设定，但 USER-CORE 空** | "请先填写这些文件的 USER-CORE 部分：[列表]" → 等用户填 |
| **USER-CORE 填了，AI-EXPAND 空** | "我来帮你生成 AI-EXPAND 部分！" → draft |
| **设定齐了，但没卷纲** | "我们来生成第一卷的卷纲吧！" → plan --volume 1 |
| **有卷纲，但没章节** | "我们来拆分章节吧！" → plan --chapters 1 |
| **有章节，但没细纲** | "我们来生成章节细纲吧！" → outline --draft 1 --all |
| **有细纲，但没正文** | "我们开始写第 X 章吧！" → write X --draft |
| **正文写了，但没 review** | "要不要对比一下修改差异？" → review X |
| **review 了，但没 learn** | "要不要学习一下你的写作风格？" → learn X |
| **learn 了，但没 update-specs** | "要不要更新一下设定？" → update-specs X |
| **update-specs 了，但没 snapshot** | "要不要生成设定快照？" → snapshot X |
| **snapshot 了，但没 archive** | "要不要归档这一章？" → archive X |
| **归档了几章** | "继续写下一章，还是先导出看看？" |

## 状态总结模板（每次展示 status 后）

```
当前进度总结：
- 书名：《XXX》
- 类型：XXX
- 进度：XX 字 / XX 字（XX%）
- 章节：第 X 卷 / 第 Y 章

下一步建议：
[根据决策表给出 1-2 个建议]

你想做什么？
```
