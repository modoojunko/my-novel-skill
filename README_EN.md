# AI-Assisted Novel Writing Workflow

> Solving common pain points in AI novel writing: forgetting details, inconsistent settings, OOC characters, prompt truncation...

---

## 🎯 What Problems Does This Tool Solve?

### 1️⃣ AI "Forgets" Details While Writing?
**Problem**: AI forgets earlier content, misspells character names, drops foreshadowing, creates plot inconsistencies
**Solutions**:
- ✅ **Setting Snapshot Mechanism** - Auto-generate snapshots after each chapter, recording what happened, who appeared, character status changes
- ✅ **Main Agent + Sub-Agent Separation** - Main agent manages progress and memory, sub-agent only writes content

---

### 2️⃣ Prompts Get Truncated Due to Length?
**Problem**: Putting worldbuilding, characters, and previous context all in leads to huge prompts that get truncated
**Solutions**:
- ✅ **Layered Prompt Summarization** - Prioritized layers: critical info (chapter outline, task list, POV constraints) kept in full, secondary info intelligently summarized
- ✅ **Token Budget Control** - L0 (must-have) 30%, L1 (very important) 30%, L2 (useful) 20%, L3 (optional) 20%

---

### 3️⃣ Characters Know Future Plot Too Early?
**Problem**: Characters know the murderer before investigating, call strangers by name, all kinds of OOC
**Solutions**:
- ✅ **POV Cognitive Constraints** - Each character has independent cognitive state, strictly limited to what they see, hear, and infer
- ✅ **Six-Layer Character Cognitive Model** - Worldview → Self-Definition → Values → Abilities → Skills → Environment, ensuring character behavior matches settings

---

### 4️⃣ Too Much Upfront Planning Burden?
**Problem**: Before writing, need to outline the entire book, hundreds of characters, complete worldbuilding - easy to give up
**Solutions**:
- ✅ **Plan One Volume, Write One Volume** - No need to plan the entire book at once; write Volume 1 first, then plan Volume 2
- ✅ **Progressive Information Collection** - Core settings first, details filled in as you write

---

### 5️⃣ File Chaos Makes Things Hard to Find?
**Problem**: Outlines, character settings, drafts all mixed together, impossible to find anything
**Solutions**:
- ✅ **Three-Directory Design** - process/ (process management), output/ (final content) clearly separated
- ✅ **All YAML Data Format** - Human-readable, easy to edit, no database needed

---

### 6️⃣ Publishing to Multiple Platforms is a Hassle?
**Problem**: After writing a chapter, need to copy-paste to Feishu, Zhihu, Qidian, and manually update table of contents
**Solutions**:
- ✅ **One-Click Multi-Platform Publishing** - Feishu Docs and other platforms supported, auto-skip unchanged content
- ✅ **Publishing Status Tracking** - Record publish time, URL, status

---

### 7️⃣ Worldbuilding Settings Scattered and Disorganized?
**Problem**: Factions, history, power systems, locations scattered in various notes, can't find when needed
**Solutions**:
- ✅ **Complete Worldbuilding Framework** - faction, history, power, organization, location unified management

---

## 🤖 Instructions for Agents (Important!)

This is the my-novel-skill repository, an AI-assisted novel writing workflow.

**Use this Skill when user mentions:**
- "Write novel", "Create novel project", "Novel outline"
- "Protagonist", "Character", "Worldbuilding"
- "Chapter X", "Volume outline", "Chapter outline"
- "story.yaml", "process/", "output/"
- Any novel writing related operations

**Usage Rules:**
1. All operations through `python story.py <command>`
2. **Must use** `--non-interactive --json` mode
3. Don't make user run commands directly; you run them and explain results
4. First run `story status` to check current project state
5. Talk to user in natural language, don't show command line output

**Command Example Format:**
```bash
# Check status
python story.py status --non-interactive --json

# Initialize project
python story.py init --non-interactive --json --args '{"title":"My Novel","genre":"Xianxia","words":500000,"volumes":3}'
```

---

## 👤 Guide for Authors

### You Can Start With...

✨ "I want to write a Xianxia novel"
✨ "Help me create a protagonist"
✨ "I want to plan Volume 1 outline"
✨ "Generate Chapter 1 prompt"
✨ "Check my current progress"
✨ "Publish completed chapters to Feishu"
✨ "I want to continue writing Chapter 3"

