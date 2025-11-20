"""User professional profile configuration for personalized content generation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class UserProfile:
    """Professional profile configuration for content personalization.

    This profile helps tailor content to your expertise, positioning,
    and professional goals for maximum opportunity generation.
    """

    # Professional Identity
    name: str = "Your Name"
    target_role: str = "AI Consultant"  # AI Consultant, ML Engineer, AI Architect, etc.
    expertise_areas: list[str] = field(
        default_factory=lambda: ["Machine Learning", "Artificial Intelligence", "Deep Learning"]
    )

    # Professional Goals
    content_goals: list[str] = field(
        default_factory=lambda: [
            "opportunities",  # Attract freelance/job opportunities
            "credibility",  # Build professional credibility
            "visibility",  # Increase visibility in the field
        ]
    )

    # Geographic & Market
    region: str = "Europe"  # Europe, US, Asia, Global, etc.
    languages: list[str] = field(default_factory=lambda: ["English"])
    target_industries: list[str] = field(
        default_factory=lambda: ["Technology", "Finance", "Healthcare", "Consulting"]
    )

    # Portfolio & Experience
    github_username: str = ""  # Your GitHub username
    linkedin_url: str = ""  # Your LinkedIn profile URL
    portfolio_url: str = ""  # Personal website/portfolio
    kaggle_username: str = ""  # Your Kaggle username

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
        default_factory=lambda: ["Python", "PyTorch", "TensorFlow", "Scikit-learn", "MLflow"]
    )

    # Content Preferences
    content_tone: str = (
        "professional-conversational"  # professional-formal, professional-conversational, technical
    )
    use_emojis: bool = True  # Use emojis in LinkedIn posts
    posting_frequency: str = "2-3x per week"  # daily, 2-3x per week, weekly

    # SEO & Positioning
    unique_value_proposition: str = (
        "I help companies turn AI research into production-ready solutions"
    )
    key_differentiators: list[str] = field(
        default_factory=lambda: [
            "Bridging research and production",
            "End-to-end AI implementation",
            "Business-focused technical expertise",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert profile to dictionary for agent context."""
        return {
            "name": self.name,
            "target_role": self.target_role,
            "expertise_areas": self.expertise_areas,
            "content_goals": self.content_goals,
            "region": self.region,
            "languages": self.languages,
            "target_industries": self.target_industries,
            "github_username": self.github_username,
            "linkedin_url": self.linkedin_url,
            "portfolio_url": self.portfolio_url,
            "kaggle_username": self.kaggle_username,
            "notable_projects": self.notable_projects,
            "primary_skills": self.primary_skills,
            "content_tone": self.content_tone,
            "use_emojis": self.use_emojis,
            "posting_frequency": self.posting_frequency,
            "unique_value_proposition": self.unique_value_proposition,
            "key_differentiators": self.key_differentiators,
        }

    def get_profile_summary(self) -> str:
        """Generate a text summary of the profile for agent instructions."""
        expertise_str = ", ".join(self.expertise_areas)
        skills_str = ", ".join(self.primary_skills[:5])
        goals_str = ", ".join(self.content_goals)

        summary = f"""
**Professional Profile**:
- Role: {self.target_role}
- Expertise: {expertise_str}
- Key Skills: {skills_str}
- Region: {self.region}
- Content Goals: {goals_str}
- Value Proposition: {self.unique_value_proposition}
- Tone: {self.content_tone}
"""

        if self.github_username:
            summary += f"- GitHub: github.com/{self.github_username}\n"
        if self.linkedin_url:
            summary += f"- LinkedIn: {self.linkedin_url}\n"

        if self.notable_projects and self.notable_projects[0]["name"] != "Project Name":
            summary += "\n**Notable Projects to Mention**:\n"
            for project in self.notable_projects[:3]:
                summary += (
                    f"- {project['name']}: {project['description']} ({project['technologies']})\n"
                )

        return summary


# Default profile (users should customize this)
DEFAULT_PROFILE = UserProfile()

# Path to user profile configuration
PROFILE_DIR = Path.home() / ".agentic-content-generation"
PROFILE_PATH = PROFILE_DIR / "profile.yaml"


def load_profile_from_yaml(path: Path) -> UserProfile:
    """Load user profile from YAML file.

    Args:
        path: Path to the YAML file

    Returns:
        UserProfile instance
    """
    if not path.exists():
        return DEFAULT_PROFILE

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data:
                return DEFAULT_PROFILE
            # Filter out any keys that don't exist in UserProfile
            valid_keys = UserProfile.__annotations__.keys()
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            return UserProfile(**filtered_data)
    except Exception as e:
        print(f"Warning: Failed to load profile from {path}: {e}")
        return DEFAULT_PROFILE


def save_profile_to_yaml(profile: UserProfile, path: Path) -> None:
    """Save user profile to YAML file.

    Args:
        profile: UserProfile instance
        path: Path to save the YAML file
    """
    # Create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(profile.to_dict(), f, default_flow_style=False, sort_keys=False)


def load_user_profile() -> UserProfile:
    """Load user profile from configuration.

    Checks ~/.agentic-content-generation/profile.yaml first.
    Falls back to default profile if not found.
    """
    if PROFILE_PATH.exists():
        print(f"👤 Loading profile from {PROFILE_PATH}")
        return load_profile_from_yaml(PROFILE_PATH)

    print("👤 Using default profile (no custom profile found)")
    return DEFAULT_PROFILE


def create_custom_profile(
    name: str, target_role: str, expertise_areas: list[str], **kwargs
) -> UserProfile:
    """Create a custom user profile.

    Args:
        name: Your name
        target_role: Target professional role
        expertise_areas: List of expertise areas
        **kwargs: Additional profile fields

    Returns:
        UserProfile instance
    """
    return UserProfile(
        name=name, target_role=target_role, expertise_areas=expertise_areas, **kwargs
    )
