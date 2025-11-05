"""
Anthropic Skills API client wrapper
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from anthropic.lib import files_from_dir


class AnthropicSkillsClient:
    """Wrapper around Anthropic SDK for skills management."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_version: str = "2023-06-01",
        beta: List[str] = None
    ):
        """
        Initialize Anthropic Skills API client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            api_version: API version to use
            beta: Beta features to enable
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set ANTHROPIC_API_KEY env var or pass api_key parameter."
            )

        self.api_version = api_version
        self.beta = beta or ["skills-2025-10-02"]
        self.client = Anthropic(api_key=self.api_key)

    def create_skill(
        self,
        skill_directory: Path,
        display_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new skill by uploading a directory.

        Args:
            skill_directory: Path to skill directory containing SKILL.md
            display_title: Optional display title for the skill

        Returns:
            Dict containing skill metadata (id, created_at, version, etc.)
        """
        if not skill_directory.exists():
            raise ValueError(f"Skill directory does not exist: {skill_directory}")

        # Use files_from_dir helper to package skill files
        files = files_from_dir(str(skill_directory))

        response = self.client.beta.skills.create(
            betas=self.beta,
            display_title=display_title,
            files=files
        )

        return {
            "id": response.id,
            "display_title": response.display_title,
            "source": response.source,
            "created_at": response.created_at,
            "updated_at": response.updated_at,
            "latest_version": response.latest_version,
            "type": response.type
        }

    def list_skills(
        self,
        source: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List all skills.

        Args:
            source: Filter by source ("custom" or "anthropic")
            limit: Maximum number of skills to return

        Returns:
            List of skill metadata dicts
        """
        skills = []
        next_page = None

        while True:
            response = self.client.beta.skills.list(
                betas=self.beta,
                source=source,
                limit=limit,
                page=next_page
            )

            for skill in response.data:
                skills.append({
                    "id": skill.id,
                    "display_title": skill.display_title,
                    "source": skill.source,
                    "created_at": skill.created_at,
                    "updated_at": skill.updated_at,
                    "latest_version": skill.latest_version,
                    "type": skill.type
                })

            if not response.has_more:
                break

            next_page = response.next_page

        return skills

    def create_skill_version(
        self,
        skill_id: str,
        skill_directory: Path
    ) -> Dict[str, Any]:
        """
        Create a new version of an existing skill.

        Args:
            skill_id: ID of the skill to update
            skill_directory: Path to skill directory containing SKILL.md

        Returns:
            Dict containing skill version metadata
        """
        if not skill_directory.exists():
            raise ValueError(f"Skill directory does not exist: {skill_directory}")

        # Use files_from_dir helper to package skill files
        files = files_from_dir(str(skill_directory))

        response = self.client.beta.skills.versions.create(
            skill_id=skill_id,
            betas=self.beta,
            files=files
        )

        return {
            "id": response.id,
            "skill_id": response.skill_id,
            "name": response.name,
            "description": response.description,
            "directory": response.directory,
            "version": response.version,
            "created_at": response.created_at,
            "type": response.type
        }

    def get_skill(self, skill_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific skill.

        Args:
            skill_id: ID of the skill

        Returns:
            Dict containing skill metadata
        """
        # Note: The API doesn't have a direct "get skill" endpoint
        # We need to list all skills and filter
        all_skills = self.list_skills()
        for skill in all_skills:
            if skill["id"] == skill_id:
                return skill

        raise ValueError(f"Skill not found: {skill_id}")

    def delete_skill(self, skill_id: str) -> bool:
        """
        Delete a skill.

        Args:
            skill_id: ID of the skill to delete

        Returns:
            True if successful

        Note:
            This endpoint may not be available in the current API version.
            Check Anthropic documentation for availability.
        """
        # Note: Delete endpoint not shown in provided API docs
        # This is a placeholder for future API support
        raise NotImplementedError(
            "Delete skill endpoint not available in current API version. "
            "Please check Anthropic documentation for updates."
        )
