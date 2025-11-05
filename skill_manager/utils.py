"""
Utility functions for skill manager
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional


def get_project_root() -> Path:
    """
    Get the project root directory.
    Looks for pyproject.toml or .git directory to identify project root.
    Falls back to current working directory.
    """
    current = Path.cwd()

    # Walk up directory tree looking for project markers
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent

    # Fallback to current directory
    return current


def get_config_file() -> Path:
    """Get the configuration file path (in project root)."""
    return get_project_root() / "skill-manager.config.json"


def get_registry_file() -> Path:
    """Get the registry file path (in project root)."""
    return get_project_root() / "skill-manager.registry.json"


def get_cache_dir() -> Path:
    """Get the cache directory (in project root)."""
    cache_dir = get_project_root() / ".skill-manager-cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON file safely."""
    if not file_path.exists():
        return {}

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Save data to JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def compute_directory_hash(directory: Path) -> str:
    """
    Compute a hash of all files in a directory.
    Used to detect changes in skill files.
    """
    hasher = hashlib.sha256()

    # Walk through directory in sorted order for consistent hashing
    for root, dirs, files in sorted(os.walk(directory)):
        # Sort for consistency
        dirs.sort()
        files.sort()

        for filename in files:
            filepath = Path(root) / filename

            # Skip hidden files and cache directories
            if filename.startswith('.'):
                continue

            # Add filename to hash
            hasher.update(filename.encode())

            # Add file content to hash
            try:
                with open(filepath, 'rb') as f:
                    hasher.update(f.read())
            except (IOError, OSError):
                # Skip files that can't be read
                continue

    return hasher.hexdigest()


def find_skill_md(directory: Path) -> Optional[Path]:
    """Find SKILL.md file in directory (case-insensitive)."""
    for filename in ['SKILL.md', 'skill.md', 'Skill.md']:
        skill_file = directory / filename
        if skill_file.exists():
            return skill_file
    return None


def get_skill_directory_name(skill_path: Path) -> str:
    """Get the top-level directory name for the skill."""
    return skill_path.name


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_directory_size(directory: Path) -> int:
    """Get total size of all files in directory."""
    total_size = 0
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = Path(root) / filename
            try:
                total_size += filepath.stat().st_size
            except (IOError, OSError):
                continue
    return total_size
