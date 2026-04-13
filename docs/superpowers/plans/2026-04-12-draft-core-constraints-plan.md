# Draft 核心设定约束 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 强化 `story draft` 功能，让 AI 扩写时严格遵守小说核心设定（总纲、世界观、其他角色），并解决 POV 视角问题。

**Architecture:** 
- 在 `draft.py` 中新增 `load_core_context()` 函数加载全局设定
- 修改 `build_expansion_prompt()` 注入核心设定上下文
- 重写三个 prompt 模板文件，增加核心设定头部、POV 约束和自我检查

**Tech Stack:** Python 3.8+, Markdown, 仅标准库

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `src/draft.py` | 修改 | 新增 `load_core_context()`，修改 `build_expansion_prompt()` |
| `src/prompts/draft_character.md` | 重写 | 加入核心设定头部、POV 约束、自我检查 |
| `src/prompts/draft_world.md` | 重写 | 类似修改（世界观扩写也要遵守总纲） |
| `src/prompts/draft_meta.md` | 重写 | 类似修改 |

---

## Task 1: 新增 load_core_context() 函数

**Files:**
- Modify: `src/draft.py`

- [ ] **Step 1: 在 draft.py 顶部添加导入（如需要）**

在现有导入之后添加（如果需要）：
```python
from .define import parse_character_frontmatter, parse_world_frontmatter
```

- [ ] **Step 2: 在 draft.py 的 # ============================================================================ 标记后新增 load_core_context() 函数**

在 `# ============================================================================` 和 `# Prompt 模板加载` 之间添加：

```python
# ============================================================================
# 核心设定加载器
# ============================================================================

def load_core_context(paths: Dict[str, Path], target_type: str, target_name: str) -> Dict[str, str]:
    """
    加载小说核心设定上下文，用于注入 draft prompt。
    
    加载策略：
    - 总纲：全文加载（超长时智能截断，8000字符上限）
    - 世界观：全文加载，按类别分组（每个文件3000字符上限）
    - 其他角色：列表 + 标签（不加载完整内容）
    - 约束清单：从总纲中提取明确的规则
    
    Args:
        paths: 项目路径字典
        target_type: 'character' | 'world' | 'meta'
        target_name: 目标名称（角色名/世界观类别等）
    
    Returns:
        {
            'meta': 总纲内容,
            'world_summary': 世界观内容（按类别分组）,
            'character_list': 已有角色列表,
            'constraints': 约束清单
        }
    """
    context = {
        'meta': '',
        'world_summary': '',
        'character_list': '',
        'constraints': ''
    }
    
    # 1. 加载总纲
    meta_path = paths['outline'] / 'meta.md'
    if meta_path.exists():
        content = meta_path.read_text(encoding='utf-8')
        if len(content) > 8000:
            content = content[:8000] + "\n\n（... 总纲过长，已截断）"
        context['meta'] = content
    
    # 2. 加载世界观（全文，按类别）
    world_dir = paths['world']
    if world_dir.exists():
        world_entries = []
        for world_file in sorted(world_dir.glob('*.md')):
            fm = parse_world_frontmatter(world_file)
            name = fm.get('name', world_file.stem)
            category = fm.get('category', '其他')
            
            content = world_file.read_text(encoding='utf-8')
            if len(content) > 3000:
                content = content[:3000] + "\n\n（... 已截断）"
            
            world_entries.append(f"### {category}：{name}\n\n{content}\n")
        
        if world_entries:
            context['world_summary'] = "\n".join(world_entries)
    
    # 3. 加载角色列表（只列名字 + 标签，不加载完整内容）
    chars_dir = paths['characters']
    if chars_dir.exists():
        char_list = []
        for char_file in sorted(chars_dir.glob('*.md')):
            if char_file.stem == target_name and target_type == 'character':
                continue
            fm = parse_character_frontmatter(char_file)
            name = fm.get('name', char_file.stem)
            occupation = fm.get('occupation', '')
            status = fm.get('status', '')
            tags = fm.get('tags', [])
            
            line = f"- {name}"
            if occupation:
                line += f"（{occupation}）"
            if status and status != '存活':
                line += f" [{status}]"
            if tags and tags != [name]:
                if isinstance(tags, list):
                    tag_str = ', #'.join(tags[:3])
                else:
                    tag_str = str(tags)[:50]
                line += f" #{tag_str}"
            
            char_list.append(line)
        
        if char_list:
            context['character_list'] = "已有角色：\n" + "\n".join(char_list)
    
    # 4. 提取约束清单（从总纲中找明确的"规则"）
    constraints = []
    if context['meta']:
        for line in context['meta'].split('\n'):
            line = line.strip()
            if line and (('必须' in line) or ('设定' in line) or ('规则' in line) or ('⚠️' in line)):
                constraints.append(f"- {line}")
    
    if constraints:
        context['constraints'] = "\n".join(constraints)
    
    return context
```

