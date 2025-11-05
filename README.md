# Skill Manager

A CLI tool for managing Anthropic skills with cloud sync capabilities.

## Overview

Skill Manager is a generic, extensible tool for managing skills locally and syncing them with the Anthropic Skills API. It provides validation, versioning, and bidirectional sync between your local skill directories and Anthropic's cloud platform.

## Features

- **Skill Validation**: Validate skill structure and SKILL.md format before upload
- **Cloud Sync**: Upload skills to Anthropic API and create new versions
- **Registry Tracking**: Track local and remote skills with metadata
- **Change Detection**: Detect local changes and avoid unnecessary uploads
- **CLI Interface**: Easy-to-use command-line interface with rich formatting

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [Skill Structure](#skill-structure)
- [Daily Workflow](#daily-workflow)
- [Troubleshooting](#troubleshooting)
- [Batch Operations](#batch-operations)
- [Architecture](#architecture)

---

## Installation

### Prerequisites

- Python 3.9 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/settings/keys))

### Quick Install (Recommended)

```bash
# 1. Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 2. Run installation script
./install.sh

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Configure with your API key
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
skill-manager init

# 5. Verify installation
skill-manager --version
```

### Alternative: Install with pip

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Skill Manager
pip install -e .

# Verify installation
skill-manager --version
```

---

## Quick Start

Get up and running in 5 minutes.

### Step 1: Configure API Key (1 minute)

```bash
# Set environment variable
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Or add to your shell profile for persistence
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key"' >> ~/.zshrc  # macOS
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key"' >> ~/.bashrc # Linux

# Initialize configuration
skill-manager init
```

Expected output:
```
✓ Configuration saved to skill-manager.config.json
✓ Skills directory: .claude/skills
```

### Step 2: Create Your First Skill (2 minutes)

```bash
# Create skill directory
mkdir -p .claude/skills/hello-skill
cd .claude/skills/hello-skill

# Create SKILL.md
cat > SKILL.md << 'EOF'
# Hello Skill

A simple demonstration skill.

## Purpose

This skill demonstrates the basic structure required for Anthropic skills.

## Usage

Use this as a template for creating new skills.

## Example

```python
print("Hello from my skill!")
```
EOF

# Create a simple script (optional)
cat > hello.py << 'EOF'
def greet(name="World"):
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet())
EOF

# Return to project root
cd ../../..
```

### Step 3: Validate (30 seconds)

```bash
skill-manager validate .claude/skills/hello-skill
```

Expected output:
```
Validating skill: hello-skill
Path: /path/to/.claude/skills/hello-skill

✓ Validation passed!

Metadata:
  name: Hello Skill
  description: A simple demonstration skill.
  total_size_mb: 0.01 MB
  file_count: 2
```

### Step 4: Upload (1 minute)

```bash
skill-manager upload .claude/skills/hello-skill --title "Hello Skill"
```

Expected output:
```
Uploading skill: hello-skill

✓ Skill created!
  Skill ID: skill_01AbCdEfGhIjKlMnOpQrStUv
  Version: 1759178010641129
  Name: hello-skill
```

### Step 5: Verify (30 seconds)

```bash
# Check local registry
skill-manager list

# Check remote API
skill-manager list --remote --source custom
```

**Congratulations!** You've successfully:
- ✓ Installed Skill Manager
- ✓ Created your first skill
- ✓ Validated the skill structure
- ✓ Uploaded to Anthropic API
- ✓ Verified the upload

---

## Configuration

### Configuration Files Location

All configuration files are stored **directly in your project root** for easy access:

```
your-project/
├── skill-manager.config.json      # Your settings (git-ignored)
├── skill-manager.registry.json    # Skill tracking (git-ignored)
├── .skill-manager-cache/          # Downloaded skills (git-ignored)
│
├── skill-manager.config.example.json  # Template (checked into git)
│
├── .claude/skills/                # Your skills
└── .venv/                         # Virtual environment
```

### Configuration File Format

Created when you run `skill-manager init`:

```json
{
  "api_key": "sk-ant-your-key-here",
  "api_version": "2023-06-01",
  "beta": ["skills-2025-10-02"],
  "skills_directory": ".claude/skills",
  "auto_sync": false
}
```

**Fields:**
- **api_key**: Your Anthropic API key
- **api_version**: API version (2023-06-01)
- **beta**: Beta features to enable (skills API)
- **skills_directory**: Where your skills are located
- **auto_sync**: Auto-sync on changes (not yet implemented)

### Using Environment Variables (Recommended)

For better security, use environment variables instead of hardcoding your API key:

**Step 1:** Add to your shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
export ANTHROPIC_API_KEY='sk-ant-your-actual-key'
```

**Step 2:** Reference it in `skill-manager.config.json`:
```json
{
  "api_key": "ANTHROPIC_API_KEY_ENV_VAR",
  ...
}
```

This keeps your actual API key out of config files.

### Registry File Format

Automatically created and updated (in `skill-manager.registry.json`):

```json
{
  "version": "1.0",
  "updated_at": "2025-01-15T10:30:00",
  "skills": {
    "product-demand": {
      "name": "product-demand",
      "display_title": "Product Demand Forecasting",
      "local_path": "/path/to/.claude/skills/product-demand",
      "local_hash": "abc123...",
      "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv",
      "remote_version": "1759178010641129",
      "last_sync": "2025-01-15T10:30:00",
      "created_at": "2025-01-15T10:30:00",
      "updated_at": "2025-01-15T10:30:00"
    }
  }
}
```

### Git Ignore

These files are automatically ignored by git:

```gitignore
skill-manager.config.json     # Your private settings
skill-manager.registry.json   # Your skill tracking
.skill-manager-cache/         # Downloaded skills cache
```

Only the example template is checked into version control:
```
skill-manager.config.example.json  # ✓ Checked into git
```

---

## CLI Commands

### `init` - Initialize Configuration

Initialize skill manager configuration.

```bash
skill-manager init [OPTIONS]

Options:
  --api-key TEXT       Anthropic API key
  --skills-dir TEXT    Default skills directory (default: .claude/skills)
```

**Example:**
```bash
# Using environment variable
export ANTHROPIC_API_KEY="sk-ant-..."
skill-manager init

# Or provide directly
skill-manager init --api-key "sk-ant-..."

# Custom skills directory
skill-manager init --skills-dir ./my-skills
```

### `validate` - Validate Skill

Validate a skill directory structure.

```bash
skill-manager validate SKILL_PATH
```

**Checks:**
- SKILL.md file exists
- Valid UTF-8 encoding
- Proper heading structure
- File sizes
- Directory structure

**Example:**
```bash
skill-manager validate .claude/skills/my-skill
```

### `upload` - Upload Skill

Upload a skill to Anthropic API.

```bash
skill-manager upload SKILL_PATH [OPTIONS]

Options:
  --title TEXT       Display title for the skill
  --no-validate      Skip validation before upload
```

**Example:**
```bash
# Upload with title
skill-manager upload .claude/skills/my-skill --title "My Custom Skill"

# Upload without validation (not recommended)
skill-manager upload .claude/skills/my-skill --no-validate
```

### `list` - List Skills

List skills (local or remote).

```bash
skill-manager list [OPTIONS]

Options:
  --remote                    List remote skills from API
  --source [custom|anthropic] Filter by source
```

**Examples:**
```bash
# List local skills
skill-manager list

# List remote skills
skill-manager list --remote

# Filter by source
skill-manager list --remote --source custom
skill-manager list --remote --source anthropic
```

### `status` - Show Sync Status

Show sync status for all skills.

```bash
skill-manager status
```

**Displays:**
- Local presence
- Remote presence
- Local changes detected
- Last sync timestamp

**Example output:**
```
Sync Status:

Skill              Local  Remote  Changes  Last Sync
─────────────────────────────────────────────────────
product-demand     ✓      ✓       No       2025-01-15T10:30:00
commodity-demand   ✓      ✓       Yes      2025-01-14T15:20:00
my-skill           ✓      ✗       N/A      Never
```

### `sync` - Sync Single Skill

Sync a single skill.

```bash
skill-manager sync SKILL_NAME [OPTIONS]

Options:
  --direction [push|pull]  Sync direction (default: push)
```

**Example:**
```bash
skill-manager sync my-skill
```

### `sync-all` - Sync All Skills

Sync all registered skills.

```bash
skill-manager sync-all [OPTIONS]

Options:
  --direction [push|pull]  Sync direction (default: push)
```

**Example:**
```bash
skill-manager sync-all
```

---

## Skill Structure

A valid skill must follow this structure:

```
my-skill/
├── SKILL.md           # Required: Skill documentation
├── script.py          # Optional: Python scripts
├── data/              # Optional: Data files
│   └── config.json
└── lib/               # Optional: Library code
    └── utils.py
```

### SKILL.md Format

The SKILL.md file is required and should follow this format:

```markdown
# Skill Name

Brief description of what the skill does.

## Usage

How to use the skill...

## Parameters

- param1: Description
- param2: Description

## Examples

Example usage...
```

---

## Daily Workflow

### Every Time You Open a New Terminal

```bash
cd /path/to/skill-manager
source .venv/bin/activate
```

**Tip:** Add an alias to your shell profile:
```bash
# Add to ~/.zshrc or ~/.bashrc
alias sm='cd /path/to/skill-manager && source .venv/bin/activate'
```

Then just type:
```bash
sm                        # Activates everything
skill-manager status      # Use as normal
```

### Common Workflow

```bash
# Activate environment
source .venv/bin/activate

# Check status
skill-manager status

# Make changes to your skills...

# Validate changes
skill-manager validate .claude/skills/my-skill

# Sync changes
skill-manager sync my-skill

# Or sync all at once
skill-manager sync-all
```

### Working with Multiple Skills

```bash
# Upload multiple skills
skill-manager upload .claude/skills/product-demand
skill-manager upload .claude/skills/commodity-demand

# Check status and remote sync
skill-manager status
skill-manager list --remote
```

---

## Troubleshooting

### Installation Issues

#### uv command not found

```bash
# Solution 1: Restart shell
exec $SHELL

# Solution 2: Source cargo environment
source $HOME/.cargo/env

# Solution 3: Reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### skill-manager command not found

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Check it's there
which skill-manager  # Should show .venv/bin/skill-manager

# If missing, reinstall
uv pip install -e .
```

#### ImportError when running

```bash
# This means venv is not activated
source .venv/bin/activate

# Then try again
skill-manager --version
```

#### Permission denied on scripts

```bash
# Make scripts executable
chmod +x install.sh install-dev.sh verify_install.sh

# Then run
./install.sh
```

### Configuration Issues

#### API Key Not Found

```
Error: Not initialized. Run 'skill-manager init' first.
```

**Solution:**
```bash
# Set API key environment variable
export ANTHROPIC_API_KEY="sk-ant-..."

# Or reinitialize
skill-manager init --api-key "sk-ant-..."
```

#### Config not found

```bash
# Make sure you're in the project directory
pwd  # Should show your project root

# Re-initialize
skill-manager init
```

### Validation Issues

#### Validation Fails - SKILL.md not found

```
✗ Validation failed

Errors:
  ✗ SKILL.md file not found in skill directory root
```

**Solution:**
```bash
# Check directory structure
ls -la .claude/skills/my-skill/

# Create SKILL.md if missing
cat > .claude/skills/my-skill/SKILL.md << 'EOF'
# My Skill

Description here...
EOF

# Retry validation
skill-manager validate .claude/skills/my-skill
```

### Upload Issues

#### Upload Fails - File Too Large

```
✗ Upload failed: 413 Request Entity Too Large
```

**Solution:**
```bash
# Check skill size
du -sh .claude/skills/large-skill

# Remove large data files or split into multiple skills
# Move data to separate storage, reference via URL in SKILL.md
```

### Sync Issues

#### Changes Not Detected

```bash
# Status shows "No" for changes, but you modified files

# Solution: Force recalculation by re-uploading
skill-manager upload .claude/skills/your-skill
```

---

## Batch Operations

### Upload Multiple Skills

```bash
# Upload all skills in .claude/skills/
for skill_dir in .claude/skills/*/; do
  skill_name=$(basename "$skill_dir")
  skill-manager validate "$skill_dir" && skill-manager upload "$skill_dir" --title "$skill_name"
done
```

### Sync All Skills

```bash
# Sync all skills after updates
skill-manager sync-all
```

---

## How It Works

### Upload Flow

1. **Validation**: Checks SKILL.md, file structure, encoding
2. **Registry Check**: Determines if skill exists (create vs update)
3. **API Call**: Uploads files using Anthropic SDK
4. **Registry Update**: Stores skill ID, version, and file hash

### Sync Flow

1. **Change Detection**: Compares current file hash with stored hash
2. **Skip if No Changes**: Avoids unnecessary API calls
3. **Version Creation**: Creates new version if changes detected
4. **Registry Update**: Updates version and sync timestamp

### Change Detection

Uses SHA-256 hash of all files in skill directory:
- Deterministic (same files = same hash)
- Fast computation
- Detects any file modifications

---

## Architecture

```
skill_manager/
├── __init__.py          # Package initialization
├── api_client.py        # Anthropic API wrapper
├── cli.py               # CLI commands (Click)
├── registry.py          # Skill registry management
├── validator.py         # Skill validation
├── sync.py              # Sync engine
└── utils.py             # Utility functions
```

### Core Components

- **AnthropicSkillsClient**: Wrapper around Anthropic SDK beta.skills API
- **SkillRegistry**: JSON-based registry for tracking skills
- **SkillValidator**: Validates SKILL.md format and directory structure
- **SyncEngine**: Handles bidirectional sync logic
- **CLI**: Click-based command-line interface with rich formatting

---

## Dependencies

```
anthropic>=0.39.0    # Official Anthropic SDK
click>=8.1.0         # CLI framework
pydantic>=2.0.0      # Data validation
rich>=13.0.0         # Terminal formatting
python-dotenv>=1.0.0 # Environment management
```

