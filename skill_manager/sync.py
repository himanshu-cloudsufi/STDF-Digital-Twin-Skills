"""
Sync engine for bidirectional skill synchronization
"""

from pathlib import Path
from typing import Optional, Dict, Any
from .api_client import AnthropicSkillsClient
from .registry import SkillRegistry
from .validator import validate_skill


class SyncEngine:
    """Engine for syncing skills between local and remote."""

    def __init__(
        self,
        api_client: AnthropicSkillsClient,
        registry: SkillRegistry
    ):
        """
        Initialize sync engine.

        Args:
            api_client: Anthropic API client
            registry: Skill registry
        """
        self.api_client = api_client
        self.registry = registry

    def upload_skill(
        self,
        skill_path: Path,
        display_title: Optional[str] = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Upload a skill to Anthropic API.

        Args:
            skill_path: Path to skill directory
            display_title: Optional display title
            validate: Whether to validate before uploading

        Returns:
            Dict with upload results

        Raises:
            ValueError: If validation fails
        """
        skill_path = Path(skill_path).absolute()
        skill_name = skill_path.name

        # Validate if requested
        if validate:
            validation = validate_skill(skill_path)
            if not validation.valid:
                raise ValueError(
                    f"Skill validation failed:\n" +
                    "\n".join(f"  - {err}" for err in validation.errors)
                )

        # Check if skill is already registered
        existing_skill = self.registry.get_skill(skill_name)

        if existing_skill and existing_skill.get("skill_id"):
            # Update existing skill (create new version)
            skill_id = existing_skill["skill_id"]
            version_info = self.api_client.create_skill_version(
                skill_id=skill_id,
                skill_directory=skill_path
            )

            # Update registry
            self.registry.update_remote_info(
                name=skill_name,
                skill_id=skill_id,
                remote_version=version_info["version"],
                display_title=display_title
            )
            self.registry.update_local_hash(skill_name)

            return {
                "action": "updated",
                "skill_id": skill_id,
                "version": version_info["version"],
                "name": skill_name
            }
        else:
            # Create new skill
            skill_info = self.api_client.create_skill(
                skill_directory=skill_path,
                display_title=display_title
            )

            # Add to registry
            self.registry.add_skill(
                name=skill_name,
                local_path=skill_path,
                skill_id=skill_info["id"],
                display_title=display_title or skill_info.get("display_title"),
                remote_version=skill_info.get("latest_version")
            )

            return {
                "action": "created",
                "skill_id": skill_info["id"],
                "version": skill_info.get("latest_version"),
                "name": skill_name
            }

    def sync_skill(
        self,
        skill_name: str,
        direction: str = "push"
    ) -> Dict[str, Any]:
        """
        Sync a skill between local and remote.

        Args:
            skill_name: Name of the skill
            direction: Sync direction ("push" or "pull")

        Returns:
            Dict with sync results

        Raises:
            ValueError: If skill not found or sync fails
        """
        skill_data = self.registry.get_skill(skill_name)
        if not skill_data:
            raise ValueError(f"Skill not found in registry: {skill_name}")

        local_path = Path(skill_data["local_path"])

        if direction == "push":
            # Check for local changes
            has_changes = self.registry.check_local_changes(skill_name)

            if not has_changes:
                return {
                    "action": "skipped",
                    "reason": "No local changes detected",
                    "skill_name": skill_name
                }

            # Upload changes
            result = self.upload_skill(
                skill_path=local_path,
                display_title=skill_data.get("display_title")
            )
            return result

        elif direction == "pull":
            # Pull not implemented yet (requires download API)
            raise NotImplementedError(
                "Pull sync not yet implemented. "
                "Anthropic API does not currently support downloading skills."
            )

        else:
            raise ValueError(f"Invalid sync direction: {direction}")

    def sync_all(self, direction: str = "push") -> Dict[str, Any]:
        """
        Sync all skills.

        Args:
            direction: Sync direction ("push" or "pull")

        Returns:
            Dict with results for all skills
        """
        results = {
            "synced": [],
            "skipped": [],
            "failed": []
        }

        skills = self.registry.list_skills()

        for skill in skills:
            skill_name = skill["name"]
            try:
                result = self.sync_skill(skill_name, direction=direction)

                if result["action"] == "skipped":
                    results["skipped"].append({
                        "name": skill_name,
                        "reason": result.get("reason", "Unknown")
                    })
                else:
                    results["synced"].append({
                        "name": skill_name,
                        "action": result["action"],
                        "version": result.get("version")
                    })

            except Exception as e:
                results["failed"].append({
                    "name": skill_name,
                    "error": str(e)
                })

        return results
