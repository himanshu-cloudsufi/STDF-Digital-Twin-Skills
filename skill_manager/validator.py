"""
Skill structure validator
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of skill validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class SkillValidator:
    """Validator for skill directory structure and SKILL.md format."""

    # Required files/directories
    REQUIRED_FILES = ["SKILL.md"]

    # SKILL.md required sections
    REQUIRED_SECTIONS = ["# "]  # At least one heading required

    # Maximum file size (50MB default, adjust as needed)
    MAX_FILE_SIZE = 50 * 1024 * 1024

    def __init__(self, skill_directory: Path):
        """
        Initialize validator for a skill directory.

        Args:
            skill_directory: Path to skill directory
        """
        self.skill_directory = Path(skill_directory)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def validate(self) -> ValidationResult:
        """
        Validate skill directory structure and contents.

        Returns:
            ValidationResult with validation status and details
        """
        self.errors = []
        self.warnings = []
        self.metadata = {}

        # Check if directory exists
        if not self.skill_directory.exists():
            self.errors.append(f"Directory does not exist: {self.skill_directory}")
            return self._build_result()

        if not self.skill_directory.is_dir():
            self.errors.append(f"Path is not a directory: {self.skill_directory}")
            return self._build_result()

        # Validate directory structure
        self._validate_directory_structure()

        # Validate SKILL.md file
        self._validate_skill_md()

        # Validate file sizes
        self._validate_file_sizes()

        # Extract metadata
        self._extract_metadata()

        return self._build_result()

    def _validate_directory_structure(self) -> None:
        """Validate that all files are in the same top-level directory."""
        # Check for SKILL.md in root
        skill_md_found = False
        for filename in ['SKILL.md', 'skill.md', 'Skill.md']:
            if (self.skill_directory / filename).exists():
                skill_md_found = True
                break

        if not skill_md_found:
            self.errors.append("SKILL.md file not found in skill directory root")

        # Check that files are in top-level directory (Anthropic requirement)
        # All files must be in same directory, no nested subdirectories required
        # but subdirectories are allowed for organization

    def _validate_skill_md(self) -> None:
        """Validate SKILL.md file format and content."""
        skill_md_path = self._find_skill_md()

        if not skill_md_path:
            self.errors.append("SKILL.md file not found")
            return

        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if file is empty
            if not content.strip():
                self.errors.append("SKILL.md file is empty")
                return

            # Check for at least one heading
            if not re.search(r'^#\s+.+', content, re.MULTILINE):
                self.warnings.append("SKILL.md should contain at least one heading")

            # Check for skill name (first heading)
            name_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
            if name_match:
                self.metadata['name'] = name_match.group(1).strip()
            else:
                self.warnings.append("Could not extract skill name from SKILL.md")

            # Check for description (content after first heading)
            desc_match = re.search(r'^#\s+.+\n\n(.+?)(?:\n#|$)', content, re.MULTILINE | re.DOTALL)
            if desc_match:
                self.metadata['description'] = desc_match.group(1).strip()[:200]  # First 200 chars
            else:
                self.warnings.append("Could not extract description from SKILL.md")

        except UnicodeDecodeError:
            self.errors.append("SKILL.md file has invalid UTF-8 encoding")
        except Exception as e:
            self.errors.append(f"Error reading SKILL.md: {str(e)}")

    def _validate_file_sizes(self) -> None:
        """Validate that files are within size limits."""
        import os
        total_size = 0

        for root, dirs, files in os.walk(self.skill_directory):
            for filename in files:
                filepath = Path(root) / filename

                # Skip hidden files
                if filename.startswith('.'):
                    continue

                try:
                    file_size = filepath.stat().st_size
                    total_size += file_size

                    if file_size > self.MAX_FILE_SIZE:
                        self.warnings.append(
                            f"File {filepath.relative_to(self.skill_directory)} "
                            f"exceeds recommended size ({file_size / 1024 / 1024:.1f}MB)"
                        )
                except (IOError, OSError) as e:
                    self.warnings.append(f"Could not read file {filepath}: {str(e)}")

        self.metadata['total_size'] = total_size
        self.metadata['total_size_mb'] = round(total_size / 1024 / 1024, 2)

    def _extract_metadata(self) -> None:
        """Extract additional metadata from skill directory."""
        self.metadata['directory_name'] = self.skill_directory.name

        # Count files
        file_count = sum(1 for _ in self.skill_directory.rglob('*') if _.is_file())
        self.metadata['file_count'] = file_count

        # List top-level contents
        top_level = [item.name for item in self.skill_directory.iterdir()]
        self.metadata['top_level_items'] = top_level

    def _find_skill_md(self) -> Optional[Path]:
        """Find SKILL.md file (case-insensitive)."""
        for filename in ['SKILL.md', 'skill.md', 'Skill.md']:
            skill_file = self.skill_directory / filename
            if skill_file.exists():
                return skill_file
        return None

    def _build_result(self) -> ValidationResult:
        """Build validation result."""
        return ValidationResult(
            valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
            metadata=self.metadata
        )


def validate_skill(skill_directory: Path) -> ValidationResult:
    """
    Convenience function to validate a skill directory.

    Args:
        skill_directory: Path to skill directory

    Returns:
        ValidationResult
    """
    validator = SkillValidator(skill_directory)
    return validator.validate()
