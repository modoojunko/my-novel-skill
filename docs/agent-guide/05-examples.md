# 完整对话流示例

## 示例：从"我想写小说"到"第一卷完成"

```
用户：我想写小说
Agent: [运行 status]
       看起来还没有项目！我们来创建一个新小说项目！
       先回答几个问题...
       
用户：书名叫《子夜便利店》，类型悬疑，50万字，3卷
Agent: [运行 init]
       好的！项目已创建！
       接下来我们来完善故事概念...
       
用户：一个普通的便利店员，在深夜便利店中，必须接待亡魂客人，否则自己无法转世
Agent: 好的！故事概念很有意思！
       接下来我们来创建人物和世界观设定...
       
用户：先创建主角林夜
Agent: [运行 define character 林夜]
       人物卡已创建！请填 USER-CORE 部分...
       
用户：填好了
Agent: 好的！我来帮你生成详细内容！
       [运行 draft character 林夜 --json → 拿到 JSON]
       [基于 prompt 生成 AI-EXPAND 内容]
       [运行 draft character 林夜 --ai <我的输出>]
       好了！林夜的人物卡已补全！
       
用户：接下来呢？

Agent: [运行 status]
       我们来生成第一卷的卷纲吧！
       [运行 plan --volume 1 --json → 拿到 JSON]
       [基于 prompt 生成卷纲]
       [保存到 OUTLINE/volume-001/volume-001-outline.md]
       卷纲已生成！你看看，需要讨论修改吗？

用户：可以了，确认吧

Agent: [运行 plan --volume 1 --confirm]
       好的！卷纲已确认！
       接下来拆分章节...
       [运行 plan --chapters 1 --json]
       [生成章节列表]
       [运行 plan --chapters 1 --confirm]
       好的！接下来生成细纲...

（继续下去...）

Agent: 大纲都确认了！开始写正文吧！
       [运行 write 1 --draft --json]
       [基于 prompt 生成正文]
       [保存到 CONTENT/volume-001/chapter-001.md]
       第一章已写好！请修改，然后我们来对比差异学习风格。

（写完一章后）

Agent: 写得不错！要不要对比一下差异？
       [运行 review 1]
       修改率 35%，要不要学习一下风格？

用户：好
Agent: [运行 learn 1]
       已更新风格档案！
       
（继续写完几章后）

Agent: 这几章都写完了！要不要归档一下？
       [运行 archive 1-5]
       已归档！
       
Agent: 第一卷进度不错！要不要导出看看？
       [运行 export --volume 1 --format docx]
       已导出！第一卷完成！
```

---

## 完整对话流示例（Agent 驱动）

```
用户：我想写小说，书名叫《子夜便利店》

你：[运行 status]
    看起来还没有项目！我们来创建...
    [收集信息]
    [运行 init]
    好的！项目已创建！

用户：先创建主角林夜

你：[运行 define character 林夜]
    人物卡已创建！请填写 USER-CORE 部分...

用户：[填完了]

你：好的！我来帮你生成详细内容！
    [运行 draft character 林夜 --json → 拿到 JSON]
    [基于 prompt 生成 AI-EXPAND 内容]
    [运行 draft character 林夜 --ai <我的输出>]
    好了！林夜的人物卡已补全！

用户：接下来呢？

你：[运行 status]
    我们来生成第一卷的卷纲吧！
    [运行 plan --volume 1 --json → 拿到 JSON]
    [基于 prompt 生成卷纲]
    [保存到 OUTLINE/volume-001/volume-001-outline.md]
    卷纲已生成！你看看，需要讨论修改吗？

用户：可以了，确认吧

你：[运行 plan --volume 1 --confirm]
    好的！卷纲已确认！
    接下来拆分章节...
    [运行 plan --chapters 1 --json]
    [生成章节列表]
    [运行 plan --chapters 1 --confirm]
    好的！接下来生成细纲...

（继续下去...）
```
