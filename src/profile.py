"""User professional profile configuration for personalized content generation."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class UserProfile:
    """Professional profile configuration for content personalization.

    This profile helps tailor content to your expertise, positioning,
    and professional goals for maximum opportunity generation.
    """

    # Professional Identity
    name: str = "Your Name"
    target_role: str = "AI Consultant"  # AI Consultant, ML Engineer, AI Architect, etc.
    expertise_areas: List[str] = field(
        default_factory=lambda: ["Machine Learning", "Artificial Intelligence", "Deep Learning"]
    )

    # Professional Goals
    content_goals: List[str] = field(
        default_factory=lambda: [
            "opportunities",  # Attract freelance/job opportunities
            "credibility",  # Build professional credibility
            "visibility",  # Increase visibility in the field
        ]
    )

    # Geographic & Market
    region: str = "Europe"  # Europe, US, Asia, Global, etc.
    languages: List[str] = field(default_factory=lambda: ["English"])
    target_industries: List[str] = field(
        default_factory=lambda: ["Technology", "Finance", "Healthcare", "Consulting"]
    )

    # Portfolio & Experience
    github_username: str = ""  # Your GitHub username
    linkedin_url: str = ""  # Your LinkedIn profile URL
    portfolio_url: str = ""  # Personal website/portfolio
    kaggle_username: str = ""  # Your Kaggle username

    # Key Projects (to mention in content)
    notable_projects: List[Dict[str, str]] = field(
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
    primary_skills: List[str] = field(
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
    key_differentiators: List[str] = field(
        default_factory=lambda: [
            "Bridging research and production",
            "End-to-end AI implementation",
            "Business-focused technical expertise",
        ]
    )

    def to_dict(self) -> Dict[str, Any]:
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


def load_user_profile() -> UserProfile:
    """Load user profile from configuration.

    In future, this could load from a config file or database.
    For now, users should edit this file directly.
    """
    # TODO: Load from ~/.agentic-content/profile.yaml or similar
    return DEFAULT_PROFILE


def create_custom_profile(
    name: str, target_role: str, expertise_areas: List[str], **kwargs
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