- [ ] **Step 3: 修改 build_expansion_prompt() 函数签名和实现**

将原函数替换为：

```python
def build_expansion_prompt(user_core: str, template_name: str, 
                          core_context: Dict[str, str], target_name: str) -> str:
    """
    构建 AI 补全的 prompt，包含核心设定上下文。
    
    Args:
        user_core: USER-CORE 内容
        template_name: 模板名
        core_context: load_core_context() 返回的核心设定字典
        target_name: 目标名称（角色名/世界观类别等）
    
    Returns:
        完整的 prompt
    """
    template = load_prompt_template(template_name)
    if not template:
        return ""
    
    # 构建各 section
    meta_section = ""
    if core_context.get('meta'):
        meta_section = "## 总纲概要\n\n" + core_context['meta']
    
    world_section = ""
    if core_context.get('world_summary'):
        world_section = "## 世界观背景\n\n" + core_context['world_summary']
    
    character_list_section = ""
    if core_context.get('character_list'):
        character_list_section = "## 已有角色\n\n" + core_context['character_list']
    
    constraints_section = ""
    if core_context.get('constraints'):
        constraints_section = "## 重要约束\n\n" + core_context['constraints']
    
    # 替换模板变量
    prompt = template.replace("{user_core_content}", user_core)
    prompt = prompt.replace("{character_name}", target_name)
    prompt = prompt.replace("{target_name}", target_name)
    prompt = prompt.replace("{meta_section}", meta_section)
    prompt = prompt.replace("{world_section}", world_section)
    prompt = prompt.replace("{character_list_section}", character_list_section)
    prompt = prompt.replace("{constraints_section}", constraints_section)
    
    return prompt
```

- [ ] **Step 4: 修改 main() 中调用 build_expansion_prompt() 的地方**

在 `src/draft.py` 第 460 行附近（`args.subcommand != 'all'` 的分支中），找到：

```python
prompt = build_expansion_prompt(user_core, template_type)
```

替换为：

```python
# 加载核心设定上下文
core_context = load_core_context(paths, args.subcommand, target_name)
prompt = build_expansion_prompt(user_core, template_type, core_context, target_name)
```

注意：`target_name` 需要在前面定义（在 file_path/template_type 定义之后）：
```python
target_name = args.name if args.subcommand == 'character' else (
    args.category if args.subcommand == 'world' else 'meta'
)
```

---

## Task 2: 重写 draft_character.md Prompt 模板

**Files:**
- Rewrite: `src/prompts/draft_character.md`

- [ ] **Step 1: 完全替换 draft_character.md 的内容**

