"""Tests for user profile functionality."""

import pytest

from src.profile import (
    UserProfile,
    load_profile_from_yaml,
    load_user_profile,
    save_profile_to_yaml,
)


class TestUserProfileValidation:
    """Test profile validation logic."""

    def test_valid_profile_passes_validation(self, valid_profile):
        """Test that a valid profile passes validation without errors."""
        result = valid_profile.validate()
        assert result["errors"] == []
        # May have warnings for default values, but no errors

    def test_default_profile_has_warnings(self, default_profile):
        """Test that default profile generates warnings."""
        result = default_profile.validate()
        assert len(result["warnings"]) > 0
        # Should warn about default name, expertise, etc.
        warning_text = " ".join(result["warnings"])
        assert "Name is not set" in warning_text or "Your Name" in warning_text

    def test_empty_name_generates_warning(self):
        """Test that empty name generates a warning."""
        profile = UserProfile(name="", expertise_areas=["ML"])
        result = profile.validate()
        assert any("name" in w.lower() for w in result["warnings"])

    def test_invalid_linkedin_url_generates_error(self):
        """Test that invalid LinkedIn URL generates an error."""
        profile = UserProfile(
            name="Test",
            expertise_areas=["ML"],
            linkedin_url="not-a-url",
        )
        result = profile.validate()
        assert any("linkedin" in e.lower() for e in result["errors"])

    def test_invalid_portfolio_url_generates_error(self):
        """Test that invalid portfolio URL generates an error."""
        profile = UserProfile(
            name="Test",
            expertise_areas=["ML"],
            portfolio_url="invalid-url",
        )
        result = profile.validate()
        assert any("portfolio" in e.lower() for e in result["errors"])

    def test_github_username_with_slash_generates_warning(self):
        """Test that GitHub username with slashes generates a warning."""
        profile = UserProfile(
            name="Test",
            expertise_areas=["ML"],
            github_username="user/repo",
        )
        result = profile.validate()
        assert any("github" in w.lower() for w in result["warnings"])

    def test_invalid_content_tone_generates_error(self):
        """Test that invalid content tone generates an error."""
        profile = UserProfile(
            name="Test",
            expertise_areas=["ML"],
            content_tone="invalid-tone",
        )
        result = profile.validate()
        assert any("content_tone" in e for e in result["errors"])

    def test_valid_content_tones_pass(self):
        """Test that all valid content tones pass validation."""
        valid_tones = ["professional-formal", "professional-conversational", "technical", "casual"]
        for tone in valid_tones:
            profile = UserProfile(
                name="Test",
                expertise_areas=["ML"],
                content_tone=tone,
            )
            result = profile.validate()
            assert not any("content_tone" in e for e in result["errors"])

    def test_empty_expertise_areas_generates_error(self):
        """Test that empty expertise areas generates an error."""
        profile = UserProfile(name="Test", expertise_areas=[])
        result = profile.validate()
        assert any("expertise_areas" in e for e in result["errors"])

    def test_invalid_content_goals_generate_warning(self):
        """Test that invalid content goals generate warnings."""
        profile = UserProfile(
            name="Test",
            expertise_areas=["ML"],
            content_goals=["invalid-goal"],
        )
        result = profile.validate()
        assert any("content goals" in w.lower() for w in result["warnings"])

    def test_valid_urls_pass_validation(self, valid_profile):
        """Test that valid URLs pass validation."""
        result = valid_profile.validate()
        # Should not have URL-related errors
        assert not any("url" in e.lower() for e in result["errors"])


class TestProfileSerialization:
    """Test profile serialization to/from YAML."""

    def test_save_and_load_profile(self, valid_profile, temp_dir):
        """Test saving and loading a profile."""
        yaml_path = temp_dir / "test_profile.yaml"

        # Save profile
        save_profile_to_yaml(valid_profile, yaml_path)
        assert yaml_path.exists()

        # Load profile
        loaded_profile = load_profile_from_yaml(yaml_path)

        # Verify all fields match
        assert loaded_profile.name == valid_profile.name
        assert loaded_profile.target_role == valid_profile.target_role
        assert loaded_profile.expertise_areas == valid_profile.expertise_areas
        assert loaded_profile.linkedin_url == valid_profile.linkedin_url
        assert loaded_profile.github_username == valid_profile.github_username

    def test_load_nonexistent_profile_returns_default(self, temp_dir):
        """Test loading a nonexistent profile returns default."""
        yaml_path = temp_dir / "nonexistent.yaml"
        profile = load_profile_from_yaml(yaml_path)

        # Should return default profile
        assert profile.name == "Your Name"

    def test_load_invalid_yaml_returns_default(self, temp_dir):
        """Test loading invalid YAML returns default profile."""
        yaml_path = temp_dir / "invalid.yaml"
        yaml_path.write_text("{ invalid yaml content ][")

        profile = load_profile_from_yaml(yaml_path)

        # Should return default profile
        assert profile.name == "Your Name"

    def test_save_creates_directory(self, temp_dir):
        """Test that save creates parent directory if it doesn't exist."""
        yaml_path = temp_dir / "subdir" / "profile.yaml"
        profile = UserProfile(name="Test")

        save_profile_to_yaml(profile, yaml_path)

        assert yaml_path.exists()
        assert yaml_path.parent.exists()


