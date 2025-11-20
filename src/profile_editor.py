"""Interactive profile editor for the content generation agent."""

import os
import subprocess
from pathlib import Path

from src.profile import PROFILE_PATH, load_profile_from_yaml, save_profile_to_yaml


def get_editor() -> str:
    """Get the user's preferred editor from environment variables.

    Returns:
        Editor command (defaults to 'nano' if not set)
    """
    # Check common editor environment variables
    for env_var in ["VISUAL", "EDITOR"]:
        editor = os.environ.get(env_var)
        if editor:
            return editor

    # Platform-specific defaults
    if os.name == "nt":  # Windows
        return "notepad"
    return "nano"  # Unix-like systems


def edit_profile_interactive() -> bool:
    """Open the profile in an interactive editor.

    Returns:
        True if profile was modified, False otherwise
    """
    if not PROFILE_PATH.exists():
        print(f"❌ Profile not found at {PROFILE_PATH}")
        print("💡 Run: python main.py --init-profile")
        return False

    # Read original content
    with open(PROFILE_PATH, encoding="utf-8") as f:
        original_content = f.read()

    # Get editor
    editor = get_editor()
    print(f"📝 Opening profile in {editor}...")
    print(f"📁 File: {PROFILE_PATH}\n")

    try:
        # Open editor
        subprocess.run([editor, str(PROFILE_PATH)], check=True)

        # Read modified content
        with open(PROFILE_PATH, encoding="utf-8") as f:
            modified_content = f.read()

        # Check if changed
        if original_content == modified_content:
            print("\n📝 No changes made.")
            return False

        print("\n✅ Profile updated!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Editor failed: {e}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Editor '{editor}' not found.")
        print("💡 Set EDITOR environment variable to your preferred editor:")
        print("   export EDITOR=vim")
        print("   export EDITOR=code  # VS Code")
        print("   export EDITOR=emacs")
        return False


def show_profile_diff(path: Path) -> None:
    """Show a diff of profile changes.

    Args:
        path: Path to the profile file
    """
    # This is a placeholder for future implementation
    # Could use difflib or external diff tool
    pass


def edit_profile_field(field_name: str, new_value: str) -> bool:
    """Edit a specific profile field programmatically.

    Args:
        field_name: Name of the field to edit
        new_value: New value for the field

    Returns:
        True if successful, False otherwise
    """
    if not PROFILE_PATH.exists():
        print(f"❌ Profile not found at {PROFILE_PATH}")
        return False

    try:
        # Load profile
        profile = load_profile_from_yaml(PROFILE_PATH)

        # Update field
        if not hasattr(profile, field_name):
            print(f"❌ Unknown field: {field_name}")
            return False

        setattr(profile, field_name, new_value)

        # Save profile
        save_profile_to_yaml(profile, PROFILE_PATH)
        print(f"✅ Updated {field_name} to: {new_value}")
        return True

    except Exception as e:
        print(f"❌ Failed to update profile: {e}")
        return False


def validate_after_edit() -> bool:
    """Validate profile after editing.

    Returns:
        True if validation passed (no errors), False otherwise
    """
    from src.profile import load_user_profile

    print("\n🔍 Validating profile...")
    try:
        load_user_profile(validate=True)
        print("✅ Profile is valid!\n")
        return True
    except ValueError as e:
        print(f"❌ Validation failed: {e}\n")
        print("💡 Please fix the errors and try again.")
        return False
