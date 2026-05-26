"""Director Skill Registry.

All available sub-skills are imported and registered here.
The director uses this registry to discover capabilities and
route tasks to the correct MCP server.
"""

from .patreon import PatreonSkill

# Registry: skill_name -> skill class
SKILL_REGISTRY: dict = {
    PatreonSkill.SKILL_NAME: PatreonSkill,
}


def get_skill(name: str):
    """Return the skill class for the given name, or None."""
    return SKILL_REGISTRY.get(name)


def list_skills() -> list[dict]:
    """Return summary info for every registered skill."""
    return [
        {
            "name": cls.SKILL_NAME,
            "version": cls.SKILL_VERSION,
            "description": cls.DESCRIPTION,
            "capabilities": cls.CAPABILITIES,
            "tool_count": len(cls.TOOLS),
        }
        for cls in SKILL_REGISTRY.values()
    ]


__all__ = [
    "SKILL_REGISTRY",
    "PatreonSkill",
    "get_skill",
    "list_skills",
]