```markdown
你是一位资深小说设定师。请基于以下核心设定和用户填写的信息，补全角色设定。

===============================================================================
🔒 小说核心设定（必须严格遵守，绝对不能冲突）
===============================================================================

{meta_section}

{world_section}

{character_list_section}

{constraints_section}

⚠️ 【重中之重】你的所有输出必须与上述设定完全一致！
   - 不要编造未在核心设定中提及的重要世界观信息
   - 如果涉及其他角色，确保与已有设定不冲突
   - 如有不确定的地方，不要编造，留空或注明"待确认"

===============================================================================
👁️ POV 视角约束（尤其重要！）
===============================================================================

你正在补全的是「{character_name}」这个角色的设定卡。

⚠️ 【关键警告】区分"你知道" vs "该角色知道"！
   - 你可以看到所有小说设定（总纲、其他角色、世界观）
   - 但该角色只能知道"在当前时间点，TA 应该知道的信息"
   - 不要让该角色知道 TA 不该知道的事情！

【该角色的认知边界】
- 除非 USER-CORE 明确说明，否则默认该角色不认识其他未提及的角色
- 除非 USER-CORE 明确说明，否则默认该角色不知道其他角色的背景故事
- 在"人物关系建议"中，如果建议与某角色有关联，请注明"这是建议的后续剧情发展，不是既成事实"

【错误示例 vs 正确示例】
❌ 错误："角色A看到照片，觉得和角色D一模一样"（除非角色A已经认识角色D）
✅ 正确："角色A看到照片，觉得这个人很眼熟，但想不起来在哪见过"
✅ 正确："（建议后续剧情：让角色A在某个场合遇到角色D，发现两人长得很像）"

===============================================================================
📝 当前角色：{character_name}
===============================================================================

## 用户核心信息
{user_core_content}

===============================================================================
✍️ 补全要求
===============================================================================

1. **严格遵守**：上方的"小说核心设定"和"POV视角约束"是硬性约束，不得违反
2. **外貌描写**：150-200字，匹配身份和性格
3. **性格扩展**：基于核心性格推导优点、缺点、压力反应
4. **背景故事**：300-500字，解释身份和目标的由来
5. **六层认知**：从核心性格深度推导
6. **人物关系建议**：基于身份和与主角关系

===============================================================================
✅ 自我检查（写完后请确认）
===============================================================================

在输出前，请逐项确认：
- [ ] 没有与总纲冲突的内容
- [ ] 没有与世界观冲突的内容
- [ ] 没有编造未在核心设定中提及的重要世界观信息
- [ ] 人物关系符合已有设定（如有）
- [ ] 该角色的核心设定（USER-CORE）被完全尊重，没有被篡改
- [ ] 没有 POV 视角问题：该角色只知道 TA 该知道的信息

===============================================================================

## 输出格式

严格按照以下格式输出，只包含 AI-EXPAND 部分的内容：

## 🔶 AI 补全区

### 外貌描写
（AI 根据核心性格生成，匹配身份和特征）

### 性格扩展
- **优点**：
- **缺点**：
- **在压力下的反应**：

### 背景故事
（AI 基于身份和目标生成，300-500字）

### 六层认知
（AI 从核心性格推导）
1. **我的世界观**：
2. **我对自己的定义**：
3. **我的价值观**：
4. **我的核心能力**：
5. **我的技能**：
6. **我的环境**：

### 人物关系建议
（AI 基于身份和与主角关系生成）

⚠️ 注：以下是**建议的关系设定**，不是既成事实。如果建议该角色认识某人，请确认 USER-CORE 中有明确说明。
```

---

## Task 3: 重写 draft_world.md Prompt 模板

**Files:**
- Rewrite: `src/prompts/draft_world.md`

- [ ] **Step 1: 完全替换 draft_world.md 的内容**

