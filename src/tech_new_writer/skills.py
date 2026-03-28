from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = PROJECT_ROOT / "src" / "tech_new_writer" / "skills"


def skill_path(skill_name: str) -> str:
    return str(Path.home() / ".agents" / "skills" / skill_name / "SKILL.md")


AGENT_SKILLS: dict[str, dict[str, object]] = {
    "trend_researcher": {
        "folder": str(SKILLS_ROOT / "trend_researcher"),
        "skills": [
            {
                "name": "persona-researcher",
                "source": "googleworkspace/cli@persona-researcher",
                "installed_path": skill_path("persona-researcher"),
                "purpose": "Organize research references, notes and collaboration workflows.",
            },
            {
                "name": "fact-checker",
                "source": "shubhamsaboo/awesome-llm-apps@fact-checker",
                "installed_path": skill_path("fact-checker"),
                "purpose": "Verify source credibility and validate claims from external publications.",
            },
        ],
    },
    "sme": {
        "folder": str(SKILLS_ROOT / "sme"),
        "skills": [
            {
                "name": "fact-checker",
                "source": "shubhamsaboo/awesome-llm-apps@fact-checker",
                "installed_path": skill_path("fact-checker"),
                "purpose": "Check technical claims, evidence quality and misleading statements.",
            },
        ],
    },
    "seo_specialist": {
        "folder": str(SKILLS_ROOT / "seo_specialist"),
        "skills": [
            {
                "name": "seo-audit",
                "source": "coreyhaines31/marketingskills@seo-audit",
                "installed_path": skill_path("seo-audit"),
                "purpose": "Provide SEO audit framework, on-page structure and search optimization guidance.",
            },
        ],
    },
    "content_writer": {
        "folder": str(SKILLS_ROOT / "content_writer"),
        "skills": [
            {
                "name": "technical-blog-writing",
                "source": "inferen-sh/skills@technical-blog-writing",
                "installed_path": skill_path("technical-blog-writing"),
                "purpose": "Guide high-quality developer-focused article structure and technical writing style.",
            },
        ],
    },
    "editor": {
        "folder": str(SKILLS_ROOT / "editor"),
        "skills": [
            {
                "name": "technical-blog-writing",
                "source": "inferen-sh/skills@technical-blog-writing",
                "installed_path": skill_path("technical-blog-writing"),
                "purpose": "Enforce strong structure, clarity, tone and developer-reader conventions.",
            },
            {
                "name": "fact-checker",
                "source": "shubhamsaboo/awesome-llm-apps@fact-checker",
                "installed_path": skill_path("fact-checker"),
                "purpose": "Re-check factual accuracy during final editorial pass.",
            },
        ],
    },
}


def build_skill_backstory(agent_key: str) -> str:
    agent_config = AGENT_SKILLS[agent_key]
    lines = [
        f"Agent skill folder: {agent_config['folder']}.",
        "Use the following curated skills as operating guidance when reasoning:",
    ]
    for skill in agent_config["skills"]:  # type: ignore[index]
        lines.append(
            f"- {skill['name']} ({skill['source']}): {skill['purpose']} "
            f"[installed at {skill['installed_path']}]"
        )
    return "\n".join(lines)