### What This Skill Can Help You With

| Feature | Description |
|---------|-------------|
| 📝 Project Management | Initialize project, check writing progress |
| 🎭 Character Creation | Protagonist, supporting cast, complete six-layer cognitive model |
| 🌍 Worldbuilding | Factions, history, power systems, organizations, locations |
| 📋 Outline Planning | Volume outlines, chapter outlines, plan one volume write one volume |
| ✍️ Writing Assistance | Generate chapter prompts, verify chapter content |
| 📦 Finalization & Archiving | Manage completed chapters |
| 🚀 Multi-Platform Publishing | One-click publish to Feishu Docs and other platforms |

---

## 💬 Example Conversations

### Scenario 1: Start Writing From Scratch

```
Author: I want to write a Xianxia novel about a young man's counterattack

Agent: Okay! Let me help you set this up...
      
      What's your novel's name? How long do you plan to make it?

Author: Let's call it "Nine Heavens Divine Emperor", about 500k words, 3 volumes

Agent: Got it! Let me collect some core info first...
      What's this story about? Who's the protagonist?
```

### Scenario 2: Continue Existing Project

```
Author: Help me check where I left off in my novel

Agent: Okay, let me check your current progress...
      
      You're currently at Volume 1 Chapter 3, volume outline complete, Chapter 3 prompt generated.
      Want to continue with Chapter 3?

Author: Yes, help me generate Chapter 3 prompt

Agent: No problem, generating now...
```

### Scenario 3: Publish Chapters

```
Author: I want to publish completed chapters to Feishu

Agent: Okay, let me check which chapters are archived...
      
      You have 3 archived chapters ready to publish. Publish specific ones or all?

Author: Publish all

Agent: No problem, publishing now...
```

---

## 🔧 Technical Details (For the Curious)

### Core Features

- ✅ **Main Agent + Sub-Agent Architecture** - Separation of responsibilities, avoids "forgetting"
- ✅ **Three-Directory Design** - process/output clearly separated
- ✅ **Zero Dependencies** - Only Python standard library
- ✅ **All YAML Data Format** - Human-readable, easy to edit
- ✅ **Plan One Volume, Write One Volume** - Progressive creation, no upfront burden
- ✅ **Six-Layer Character Cognitive Model** - Worldview/Self-Definition/Values/Abilities/Skills/Environment
- ✅ **Intelligent Layered Prompt Summarization** - Avoid truncation, critical info first
- ✅ **Setting Snapshot Mechanism** - Prevents plot inconsistency
- ✅ **POV Cognitive Constraints** - Prevents characters knowing future plot
- ✅ **Complete Worldbuilding Framework** - faction/history/power/organization/location
- ✅ **Chapter Verification** - Ensures chapters follow outline requirements
- ✅ **Multi-Platform Publishing** - Supports publishing to Feishu Docs and other platforms

### Use as Claude Skill

This project is designed as a skill for Claude Code / WorkBuddy. After installation, skill auto-activates when you mention "write novel", "novel outline", etc.

### Command Line Usage (For Developers)

If you want to use command line directly:

```bash
# Clone project
git clone <repository-url> my-novel-skill
cd my-novel-skill

# No pip install needed, just Python 3.8+
```

**Create Your First Novel:**

```bash
# 1. Create project directory
mkdir my-first-novel
cd my-first-novel

# 2. Initialize project
python /path/to/my-novel-skill/story.py init --non-interactive --json --args '{"title":"My Novel","genre":"Xianxia","words":500000,"volumes":3}'

# 3. Check status
python /path/to/my-novel-skill/story.py status --non-interactive --json
```

### Complete Command List