class TestProfileLoading:
    """Test profile loading with validation."""

    def test_load_user_profile_with_validation(self, mock_profile_dir, valid_profile):
        """Test loading user profile with validation enabled."""
        from src.profile import PROFILE_PATH

        # Save a valid profile
        save_profile_to_yaml(valid_profile, PROFILE_PATH)

        # Load with validation
        loaded = load_user_profile(validate=True)

        assert loaded.name == valid_profile.name

    def test_load_user_profile_without_validation(self, mock_profile_dir, default_profile):
        """Test loading profile without validation (no warnings)."""
        from src.profile import PROFILE_PATH

        # Save default profile (has warnings)
        save_profile_to_yaml(default_profile, PROFILE_PATH)

        # Load without validation - should not raise
        loaded = load_user_profile(validate=False)

        assert loaded.name == "Your Name"

    def test_load_user_profile_with_errors_raises(self, mock_profile_dir):
        """Test that loading profile with errors raises ValueError."""
        from src.profile import PROFILE_PATH

        # Create profile with validation errors
        invalid = UserProfile(
            name="Test",
            expertise_areas=[],  # Empty - generates error
            content_tone="invalid",  # Invalid tone - generates error
        )
        save_profile_to_yaml(invalid, PROFILE_PATH)

        # Load with validation - should raise
        with pytest.raises(ValueError, match="validation failed"):
            load_user_profile(validate=True)


class TestProfileSummary:
    """Test profile summary generation."""

    def test_get_profile_summary_includes_key_info(self, valid_profile):
        """Test that profile summary includes key information."""
        summary = valid_profile.get_profile_summary()

        assert valid_profile.target_role in summary
        assert valid_profile.name != "Your Name"  # Ensure we're not using default
        assert valid_profile.expertise_areas[0] in summary
        assert valid_profile.region in summary

    def test_get_profile_summary_includes_github_if_present(self, valid_profile):
        """Test that GitHub is included if username is set."""
        valid_profile.github_username = "testuser"
        summary = valid_profile.get_profile_summary()

        assert "github.com/testuser" in summary

    def test_get_profile_summary_includes_projects_if_not_default(self, valid_profile):
        """Test that notable projects are included if not default."""
        valid_profile.notable_projects = [
            {
                "name": "Real Project",
                "description": "A real project",
                "technologies": "Python",
                "url": "https://example.com",
            }
        ]
        summary = valid_profile.get_profile_summary()

        assert "Real Project" in summary
        assert "Notable Projects" in summary

    def test_get_profile_summary_excludes_default_projects(self):
        """Test that default project placeholder is excluded."""
        profile = UserProfile()  # Default profile with placeholder project
        summary = profile.get_profile_summary()

        # Should not include the default "Project Name" placeholder
        assert "Notable Projects" not in summary or "Project Name" not in summary


class TestProfileConversion:
    """Test profile to_dict conversion."""

    def test_to_dict_includes_all_fields(self, valid_profile):
        """Test that to_dict includes all profile fields."""
        profile_dict = valid_profile.to_dict()

        expected_keys = [
            "name",
            "target_role",
            "expertise_areas",
            "content_goals",
            "region",
            "languages",
            "target_industries",
            "github_username",
            "linkedin_url",
            "portfolio_url",
            "kaggle_username",
            "notable_projects",
            "primary_skills",
            "content_tone",
            "use_emojis",
            "posting_frequency",
            "unique_value_proposition",
            "key_differentiators",
        ]

        for key in expected_keys:
            assert key in profile_dict

    def test_to_dict_values_match_profile(self, valid_profile):
        """Test that to_dict values match profile attributes."""
        profile_dict = valid_profile.to_dict()

        assert profile_dict["name"] == valid_profile.name
        assert profile_dict["target_role"] == valid_profile.target_role
        assert profile_dict["expertise_areas"] == valid_profile.expertise_areas
        assert profile_dict["use_emojis"] == valid_profile.use_emojis