```markdown
你是一位资深世界观设定师。请基于以下核心设定和用户填写的信息，补全世界观设定。

===============================================================================
🔒 小说核心设定（必须严格遵守，绝对不能冲突）
===============================================================================

{meta_section}

{character_list_section}

{constraints_section}

⚠️ 【重中之重】你的所有输出必须与上述设定完全一致！
   - 不要编造未在总纲中提及的重要世界观信息
   - 如果涉及已有角色，确保与他们的设定不冲突
   - 如有不确定的地方，不要编造，留空或注明"待确认"

===============================================================================
📝 当前设定：{target_name}
===============================================================================

## 用户核心信息
{user_core_content}

===============================================================================
✍️ 补全要求
===============================================================================

1. **严格遵守**：上方的"小说核心设定"是硬性约束，不得违反
2. **详细说明**：对每条核心规则进行扩展解释
3. **具体例子/表现**：生成 2-3 个在故事中的具体体现
4. **与其他设定的关联**：建议如何与已有世界观设定配合

===============================================================================
✅ 自我检查（写完后请确认）
===============================================================================

在输出前，请逐项确认：
- [ ] 没有与总纲冲突的内容
- [ ] 没有与其他世界观设定冲突的内容
- [ ] 没有编造未在总纲中提及的重要世界观信息
- [ ] 该设定的核心信息（USER-CORE）被完全尊重，没有被篡改

===============================================================================

## 输出格式

严格按照以下格式输出，只包含 AI-EXPAND 部分的内容：

## 🔶 AI 补全区

### 详细说明
（AI 基于核心规则扩展）

### 具体例子/表现
（AI 生成在故事中的具体体现）

### 与其他设定的关联
（AI 建议如何与其他世界观设定配合）
```

---

## Task 4: 重写 draft_meta.md Prompt 模板

**Files:**
- Rewrite: `src/prompts/draft_meta.md`

- [ ] **Step 1: 完全替换 draft_meta.md 的内容**

```markdown
你是一位资深小说设定师。请基于以下用户填写的核心信息，补全总纲设定。

===============================================================================
📝 当前目标：补全总纲
===============================================================================

## 用户核心信息
{user_core_content}

===============================================================================
✍️ 补全要求
===============================================================================

1. **保持一致性**：补全内容要与 USER-CORE 的核心基调一致
2. **详细展开**：对每个核心要点进行扩展说明
3. **提供示例**：为抽象概念提供具体的故事中的例子

===============================================================================
✅ 自我检查（写完后请确认）
===============================================================================

在输出前，请确认：
- [ ] 该总纲的核心信息（USER-CORE）被完全尊重，没有被篡改
- [ ] 补全内容与核心基调一致

===============================================================================

## 输出格式

严格按照以下格式输出，只包含 AI-EXPAND 部分的内容：

## 🔶 AI 补全区

（AI 基于核心信息展开补全）
```

---

## Task 5: 测试验证

**Files:**
- Test: 使用现有测试项目或新建测试项目

- [ ] **Step 1: 验证代码可以正常导入**

运行：
```bash
cd /mnt/d/code/zhihu/my-novel-skill
python -c "from src.draft import load_core_context, build_expansion_prompt; print('OK')"
```
Expected: 输出 `OK`，无错误

- [ ] **Step 2: 检查 draft.py 可以正常运行（显示帮助）**

运行：
```bash
python story.py draft --help
```
Expected: 显示帮助信息，无错误

- [ ] **Step 3: 如果有测试项目，测试 draft character 命令**

在有 story.json 的测试项目中运行：
```bash
python story.py draft character <某个角色名>
```
Expected: 生成的 prompt 中包含核心设定头部、POV 约束等新内容

---

## Task 6: 提交更改

**Files:**
- Git: 提交所有修改

- [ ] **Step 1: 查看更改**

```bash
git status
git diff
```

- [ ] **Step 2: 提交更改**

```bash
git add src/draft.py src/prompts/draft_character.md src/prompts/draft_world.md src/prompts/draft_meta.md
git commit -m "feat: 强化 draft AI 扩写遵守核心设定约束

- 新增 load_core_context() 加载总纲/世界观/角色列表
- 修改 build_expansion_prompt() 注入核心设定上下文
- 重写三个 prompt 模板，增加核心设定头部、POV 约束和自我检查
- 解决上帝视角问题，明确区分'AI知道'vs'角色知道'"
```

---

## 计划完成

计划已完整。请使用 subagent-driven-development 或 executing-plans 来执行。
