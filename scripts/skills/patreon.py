"""Patreon Creator Skill — Director adapter.

This module registers the ``patreon-creator`` MCP server as a
first-class sub-skill of the Director.  It provides:

- :data:`PatreonSkill.TOOLS`       — full manifest of all 52 MCP tools
- :meth:`PatreonSkill.get_mcp_config` — builds the ``MCPServerConfig``
  that tells the Director how to spawn / connect to the server
- Capability tags the Director uses for task routing

Design note — model-agnostic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The Patreon skill never calls an LLM on its own.  Every tool that
needs text generation returns a ``*_prompt`` field containing a
fully-populated prompt template.  The Director (or its host agent)
passes that prompt to **its own** model and feeds the result back
into the workflow.
"""

from __future__ import annotations

import os
from pathlib import Path

from .base import MCPServerConfig, SkillBase


class PatreonSkill(SkillBase):
    """Director sub-skill: Patreon Creator MCP server."""

    SKILL_NAME = "patreon-creator"
    SKILL_VERSION = "1.0.0"
    DESCRIPTION = (
        "Manage a Patreon creator page: analytics, supporter insights, "
        "competitor intelligence, AI-assisted content drafting, automated "
        "post publishing, comment management with RAG, and reporting."
    )
    CAPABILITIES = [
        "patreon:campaign_analytics",
        "patreon:supporter_analytics",
        "patreon:content_generation",
        "patreon:post_publishing",
        "patreon:competitor_intelligence",
        "patreon:comment_management",
        "patreon:rag_knowledge_base",
        "patreon:webhooks",
        "patreon:reporting",
    ]

    # ------------------------------------------------------------------ #
    # Full tool manifest — 52 tools                                        #
    # ------------------------------------------------------------------ #
    TOOLS = [
        # ── Auth & Setup ──────────────────────────────────────────────── #
        {
            "name": "patreon_authenticate",
            "category": "auth",
            "description": "Run OAuth2 flow or set a Creator Access Token.",
            "writes": False,
        },
        {
            "name": "patreon_get_identity",
            "category": "auth",
            "description": "Return authenticated user info (name, email, url).",
            "writes": False,
        },
        {
            "name": "patreon_check_connection",
            "category": "auth",
            "description": "Verify API connectivity and token validity.",
            "writes": False,
        },
        # ── Campaign Intelligence ─────────────────────────────────────── #
        {
            "name": "campaign_get_overview",
            "category": "campaign",
            "description": "Return MRR, patron count, and goal progress.",
            "writes": False,
        },
        {
            "name": "campaign_analyze_tiers",
            "category": "campaign",
            "description": "Break down member distribution and revenue by tier.",
            "writes": False,
        },
        {
            "name": "campaign_track_goals",
            "category": "campaign",
            "description": "Show goal progress with ETA forecasts.",
            "writes": False,
        },
        {
            "name": "campaign_revenue_breakdown",
            "category": "campaign",
            "description": "Detailed MRR breakdown, growth rate, projections.",
            "writes": False,
        },
        {
            "name": "campaign_suggest_tier_optimization",
            "category": "campaign",
            "description": "Return tier data + structured prompt for pricing advice (agent uses own model).",
            "writes": False,
            "returns_prompt": True,
            "prompt_field": "optimization_prompt",
        },
        {
            "name": "campaign_generate_growth_strategy",
            "category": "campaign",
            "description": "Return campaign data + structured prompt for growth strategy (agent uses own model).",
            "writes": False,
            "returns_prompt": True,
            "prompt_field": "strategy_prompt",
        },
        # ── Supporter Analytics ───────────────────────────────────────── #
        {
            "name": "members_fetch_all",
            "category": "members",
            "description": "Paginated list of all members with optional filters.",
            "writes": False,
        },
        {
            "name": "members_analyze_demographics",
            "category": "members",
            "description": "Tier distribution, tenure, LTV, and aggregate stats.",
            "writes": False,
        },
        {
            "name": "members_detect_churn_risk",
            "category": "members",
            "description": "Identify supporters at risk of cancellation.",
            "writes": False,
        },
        {
            "name": "members_cohort_analysis",
            "category": "members",
            "description": "Retention analysis grouped by join cohort.",
            "writes": False,
        },
        {
            "name": "members_segment",
            "category": "members",
            "description": "Segment supporters by tier, tenure, engagement, or region.",
            "writes": False,
        },
        {
            "name": "members_get_top_supporters",
            "category": "members",
            "description": "Top patrons ranked by value or seniority.",
            "writes": False,
        },
        {
            "name": "members_language_analysis",
            "category": "members",
            "description": "Inferred language distribution across the supporter base.",
            "writes": False,
        },
        {
            "name": "members_geographic_analysis",
            "category": "members",
            "description": "Estimated geographic distribution of supporters.",
            "writes": False,
        },
        {
            "name": "members_recent_activity",
            "category": "members",
            "description": "New joins, upgrades, and cancellations in the last N days.",
            "writes": False,
        },
        {
            "name": "members_ai_insights",
            "category": "members",
            "description": "Return supporter data + structured prompt for narrative insights (agent uses own model).",
            "writes": False,
            "returns_prompt": True,
            "prompt_field": "insights_prompt",
        },
        # ── Content & Posts ───────────────────────────────────────────── #
        {
            "name": "posts_get_analytics",
            "category": "content",
            "description": "Post performance: type, frequency, engagement data.",
            "writes": False,
        },
        {
            "name": "posts_fetch_content",
            "category": "content",
            "description": "Retrieve post body for reference or indexing.",
            "writes": False,
        },
        {
            "name": "posts_generate_draft",
            "category": "content",
            "description": "Return topic + RAG context as structured generation_prompt (agent uses own model).",
            "writes": False,
            "returns_prompt": True,
            "prompt_field": "generation_prompt",
        },
        {
            "name": "posts_generate_with_media",
            "category": "content",
            "description": "Draft prompt + image_prompts list + video_script_prompt.",
            "writes": False,
            "returns_prompt": True,
            "prompt_field": "generation_prompt",
        },
        {
            "name": "posts_optimize_for_engagement",
            "category": "content",
            "description": "Return post content + optimisation context for agent model.",
            "writes": False,
            "returns_prompt": True,
            "prompt_field": "optimization_prompt",
        },
        {
            "name": "posts_suggest_content_calendar",
            "category": "content",
            "description": "Return posting history + calendar_prompt for agent model.",
            "writes": False,
            "returns_prompt": True,
            "prompt_field": "calendar_prompt",
        },
        {
            "name": "posts_draft_and_review",
            "category": "content",
            "description": "Prepare full post preview (title, body, tier, schedule).",
            "writes": False,
        },
        {
            "name": "posts_publish_via_browser",
            "category": "content",
            "description": "Publish a post to Patreon via Playwright browser automation.",
            "writes": True,
            "requires": ["playwright"],
        },
        # ── Competitor Intelligence ───────────────────────────────────── #
        {
            "name": "competitor_analyze_patreon_page",
            "category": "competitor",
            "description": "Scrape a public Patreon page: tiers, prices, recent posts.",
            "writes": False,
        },
        {
            "name": "competitor_compare_tiers",
            "category": "competitor",
            "description": "Side-by-side comparison of your tiers vs a competitor.",
            "writes": False,
        },
        {
            "name": "competitor_track_posting_frequency",
            "category": "competitor",
            "description": "Analyse a competitor's publication cadence.",
            "writes": False,
        },
        {
            "name": "competitor_search_web",
            "category": "competitor",
            "description": "Google/Bing search for competitor news and content.",
            "writes": False,
        },
        {
            "name": "competitor_monitor_social",
            "category": "competitor",
            "description": "Twitter/Reddit/YouTube trend monitoring for the niche.",
            "writes": False,
        },
        {
            "name": "competitor_generate_strategy",
            "category": "competitor",
            "description": "Aggregate competitor data + strategy_prompt for agent model.",
            "writes": False,
            "returns_prompt": True,
            "prompt_field": "strategy_prompt",
        },
        # ── Comment Management ────────────────────────────────────────── #
        {
            "name": "comments_fetch_recent",
            "category": "comments",
            "description": "Retrieve recent comments from posts via scraping.",
            "writes": False,
        },
        {
            "name": "comments_generate_response",
            "category": "comments",
            "description": "RAG context retrieval + response_prompt for agent model.",
            "writes": False,
            "returns_prompt": True,
            "prompt_field": "response_prompt",
        },
        {
            "name": "comments_bulk_respond",
            "category": "comments",
            "description": "Post batch replies via Playwright (text provided by agent).",
            "writes": True,
            "requires": ["playwright"],
        },
        {
            "name": "comments_analyze_sentiment",
            "category": "comments",
            "description": "Return comments + sentiment_prompt for agent model.",
            "writes": False,
            "returns_prompt": True,
            "prompt_field": "sentiment_prompt",
        },
        # ── Knowledge Base / RAG ──────────────────────────────────────── #
        {
            "name": "kb_index_campaign",
            "category": "rag",
            "description": "Index all campaign posts into ChromaDB.",
            "writes": True,
        },
        {
            "name": "kb_add_document",
            "category": "rag",
            "description": "Add FAQ, brand-voice doc, or custom document to the KB.",
            "writes": True,
        },
        {
            "name": "kb_search",
            "category": "rag",
            "description": "Semantic search across the knowledge base.",
            "writes": False,
        },
        {
            "name": "kb_list_documents",
            "category": "rag",
            "description": "List all indexed documents.",
            "writes": False,
        },
        {
            "name": "kb_delete_document",
            "category": "rag",
            "description": "Remove a document from the knowledge base.",
            "writes": True,
        },
        # ── Webhook Management ────────────────────────────────────────── #
        {
            "name": "webhooks_list",
            "category": "webhooks",
            "description": "List active Patreon webhooks.",
            "writes": False,
        },
        {
            "name": "webhooks_create",
            "category": "webhooks",
            "description": "Register a new webhook (members/posts events).",
            "writes": True,
        },
        {
            "name": "webhooks_update",
            "category": "webhooks",
            "description": "Update webhook URL or trigger events.",
            "writes": True,
        },
        {
            "name": "webhooks_delete",
            "category": "webhooks",
            "description": "Delete a webhook.",
            "writes": True,
        },
        # ── Reporting ─────────────────────────────────────────────────── #
        {
            "name": "report_monthly_summary",
            "category": "reporting",
            "description": "Full monthly report: growth, revenue, content performance.",
            "writes": False,
        },
        {
            "name": "report_export_members",
            "category": "reporting",
            "description": "Export member list as CSV or JSON.",
            "writes": False,
        },
        {
            "name": "report_growth_analysis",
            "category": "reporting",
            "description": "Growth metrics over time with trend analysis.",
            "writes": False,
        },
        {
            "name": "report_revenue_forecast",
            "category": "reporting",
            "description": "Revenue projection for next 3–6 months.",
            "writes": False,
        },
        {
            "name": "report_competitive_benchmark",
            "category": "reporting",
            "description": "Benchmark your metrics against analysed competitors.",
            "writes": False,
        },
        {
            "name": "monitor_rss_trends",
            "category": "reporting",
            "description": "Monitor RSS feeds for niche trends.",
            "writes": False,
        },
    ]

    # ------------------------------------------------------------------ #
    # MCP server configuration                                            #
    # ------------------------------------------------------------------ #

    @classmethod
    def get_mcp_config(
        cls,
        install_dir: str | None = None,
        **env_overrides: str,
    ) -> MCPServerConfig:
        """Build the MCP server config for the Patreon Creator skill.

        Args:
            install_dir:  Directory where ``nuspy/patreonskills`` is cloned.
                          Defaults to ``~/patreon-skill``.
            **env_overrides: Any env vars to inject (e.g.
                ``PATREON_ACCESS_TOKEN="pat_…"``).

        Returns:
            :class:`MCPServerConfig` ready to serialise into MCP client JSON.

        Example::

            cfg = PatreonSkill.get_mcp_config(
                install_dir="/opt/skills/patreon-skill",
                PATREON_ACCESS_TOKEN="pat_xxx",
            )
            # → MCPServerConfig(
            #     command="python",
            #     args=["/opt/skills/patreon-skill/scripts/mcp_server.py"],
            #     env={"PATREON_ACCESS_TOKEN": "pat_xxx"},
            # )
        """
        if install_dir is None:
            install_dir = str(Path.home() / "patreon-skill")

        server_script = str(Path(install_dir) / "scripts" / "mcp_server.py")

        # Collect env: start from os.environ, then apply overrides
        env: dict[str, str] = {}
        for key in (
            "PATREON_ACCESS_TOKEN",
            "LLM_BASE_URL",
            "LLM_MODEL",
            "LLM_API_KEY",
            "GOOGLE_SEARCH_API_KEY",
            "GOOGLE_SEARCH_CX",
            "BING_SEARCH_API_KEY",
            "PATREON_EMAIL",
            "PATREON_PASSWORD",
            "BROWSER_HEADLESS",
            "KNOWLEDGE_BASE_PATH",
            "BROWSER_SESSION_PATH",
        ):
            val = os.environ.get(key, "").strip()
            if val:
                env[key] = val

        # Apply any explicit overrides
        env.update({k: v for k, v in env_overrides.items() if v})

        # Determine Python executable (prefer venv if present)
        venv_python = Path(install_dir) / ".venv" / "bin" / "python"
        python_cmd = str(venv_python) if venv_python.exists() else "python"

        return MCPServerConfig(
            command=python_cmd,
            args=[server_script],
            env=env,
        )

    @classmethod
    def get_install_command(cls, token: str = "", extra_flags: str = "") -> str:
        """Return the one-liner install command for this skill.

        Args:
            token:       Creator Access Token to embed (optional).
            extra_flags: Additional flags to append (e.g. ``"--venv --playwright"``).

        Returns:
            A shell command string the Director can hand off to the user
            or execute in a subprocess.

        Example::

            cmd = PatreonSkill.get_install_command(
                token="pat_xxx",
                extra_flags="--venv --playwright --client claude",
            )
            # → "python install.py --token pat_xxx --venv --playwright --client claude"
        """
        base = "python install.py"
        if token:
            base += f" --token {token}"
        if extra_flags:
            base += f" {extra_flags.strip()}"
        return base

    @classmethod
    def get_repo_url(cls) -> str:
        """Return the canonical GitHub URL for this skill."""
        return "https://github.com/nuspy/patreonskills"

    @classmethod
    def read_only_tools(cls) -> list[dict]:
        """Return tools that only read data (safe to call without confirmation)."""
        return [t for t in cls.TOOLS if not t.get("writes", False)]

    @classmethod
    def write_tools(cls) -> list[dict]:
        """Return tools that perform write actions (publish, comment, etc.)."""
        return [t for t in cls.TOOLS if t.get("writes", False)]

    @classmethod
    def prompt_returning_tools(cls) -> list[dict]:
        """Return tools that include a ``*_prompt`` field for the agent's model."""
        return [t for t in cls.TOOLS if t.get("returns_prompt", False)]
