# SKILL.md Agent 操作规范完善设计

## 背景

SKILL.md Phase 1/2/3 的流程定义不完整：
1. Phase 1 缺少验收标准，且没有用户确认环节
2. Phase 2 已有 schema 附录（上一轮已完成）
3. Phase 3 缺少用户确认 verify 结果的流程
4. 命令参考表缺少 github 命令说明

## 解决方案

### 1. Phase 1 流程完善

**改为：**
```
【阶段 1：初始化】
story init → story collect core → story world basic → 用户确认 story.yaml

其中：
- collect core: 收集小说名、故事主线、核心设定
- world basic: 世界基础设定（可在 Phase 3 按需扩展）
- 用户确认: Agent 展示 story.yaml 内容，用户确认后才进入 Phase 2
```

**验收标准：** 用户确认 story.yaml 内容后进入 Phase 2

### 2. Phase 3 流程完善

**改为：**
```
【阶段 3：每章写作循环】
1. story write N --prompt     生成提示词
2. 子 Agent 写正文             按提示词写第 N 章
3. story verify N              验证章节是否符合大纲
4. 展示验证报告                Agent 展示 verify 结果，告知用户查阅文档
5. 用户确认                    用户自行判断验证结果
6. story archive N             归档（如用户确认通过）
（可选）story character update  更新角色认知
```

**验证结果处理：**
- verify 通过 → 展示报告 → 用户确认 → archive
- verify 失败 → 展示问题 → 用户决定处理方式（重写/修改大纲/强制归档）

### 3. 命令参考表补充

**新增 github 命令说明：**
| `story github <action>` | GitHub Issue 管理（list/view/create） | 查看或创建工具问题 |

**world 命令保持只列 basic。**

## 修改文件

1. **SKILL.md** - Phase 1/3 流程改动 + 命令参考表补充
