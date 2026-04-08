# 工作记忆 - my-novel-skill 项目

## 项目信息

- **项目路径**: `d:\code\zhihu\my-novel-skill`
- **项目类型**: AI 辅助小说写作工作流 Skill
- **技术栈**: Python 3.x CLI

## 核心设计决策

### v2 新增功能 (2026-04-08)

经评估，精简为 4 个核心功能：

1. **recall** - 章节回顾/摘要
   - 读取预生成摘要文件（由 update-specs 生成）
   - 命令: `story:recall 5`, `story:recall 3-5`, `story:recall --recent 3`

2. **export** - 导出 txt/docx
   - 导出章节为纯文本或 Word 文档
   - 命令: `story:export 1-10`, `story:export --format docx`
   - 依赖 python-docx 库（可选）

3. **outline --expand** - 展开场景细节
   - 展开大纲中的场景，提供详细写作提示
   - 命令: `story:outline --expand 5`, `story:outline --expand 5 --scene 2`

4. **outline --swap** - 调整章节顺序
   - 交换两个章节的大纲内容
   - 命令: `story:outline --swap 8 10`

### 精简掉的功能

- ~~自动衔接~~: 摘要已包含衔接信息，无需重复
- ~~scene~~: 大纲的场景列表本身就是场景灵感

### recall 与 update-specs 的关系

```
写完章节 → story:update-specs 5
                    ↓
              生成摘要 → 保存到 OUTLINE/volume-N/summaries/chapter-005-summary.md
                    
story:recall 5 → 直接读摘要文件（秒开，无需重新分析）
```

## 文件结构

```
src/
├── recall.py       # [NEW] 章节回顾
├── export.py      # [NEW] 导出功能
├── outline.py     # [增强] --expand, --swap
├── __init__.py    # [更新] 注册新模块
story.py           # [更新] 注册 recall, export
SKILL.md           # [更新] 添加新功能文档
README.md          # [更新] 添加新命令说明
```

## 使用习惯

- 用户偏好直接给出需求，较少闲聊
- 关注代码安全性和可移植性
- 喜欢结构化的文档和更新记录
