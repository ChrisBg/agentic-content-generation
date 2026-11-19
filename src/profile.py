"""User professional profile configuration for B2B & scientific personal branding."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_BANNED_PHRASES: list[str] = [
    "navigating the next wave",
    "game-changing",
    "game changer",
    "unlock the power of",
    "in today's fast-paced world",
    "in the ever-evolving landscape",
    "revolutionizing",
    "are you ready for the",
    "let's dive in",
    "delve into",
    "in conclusion",
    "harness the power",
    "transformative potential",
    "the future is here",
    "dans un monde en constante évolution",
    "révolutionne le secteur",
    "plongeons ensemble",
    "prêt à débloquer",
]


@dataclass
class UserProfile:
    """Professional profile configuration for personalized B2B/R&D content generation."""

    # Professional Identity
    name: str = "Your Name"
    target_role: str = "Principal AI Engineer & Research Consultant"
    expertise_areas: list[str] = field(
        default_factory=lambda: ["Machine Learning", "Artificial Intelligence", "Deep Learning"]
    )

    # Professional Goals
    content_goals: list[str] = field(
        default_factory=lambda: [
            "opportunities",  # Attract B2B consulting / CIR-CII clients
            "credibility",  # Build scientific & engineering authority
            "visibility",  # Grow audience for digital assets
        ]
    )

    # B2B Positioning & Editorial Strategy (v2)
    editorial_pillars: list[str] = field(
        default_factory=lambda: [
            "Production AI & Agentic Systems (cost, latency, evaluation, MLOps)",
            "AdTech, MFA & Ad Fraud Detection at Scale",
            "Build in Public: Applied R&D, Active Research & Digital Assets",
        ]
    )
    target_personas: list[str] = field(
        default_factory=lambda: [
            "CTOs & VP Engineering",
            "VP Data / Head of AI",
            "CMOs & AdTech / MarTech Leaders",
            "Tech Founders & Product Leaders",
        ]
    )
    business_offers: list[str] = field(
        default_factory=lambda: [
            "Freelance AI Engineering & Architecture (CIR / CII eligible R&D)",
            "AdTech / Ad Fraud / Brand Safety AI Audits & Systems",
            "Digital Assets & Open-Source Benchmarks",
        ]
    )
    banned_phrases: list[str] = field(default_factory=lambda: list(DEFAULT_BANNED_PHRASES))

    # Geographic & Market
    region: str = "Europe"
    languages: list[str] = field(default_factory=lambda: ["French", "English"])
    target_industries: list[str] = field(
        default_factory=lambda: ["AdTech", "MarTech", "FinTech", "SaaS", "Media"]
    )

    # Portfolio & Experience
    github_username: str = ""
    linkedin_url: str = ""
    portfolio_url: str = ""
    kaggle_username: str = ""
    x_handle: str = ""
    youtube_channel: str = ""

    # Key Projects (to mention in content)
    notable_projects: list[dict[str, str]] = field(
        default_factory=lambda: [
            {
                "name": "Project Name",
                "description": "Brief description of what you built",
                "technologies": "PyTorch, FastAPI, Docker",
                "url": "https://github.com/username/project",
            }
        ]
    )

    # Technical Skills & Tools
    primary_skills: list[str] = field(
        default_factory=lambda: ["Python", "PyTorch", "HuggingFace", "LangGraph", "MLflow"]
    )

    # Content Preferences
    content_tone: str = "professional-conversational"
    use_emojis: bool = False  # Restrained by default to avoid AI-slop look
    posting_frequency: str = "2-3x per week"

    # Positioning
    unique_value_proposition: str = (
        "I help companies turn AI research into production-ready solutions"
    )
    key_differentiators: list[str] = field(
        default_factory=lambda: [
            "Bridging PhD-level research and production engineering",
            "End-to-end AI systems at ultra-low inference cost",
            "Proven business impact across AdTech and FinTech",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert profile to dictionary for YAML serialization and agent context."""
        return {
            "name": self.name,
            "target_role": self.target_role,
            "expertise_areas": self.expertise_areas,
            "content_goals": self.content_goals,
            "editorial_pillars": self.editorial_pillars,
            "target_personas": self.target_personas,
            "business_offers": self.business_offers,
            "banned_phrases": self.banned_phrases,
            "region": self.region,
            "languages": self.languages,
            "target_industries": self.target_industries,
            "github_username": self.github_username,
            "linkedin_url": self.linkedin_url,
            "portfolio_url": self.portfolio_url,
            "kaggle_username": self.kaggle_username,
            "x_handle": self.x_handle,
            "youtube_channel": self.youtube_channel,
            "notable_projects": self.notable_projects,
            "primary_skills": self.primary_skills,
            "content_tone": self.content_tone,
            "use_emojis": self.use_emojis,
            "posting_frequency": self.posting_frequency,
            "unique_value_proposition": self.unique_value_proposition,
            "key_differentiators": self.key_differentiators,
        }

    def get_profile_summary(self) -> str:
        """Generate a concise B2B/R&D profile summary for agent instructions."""
        expertise_str = ", ".join(self.expertise_areas)
        skills_str = ", ".join(self.primary_skills[:8])
        goals_str = ", ".join(self.content_goals)
        personas_str = ", ".join(self.target_personas)
        pillars_str = "\n  - ".join(self.editorial_pillars)
        offers_str = "\n  - ".join(self.business_offers)

        summary = f"""**Author Identity & Positioning**:
- Name: {self.name}
- Positioning: {self.target_role}
- Expertise: {expertise_str}
- Core Stack: {skills_str}
- Market / Region: {self.region} ({", ".join(self.languages)})
- Target Personas (NOT generic HR recruiters): {personas_str}
- Content Goals: {goals_str}
- Value Proposition: {self.unique_value_proposition}
- Tone: {self.content_tone} (emojis: {"minimal" if self.use_emojis else "none"})

**Editorial Pillars**:
  - {pillars_str}

**Offers / Strategic Angles (mention subtly only when relevant)**:
  - {offers_str}
"""

        if self.github_username:
            summary += f"\n- GitHub: https://github.com/{self.github_username}"
        if self.linkedin_url:
            summary += f"\n- LinkedIn: {self.linkedin_url}"
        if self.x_handle:
            summary += f"\n- X: https://x.com/{self.x_handle.lstrip('@')}"
        if self.youtube_channel:
            summary += f"\n- YouTube: {self.youtube_channel}"

        if self.notable_projects and self.notable_projects[0].get("name") != "Project Name":
            summary += "\n\n**Notable Projects**:\n"
            for project in self.notable_projects[:4]:
                summary += (
                    f"- {project['name']}: {project['description']} "
                    f"({project.get('technologies', '')})\n"
                )

        return summary

    def validate(self) -> dict[str, list[str]]:
        """Validate profile completeness and correctness."""
        errors: list[str] = []
        warnings: list[str] = []

        if self.name == "Your Name" or not self.name.strip():
            warnings.append("Name is not set. Please update 'name' field in profile.yaml")

        if not self.expertise_areas or (
            len(self.expertise_areas) == 3
            and self.expertise_areas[0] == "Machine Learning"
            and self.expertise_areas[1] == "Artificial Intelligence"
        ):
            warnings.append(
                "Using default expertise areas. Update 'expertise_areas' with your specific skills"
            )

        url_pattern = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if self.linkedin_url and not url_pattern.match(self.linkedin_url):
            errors.append(
                f"Invalid LinkedIn URL: '{self.linkedin_url}'. Must start with http:// or https://"
            )

        if self.portfolio_url and not url_pattern.match(self.portfolio_url):
            errors.append(
                f"Invalid portfolio URL: '{self.portfolio_url}'. Must start with http:// or https://"
            )

        if self.github_username and "/" in self.github_username:
            warnings.append(
                f"GitHub username should be just the username, not a URL: '{self.github_username}'"
            )

        if self.kaggle_username and "/" in self.kaggle_username:
            warnings.append(
                f"Kaggle username should be just the username, not a URL: '{self.kaggle_username}'"
            )

        valid_tones = ["professional-formal", "professional-conversational", "technical", "casual"]
        if self.content_tone not in valid_tones:
            errors.append(
                f"Invalid content_tone: '{self.content_tone}'. "
                f"Valid options: {', '.join(valid_tones)}"
            )

        valid_goals = [
            "opportunities",
            "credibility",
            "visibility",
            "thought-leadership",
            "networking",
        ]
        invalid_goals = [g for g in self.content_goals if g not in valid_goals]
        if invalid_goals:
            warnings.append(
                f"Unrecognized content goals: {', '.join(invalid_goals)}. "
                f"Valid options: {', '.join(valid_goals)}"
            )

        valid_frequencies = ["daily", "2-3x per week", "weekly", "biweekly", "monthly"]
        if self.posting_frequency not in valid_frequencies:
            warnings.append(
                f"Unrecognized posting frequency: '{self.posting_frequency}'. "
                f"Valid options: {', '.join(valid_frequencies)}"
            )

        if not self.expertise_areas:
            errors.append("'expertise_areas' cannot be empty. Add at least one area of expertise")

        if not self.primary_skills:
            warnings.append("'primary_skills' is empty. Consider adding your technical skills")

        if not self.target_industries:
            warnings.append("'target_industries' is empty. Consider adding target industries")

        for idx, project in enumerate(self.notable_projects):
            required_keys = ["name", "description", "technologies", "url"]
            missing_keys = [key for key in required_keys if key not in project]
            if missing_keys:
                warnings.append(f"Project {idx + 1} missing keys: {', '.join(missing_keys)}")
            if project.get("name") == "Project Name":
                warnings.append(
                    "Using default project placeholder. Update 'notable_projects' with your actual projects"
                )
                break

        if (
            self.unique_value_proposition
            == "I help companies turn AI research into production-ready solutions"
        ):
            warnings.append(
                "Using default value proposition. Update 'unique_value_proposition' with your unique offering"
            )

        return {"errors": errors, "warnings": warnings}


