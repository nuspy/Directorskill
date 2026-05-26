"""Base class and data structures for Director sub-skills."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPServerConfig:
    """Configuration for starting an MCP server process.

    Attributes:
        command:  Executable to run (e.g. ``"python"`` or ``"uvx"``)
        args:     Arguments after the command
        env:      Additional environment variables (merged with os.environ)
        transport: ``"stdio"`` (default) or ``"sse"``
    """

    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    transport: str = "stdio"

    def to_mcp_json(self, server_name: str) -> dict:
        """Return an MCP client config dict for this server.

        Compatible with Claude Desktop / Cursor / VS Code MCP config format::

            {"mcpServers": {server_name: <this result>}}
        """
        return {
            "command": self.command,
            "args": self.args,
            "env": self.env,
        }


class SkillBase:
    """Abstract base for every Director sub-skill.

    Sub-classes must define the class-level attributes below and
    implement :meth:`get_mcp_config`.
    """

    SKILL_NAME: str = ""
    SKILL_VERSION: str = "0.0.0"
    DESCRIPTION: str = ""
    CAPABILITIES: list[str] = []
    TOOLS: list[dict[str, Any]] = []

    @classmethod
    def get_mcp_config(
        cls,
        install_dir: str | None = None,
        **env_overrides: str,
    ) -> MCPServerConfig:
        """Return the MCP server configuration for this skill.

        Args:
            install_dir:  Path where the skill repo is installed.
            **env_overrides: Extra environment variables (e.g. API keys).

        Returns:
            :class:`MCPServerConfig` ready to serialise into MCP client JSON.
        """
        raise NotImplementedError

    @classmethod
    def get_tool(cls, tool_name: str) -> dict[str, Any] | None:
        """Look up a tool by name from the skill's TOOLS manifest."""
        for tool in cls.TOOLS:
            if tool.get("name") == tool_name:
                return tool
        return None

    @classmethod
    def tools_by_category(cls) -> dict[str, list[dict]]:
        """Group TOOLS by their ``category`` field."""
        result: dict[str, list[dict]] = {}
        for tool in cls.TOOLS:
            cat = tool.get("category", "uncategorised")
            result.setdefault(cat, []).append(tool)
        return result
