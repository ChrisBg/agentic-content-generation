"""User professional profile configuration for personalized content generation."""

import re
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

    def validate(self) -> dict[str, list[str]]:
        """Validate profile completeness and correctness.

        Returns:
            Dictionary with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []

        # Validate required fields
        if self.name == "Your Name" or not self.name.strip():
            warnings.append("⚠️  Name is not set. Please update 'name' field in profile.yaml")

        if not self.expertise_areas or (
            len(self.expertise_areas) == 3
            and self.expertise_areas[0] == "Machine Learning"
            and self.expertise_areas[1] == "Artificial Intelligence"
        ):
            warnings.append(
                "⚠️  Using default expertise areas. Update 'expertise_areas' with your specific skills"
            )

        # Validate URLs
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if self.linkedin_url and not url_pattern.match(self.linkedin_url):
            errors.append(
                f"❌ Invalid LinkedIn URL: '{self.linkedin_url}'. Must start with http:// or https://"
            )

        if self.portfolio_url and not url_pattern.match(self.portfolio_url):
            errors.append(
                f"❌ Invalid portfolio URL: '{self.portfolio_url}'. Must start with http:// or https://"
            )

        # Validate GitHub username (no special URL validation, just username)
        if self.github_username and "/" in self.github_username:
            warnings.append(
                f"⚠️  GitHub username should be just the username, not a URL: '{self.github_username}'"
            )

        # Validate Kaggle username
        if self.kaggle_username and "/" in self.kaggle_username:
            warnings.append(
                f"⚠️  Kaggle username should be just the username, not a URL: '{self.kaggle_username}'"
            )

        # Validate content_tone enum
        valid_tones = ["professional-formal", "professional-conversational", "technical", "casual"]
        if self.content_tone not in valid_tones:
            errors.append(
                f"❌ Invalid content_tone: '{self.content_tone}'. "
                f"Valid options: {', '.join(valid_tones)}"
            )

        # Validate content_goals
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
                f"⚠️  Unrecognized content goals: {', '.join(invalid_goals)}. "
                f"Valid options: {', '.join(valid_goals)}"
            )

        # Validate posting_frequency
        valid_frequencies = ["daily", "2-3x per week", "weekly", "biweekly", "monthly"]
        if self.posting_frequency not in valid_frequencies:
            warnings.append(
                f"⚠️  Unrecognized posting frequency: '{self.posting_frequency}'. "
                f"Valid options: {', '.join(valid_frequencies)}"
            )

        # Validate lists are not empty
        if not self.expertise_areas:
            errors.append(
                "❌ 'expertise_areas' cannot be empty. Add at least one area of expertise"
            )

        if not self.primary_skills:
            warnings.append("⚠️  'primary_skills' is empty. Consider adding your technical skills")

        if not self.target_industries:
            warnings.append("⚠️  'target_industries' is empty. Consider adding target industries")

        # Validate notable_projects structure
        for idx, project in enumerate(self.notable_projects):
            required_keys = ["name", "description", "technologies", "url"]
            missing_keys = [key for key in required_keys if key not in project]
            if missing_keys:
                warnings.append(f"⚠️  Project {idx + 1} missing keys: {', '.join(missing_keys)}")

            # Check if still using default project
            if project.get("name") == "Project Name":
                warnings.append(
                    "⚠️  Using default project placeholder. Update 'notable_projects' with your actual projects"
                )
                break  # Only warn once

        # Validate unique_value_proposition
        if (
            self.unique_value_proposition
            == "I help companies turn AI research into production-ready solutions"
        ):
            warnings.append(
                "⚠️  Using default value proposition. Update 'unique_value_proposition' with your unique offering"
            )

        return {"errors": errors, "warnings": warnings}


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


def load_user_profile(validate: bool = True) -> UserProfile:
    """Load user profile from configuration.

    Checks ~/.agentic-content-generation/profile.yaml first.
    Falls back to default profile if not found.

    Args:
        validate: Whether to run validation and display warnings/errors

    Returns:
        UserProfile instance
    """
    if PROFILE_PATH.exists():
        print(f"👤 Loading profile from {PROFILE_PATH}")
        profile = load_profile_from_yaml(PROFILE_PATH)
    else:
        print("👤 Using default profile (no custom profile found)")
        print(f"💡 Run with --init-profile to create one at {PROFILE_PATH}")
        profile = DEFAULT_PROFILE

    # Validate profile if requested
    if validate:
        validation = profile.validate()
        errors = validation["errors"]
        warnings = validation["warnings"]

        if errors:
            print("\n❌ Profile Validation Errors:")
            for error in errors:
                print(f"   {error}")
            print("\n⚠️  Please fix these errors in your profile.yaml before continuing.\n")
            raise ValueError(f"Profile validation failed with {len(errors)} error(s)")

        if warnings:
            print("\n📋 Profile Validation Warnings:")
            for warning in warnings:
                print(f"   {warning}")
            print()

    return profile


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