DEFAULT_PROFILE = UserProfile()

PROFILE_DIR = Path.home() / ".agentic-content-generation"
PROFILE_PATH = PROFILE_DIR / "profile.yaml"


def load_profile_from_yaml(path: Path) -> UserProfile:
    """Load user profile from YAML file."""
    if not path.exists():
        return DEFAULT_PROFILE

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data:
                return DEFAULT_PROFILE
            valid_keys = UserProfile.__annotations__.keys()
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            return UserProfile(**filtered_data)
    except Exception as e:
        print(f"Warning: Failed to load profile from {path}: {e}")
        return DEFAULT_PROFILE


def save_profile_to_yaml(profile: UserProfile, path: Path) -> None:
    """Save user profile to YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            profile.to_dict(), f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )


def load_user_profile(validate: bool = True) -> UserProfile:
    """Load user profile from configuration."""
    profile = load_profile_from_yaml(PROFILE_PATH) if PROFILE_PATH.exists() else DEFAULT_PROFILE

    if validate:
        validation = profile.validate()
        errors = validation["errors"]
        if errors:
            raise ValueError(f"Profile validation failed with {len(errors)} error(s): {errors}")

    return profile


def create_custom_profile(
    name: str, target_role: str, expertise_areas: list[str], **kwargs: Any
) -> UserProfile:
    """Create a custom user profile."""
    return UserProfile(
        name=name, target_role=target_role, expertise_areas=expertise_areas, **kwargs
    )