| Command | Function |
|---------|----------|
| `story init` | Initialize new project |
| `story status` | Show project status |
| `story collect core` | Collect novel core info |
| `story collect protagonist` | Create protagonist |
| `story collect volume <num>` | Collect volume info |
| `story world basic` | Set basic worldbuilding |
| `story world faction <name>` | Set faction settings |
| `story world history` | Set historical background |
| `story world power <name>` | Set power system |
| `story world organization <name>` | Set organization |
| `story world location <name>` | Set location |
| `story world list` | List all worldbuilding settings |
| `story plan volume <num>` | Plan volume outline |
| `story plan chapter <vol> <num>` | Plan chapter outline |
| `story write <num> --prompt` | Generate chapter prompt |
| `story verify <num>` | Verify chapter follows outline |
| `story archive <num>` | Archive completed chapter |
| `story export` | Export novel |
| `story publish check <platform>` | Check platform availability |
| `story publish status` | View publishing status |
| `story publish <chapter> <platform>` | Publish single chapter to platform |
| `story publish all <platform>` | Publish all unpublished chapters |
| `story github <subcommand>` | GitHub Issue management |

### Multi-Platform Publishing

Supports publishing archived chapters to multiple platforms:

```bash
# Check platform availability
story publish check feishu

# Publish single chapter
story publish 1 feishu

# Publish all chapters
story publish all feishu

# View publishing status
story publish status
```

**Supported Platforms:**
- Feishu Docs (feishu)
- Zhihu (zhihu) - reserved
- Qidian (qidian) - reserved

### Project Structure

```
Your Novel Project/
├── story.yaml                    # Config + overall progress
├── process/                      # Process management artifacts
│   ├── INFO/                     # Collected information
│   │   ├── 01-core.yaml          # Novel core info
│   │   ├── world/                # Worldbuilding settings
│   │   │   ├── basic.yaml
│   │   │   ├── factions/
│   │   │   ├── history.yaml
│   │   │   ├── powers/
│   │   │   ├── organizations/
│   │   │   └── locations/
│   │   └── characters/            # Character categories
│   │       ├── protagonist/       # Protagonist (full settings)
│   │       ├── main_cast/         # Main cast (full settings)
│   │       ├── supporting/      # Secondary characters (simplified)
│   │       └── guest/            # Extras (minimal)
│   ├── OUTLINE/                  # Outline drafts
│   │   ├── volume-001.yaml       # Volume outline
│   │   └── volume-001/           # Chapter outlines + snapshots
│   ├── PROMPTS/                  # Generated prompts
│   └── TEMPLATES/                # Prompt templates
└── output/                       # Final content
    ├── CONTENT/                  # Novel content
    ├── EXPORT/                   # Export files
    └── ARCHIVE/                  # Archived chapters
```

### Core Design Philosophy

#### 1. Main Agent + Sub-Agent Separation

- **Main Agent**: Talks to user, collects info, manages progress, generates prompts
- **Sub-Agent**: Only writes content based on complete prompts, no memory of previous conversation

#### 2. Layered Prompt Summarization

To avoid prompt truncation due to length, four priority layers:

- **L0 (Must-have)**: Chapter outline, task list, POV cognitive constraints
- **L1 (Very Important)**: Volume outline, protagonist settings, previous 3 chapter snapshots
- **L2 (Useful)**: Other supporting characters, minimal summary of chapters 4-10
- **L3 (Optional)**: Earlier chapters, worldbuilding details (load on demand)

#### 3. Six-Layer Character Cognitive Model

Each protagonist/main cast has complete six-layer cognition:

1. **Worldview** - How character sees the world
2. **Self-Definition** - Who character thinks they are
3. **Values** - What matters most to character
4. **Core Abilities** - Innate/mastered abilities
5. **Skills** - Learned skills
6. **Environment** - Character's current environment

#### 4. Plan One Volume, Write One Volume

No need to plan entire book at start; write Volume 1 first, then plan Volume 2.

### Differences from v1

my-novel-v2 is a complete rewrite of original my-novel-skill:

| Feature | v1 | v2 |
|---------|-----|-----|
| Architecture | Single Agent | Main Agent + Sub-Agent |
| Directories | Single mixed directory | Three separate directories (process/output/templates) |
| Data Format | JSON + Markdown | All YAML (JSON fallback) |
| Character System | Basic settings | Six-layer cognitive model |
| Prompts | Simple combination | Layered intelligent summarization |
| Creation Style | Plan all at once | Plan one volume, write one volume |
| Worldbuilding | Basic support | Complete framework |
| Verification | None | Chapter verification |
| Publishing | None | Multi-platform support |

### Development

```bash
# Run tests
python -c "from src_v2 import paths, init, status; print('OK')"

# View help
python story.py --help
```

### License

MIT License
