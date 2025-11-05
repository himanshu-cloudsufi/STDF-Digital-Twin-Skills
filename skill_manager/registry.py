"""
Skills registry for tracking local and remote skills
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from .utils import (
    get_registry_file,
    load_json,
    save_json,
    compute_directory_hash
)


class SkillRegistry:
    """Registry for tracking local and remote skills."""

    def __init__(self, registry_file: Optional[Path] = None):
        """
        Initialize skill registry.

        Args:
            registry_file: Path to registry JSON file (defaults to ~/.skill-manager/registry.json)
        """
        self.registry_file = registry_file or get_registry_file()
        self.skills: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load registry from file."""
        data = load_json(self.registry_file)
        self.skills = data.get("skills", {})

    def save(self) -> None:
        """Save registry to file."""
        data = {
            "version": "1.0",
            "updated_at": datetime.utcnow().isoformat(),
            "skills": self.skills
        }
        save_json(self.registry_file, data)

    def add_skill(
        self,
        name: str,
        local_path: Path,
        skill_id: Optional[str] = None,
        display_title: Optional[str] = None,
        remote_version: Optional[str] = None
    ) -> None:
        """
        Add or update a skill in the registry.

        Args:
            name: Skill name (directory name)
            local_path: Path to local skill directory
            skill_id: Remote skill ID (if uploaded)
            display_title: Display title for the skill
            remote_version: Remote version identifier
        """
        # Compute hash of local files
        local_hash = compute_directory_hash(local_path)

        skill_entry = {
            "name": name,
            "display_title": display_title or name,
            "local_path": str(local_path.absolute()),
            "local_hash": local_hash,
            "skill_id": skill_id,
            "remote_version": remote_version,
            "last_sync": datetime.utcnow().isoformat(),
            "created_at": self.skills.get(name, {}).get("created_at") or datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        self.skills[name] = skill_entry
        self.save()

    def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get skill metadata by name.

        Args:
            name: Skill name

        Returns:
            Skill metadata dict or None if not found
        """
        return self.skills.get(name)

    def get_skill_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        Get skill metadata by remote skill ID.

        Args:
            skill_id: Remote skill ID

        Returns:
            Skill metadata dict or None if not found
        """
        for skill_name, skill_data in self.skills.items():
            if skill_data.get("skill_id") == skill_id:
                return skill_data
        return None

    def list_skills(self, uploaded_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all skills in registry.

        Args:
            uploaded_only: If True, only return skills that have been uploaded

        Returns:
            List of skill metadata dicts
        """
        skills_list = []
        for name, skill_data in self.skills.items():
            if uploaded_only and not skill_data.get("skill_id"):
                continue
            skills_list.append({
                "name": name,
                **skill_data
            })
        return skills_list

    def remove_skill(self, name: str) -> bool:
        """
        Remove a skill from the registry.

        Args:
            name: Skill name

        Returns:
            True if skill was removed, False if not found
        """
        if name in self.skills:
            del self.skills[name]
            self.save()
            return True
        return False

    def update_remote_info(
        self,
        name: str,
        skill_id: str,
        remote_version: str,
        display_title: Optional[str] = None
    ) -> None:
        """
        Update remote information for a skill.

        Args:
            name: Skill name
            skill_id: Remote skill ID
            remote_version: Remote version identifier
            display_title: Display title for the skill
        """
        if name not in self.skills:
            raise ValueError(f"Skill not found in registry: {name}")

        self.skills[name]["skill_id"] = skill_id
        self.skills[name]["remote_version"] = remote_version
        self.skills[name]["last_sync"] = datetime.utcnow().isoformat()
        self.skills[name]["updated_at"] = datetime.utcnow().isoformat()

        if display_title:
            self.skills[name]["display_title"] = display_title

        self.save()

    def check_local_changes(self, name: str) -> bool:
        """
        Check if local files have changed since last sync.

        Args:
            name: Skill name

        Returns:
            True if local files have changed, False otherwise
        """
        skill_data = self.get_skill(name)
        if not skill_data:
            return False

        local_path = Path(skill_data["local_path"])
        if not local_path.exists():
            return False

        current_hash = compute_directory_hash(local_path)
        stored_hash = skill_data.get("local_hash", "")

        return current_hash != stored_hash

    def update_local_hash(self, name: str) -> None:
        """
        Update the stored hash for local files.

        Args:
            name: Skill name
        """
        skill_data = self.get_skill(name)
        if not skill_data:
            raise ValueError(f"Skill not found in registry: {name}")

        local_path = Path(skill_data["local_path"])
        if not local_path.exists():
            raise ValueError(f"Local path does not exist: {local_path}")

        current_hash = compute_directory_hash(local_path)
        self.skills[name]["local_hash"] = current_hash
        self.skills[name]["updated_at"] = datetime.utcnow().isoformat()
        self.save()

    def get_sync_status(self) -> List[Dict[str, Any]]:
        """
        Get sync status for all skills.

        Returns:
            List of dicts with skill name and sync status
        """
        status_list = []

        for name, skill_data in self.skills.items():
            has_local = Path(skill_data["local_path"]).exists()
            has_remote = bool(skill_data.get("skill_id"))
            has_changes = self.check_local_changes(name) if has_local else False

            status_list.append({
                "name": name,
                "has_local": has_local,
                "has_remote": has_remote,
                "has_local_changes": has_changes,
                "skill_id": skill_data.get("skill_id"),
                "remote_version": skill_data.get("remote_version"),
                "last_sync": skill_data.get("last_sync")
            })

        return status_list
