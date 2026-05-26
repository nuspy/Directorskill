# Director Skill

An **orchestration layer** that exposes multiple specialised sub-skills to AI
agents via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io).
Each sub-skill is an independent MCP server; the Director's skill registry
tells agents which capabilities are available and how to reach them.

---

## Architecture

```
 Agent (Hermes · OpenClaw · GPT-4 · Claude · Llama · Mistral …)
   │
   │  MCP protocol
   ├─────────────────────────────────────────────────────────┐
   │                                                         │
 Director Skill (this repo)                    Patreon Creator Skill
 ├── skills/__init__.py  (registry)            └── scripts/mcp_server.py
 ├── skills/base.py      (SkillBase)               52 tools:
 └── skills/patreon.py   (PatreonSkill)               campaign · members
                                                       content  · competitor
                                                       comments · rag
                                                       webhooks · reporting
```

The Director is **model-agnostic**: it never calls an LLM itself.  Tools that
require text generation return a `*_prompt` field — the agent passes it to its
own model and feeds the result back into the workflow.

---

## Registered Skills

| Skill | Version | Repo |
|-------|---------|------|
| `patreon-creator` | 1.0.0 | [nuspy/patreonskills](https://github.com/nuspy/patreonskills) |

---

## Patreon Creator Skill

### What it does

| Category | Highlights |
|----------|------------|
| **Campaign analytics** | MRR, patron count, tier breakdown, revenue forecast, growth strategy prompt |
| **Supporter analytics** | Demographics, churn risk, cohort retention, segments, LTV, language/geo distribution |
| **Content & posts** | AI draft prompt, media prompt, calendar prompt, publish via Playwright |
| **Competitor intel** | Scrape public pages, tier comparison, web/social search, strategy prompt |
| **Comment management** | Fetch, RAG-assisted response prompt, bulk auto-reply via Playwright |
| **Knowledge base** | ChromaDB RAG — index posts, add FAQs/brand-voice, semantic search |
| **Webhooks** | Full CRUD for Patreon event webhooks |
| **Reporting** | Monthly summary, member export, growth analysis, competitive benchmark, RSS trends |

### Prerequisites

- Python 3.11+
- A [Patreon Creator Access Token](https://www.patreon.com/portal/registration/register-clients)
- (Optional) Playwright Chromium — for `posts_publish_via_browser` and `comments_bulk_respond`

### Quick install

```bash
# 1. Clone the installer
curl -O https://raw.githubusercontent.com/nuspy/patreonskills/main/install.py

# 2. Run it
python install.py \
  --token pat_YOUR_TOKEN \
  --venv \
  --playwright \
  --client claude          # also: cursor | vscode (comma-separated)
```

The installer will:
- Clone `nuspy/patreonskills` into `~/patreon-skill`
- Create a virtualenv and install all dependencies
- Store credentials in `~/.patreon/credentials.json` (chmod 600)
- Write an `.env` file
- Patch the MCP client config (Claude Desktop / Cursor / VS Code)
- Run a live connection test

See [`install.py --help`](https://github.com/nuspy/patreonskills/blob/main/install.py) for all options.

---

## Using from the Director

### Query the skill registry

```python
from scripts.skills import list_skills, get_skill

# List all registered skills
for info in list_skills():
    print(info["name"], "—", info["description"])

# Look up a specific skill
Patreon = get_skill("patreon-creator")
print(Patreon.CAPABILITIES)
print(f"{len(Patreon.TOOLS)} tools available")
```

### Build the MCP server config

```python
from scripts.skills import get_skill

Patreon = get_skill("patreon-creator")

# Build MCP config (reads env vars automatically)
cfg = Patreon.get_mcp_config(
    install_dir="/opt/skills/patreon-skill",
    PATREON_ACCESS_TOKEN="pat_xxx",   # override / inject
)

print(cfg.command)   # "python"
print(cfg.args)      # ["/opt/skills/patreon-skill/scripts/mcp_server.py"]
print(cfg.env)       # {"PATREON_ACCESS_TOKEN": "pat_xxx"}

# Serialise for a Claude Desktop mcp config
import json
mcp_json = {"mcpServers": {"patreon-creator": cfg.to_mcp_json("patreon-creator")}}
print(json.dumps(mcp_json, indent=2))
```

### Inspect tools by category

```python
Patreon = get_skill("patreon-creator")

for category, tools in Patreon.tools_by_category().items():
    print(f"\n{category.upper()}")
    for t in tools:
        icon = "✏️ " if t.get("writes") else "📖"
        prompt = " [returns_prompt]" if t.get("returns_prompt") else ""
        print(f"  {icon} {t['name']}{prompt}")
```

Output (excerpt):
```
CAMPAIGN
  📖 campaign_get_overview
  📖 campaign_analyze_tiers
  📖 campaign_track_goals
  📖 campaign_revenue_breakdown
  📖 campaign_suggest_tier_optimization [returns_prompt]
  📖 campaign_generate_growth_strategy [returns_prompt]

CONTENT
  📖 posts_get_analytics
  📖 posts_generate_draft [returns_prompt]
  ✏️  posts_publish_via_browser
  …
```

### Trigger an install from the Director

```python
import subprocess
from scripts.skills import get_skill

Patreon = get_skill("patreon-creator")

cmd = Patreon.get_install_command(
    token="pat_xxx",
    extra_flags="--venv --playwright --client claude",
)
print(cmd)
# python install.py --token pat_xxx --venv --playwright --client claude

# Execute autonomously (e.g. from an agent action):
subprocess.run(cmd.split(), check=True)
```

---

## Model-Agnostic Prompt Flow

Tools that need LLM reasoning return a `*_prompt` field instead of calling
any model themselves.  The Director (or host agent) handles the generation
step with whatever model is configured:

```
1. Agent calls  →  posts_generate_draft(topic="...", tone="...", rag_query="...")
2. Tool returns →  {
     "rag_context": ["...previous post excerpts..."],
     "generation_prompt": "You are a Patreon creator...\n\n## Context\n{rag}\n\n## Task\nWrite a post about..."
   }
3. Agent sends  →  generation_prompt  →  own model (Hermes / GPT / Claude / Llama…)
4. Agent calls  →  posts_publish_via_browser(title="…", content="<model output>")
```

This pattern applies to all `[returns_prompt]` tools:

| Tool | Prompt field |
|------|--------------|
| `posts_generate_draft` | `generation_prompt` |
| `posts_generate_with_media` | `generation_prompt`, `image_prompts`, `video_script_prompt` |
| `posts_optimize_for_engagement` | `optimization_prompt` |
| `posts_suggest_content_calendar` | `calendar_prompt` |
| `campaign_suggest_tier_optimization` | `optimization_prompt` |
| `campaign_generate_growth_strategy` | `strategy_prompt` |
| `competitor_generate_strategy` | `strategy_prompt` |
| `comments_generate_response` | `response_prompt` |
| `comments_analyze_sentiment` | `sentiment_prompt` |
| `members_ai_insights` | `insights_prompt` |

---

## Environment Variables (Patreon Skill)

| Variable | Required | Description |
|----------|----------|-------------|
| `PATREON_ACCESS_TOKEN` | **Yes** | Creator Access Token |
| `LLM_BASE_URL` | No | Optional LLM endpoint for batch preprocessing |
| `LLM_MODEL` | No | Model identifier (e.g. `hermes3`, `gpt-4o`) |
| `LLM_API_KEY` | No | API key (empty for local Ollama) |
| `GOOGLE_SEARCH_API_KEY` | No | Google Custom Search API |
| `GOOGLE_SEARCH_CX` | No | Google Custom Search Engine ID |
| `BING_SEARCH_API_KEY` | No | Bing Web Search API |
| `PATREON_EMAIL` | No | For Playwright browser login |
| `PATREON_PASSWORD` | No | For Playwright browser login |
| `BROWSER_HEADLESS` | No | `true` / `false` (default `true`) |

---

## Adding New Skills

1. Create `scripts/skills/<skillname>.py` extending `SkillBase`
2. Define `SKILL_NAME`, `SKILL_VERSION`, `DESCRIPTION`, `CAPABILITIES`, `TOOLS`
3. Implement `get_mcp_config()`
4. Register in `scripts/skills/__init__.py`:
   ```python
   from .yourskill import YourSkill
   SKILL_REGISTRY[YourSkill.SKILL_NAME] = YourSkill
   ```

---

## License

MIT — see [LICENSE.txt](LICENSE.txt)
