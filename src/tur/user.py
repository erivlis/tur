from pathlib import Path

import yaml

from tur.models import UserProfile


def get_user_profile() -> UserProfile:
    """
    Loads the user profile from the project's .tur/user.yaml or a global default.
    """
    local_user_path = Path(".tur/user.yaml")
    global_user_path = Path.home() / ".tur" / "user.yaml"

    config_path = None
    if local_user_path.exists():
        config_path = local_user_path
    elif global_user_path.exists():
        config_path = global_user_path

    if config_path:
        with open(config_path, encoding="utf-8") as f:
            user_data = yaml.safe_load(f)
        return UserProfile(**user_data)
    else:
        # Fallback to a default user if no config is found
        return UserProfile(
            name="Default User",
            role="Architect",
            domain_expertise=["Software Development"],
            core_values=["Clarity", "Simplicity"]
        )
