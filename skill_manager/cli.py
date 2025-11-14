"""
CLI for skill manager
"""

import os
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .api_client import AnthropicSkillsClient
from .registry import SkillRegistry
from .validator import validate_skill
from .sync import SyncEngine
from .utils import (
    get_config_file,
    load_json,
    save_json,
    format_file_size,
    get_directory_size
)

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Skill Manager - CLI tool for managing Anthropic skills."""
    pass


@main.command()
@click.option('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')
@click.option('--skills-dir', default='.claude/skills', help='Default skills directory')
def init(api_key, skills_dir):
    """Initialize skill manager configuration."""
    config_file = get_config_file()

    # Check if already initialized
    if config_file.exists():
        if not click.confirm('Configuration already exists. Overwrite?'):
            console.print("[yellow]Initialization cancelled[/yellow]")
            return

    # Get API key
    if not api_key:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            api_key = click.prompt('Enter your Anthropic API key', hide_input=True)

    # Save configuration
    config = {
        'api_key': api_key,
        'api_version': '2023-06-01',
        'beta': ['skills-2025-10-02'],
        'skills_directory': skills_dir,
        'auto_sync': False
    }

    save_json(config_file, config)
    console.print(f"[green]✓[/green] Configuration saved to {config_file}")
    console.print(f"[green]✓[/green] Skills directory: {skills_dir}")


@main.command()
@click.argument('skill_path', type=click.Path(exists=True))
def validate(skill_path):
    """Validate a skill directory structure."""
    skill_path = Path(skill_path)

    console.print(f"\n[bold]Validating skill:[/bold] {skill_path.name}")
    console.print(f"[dim]Path: {skill_path.absolute()}[/dim]\n")

    result = validate_skill(skill_path)

    if result.valid:
        console.print("[green]✓ Validation passed![/green]\n")
    else:
        console.print("[red]✗ Validation failed[/red]\n")

    # Show errors
    if result.errors:
        console.print("[bold red]Errors:[/bold red]")
        for error in result.errors:
            console.print(f"  [red]✗[/red] {error}")
        console.print()

    # Show warnings
    if result.warnings:
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  [yellow]![/yellow] {warning}")
        console.print()

    # Show metadata
    if result.metadata:
        console.print("[bold]Metadata:[/bold]")
        for key, value in result.metadata.items():
            if key == 'total_size_mb':
                console.print(f"  {key}: {value} MB")
            elif isinstance(value, list):
                console.print(f"  {key}: {', '.join(str(v) for v in value[:5])}")
            else:
                console.print(f"  {key}: {value}")

    sys.exit(0 if result.valid else 1)


@main.command()
@click.argument('skill_path', type=click.Path(exists=True))
@click.option('--title', help='Display title for the skill')
@click.option('--no-validate', is_flag=True, help='Skip validation before upload')
def upload(skill_path, title, no_validate):
    """Upload a skill to Anthropic API."""
    config = load_json(get_config_file())
    if not config:
        console.print("[red]Error: Not initialized. Run 'skill-manager init' first.[/red]")
        sys.exit(1)

    skill_path = Path(skill_path)

    # Initialize components
    api_client = AnthropicSkillsClient(api_key=config.get('api_key'))
    registry = SkillRegistry()
    sync_engine = SyncEngine(api_client, registry)

    console.print(f"\n[bold]Uploading skill:[/bold] {skill_path.name}")

    try:
        result = sync_engine.upload_skill(
            skill_path=skill_path,
            display_title=title,
            validate=not no_validate
        )

        console.print(f"\n[green]✓ Skill {result['action']}![/green]")
        console.print(f"  Skill ID: {result['skill_id']}")
        console.print(f"  Version: {result['version']}")
        console.print(f"  Name: {result['name']}\n")

    except Exception as e:
        console.print(f"\n[red]✗ Upload failed: {e}[/red]\n")
        sys.exit(1)


@main.command()
@click.option('--remote', is_flag=True, help='List remote skills from API')
@click.option('--source', type=click.Choice(['custom', 'anthropic']), help='Filter by source')
def list(remote, source):
    """List skills (local or remote)."""
    config = load_json(get_config_file())
    if not config:
        console.print("[red]Error: Not initialized. Run 'skill-manager init' first.[/red]")
        sys.exit(1)

    if remote:
        # List remote skills
        api_client = AnthropicSkillsClient(api_key=config.get('api_key'))
        skills = api_client.list_skills(source=source)

        console.print(f"\n[bold]Remote Skills ({len(skills)}):[/bold]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID")
        table.add_column("Title")
        table.add_column("Source")
        table.add_column("Version")
        table.add_column("Updated")

        for skill in skills:
            table.add_row(
                skill['id'][:24] + '...',
                skill['display_title'] or 'N/A',
                skill['source'],
                skill.get('latest_version', 'N/A')[:16],
                skill.get('updated_at', 'N/A')[:19]
            )

        console.print(table)
        console.print()

    else:
        # List local skills
        registry = SkillRegistry()
        skills = registry.list_skills()

        console.print(f"\n[bold]Local Skills ({len(skills)}):[/bold]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name")
        table.add_column("Remote ID")
        table.add_column("Status")
        table.add_column("Last Sync")

        for skill in skills:
            has_remote = "✓" if skill.get('skill_id') else "✗"
            status_color = "green" if skill.get('skill_id') else "yellow"

            table.add_row(
                skill['name'],
                skill.get('skill_id', 'Not uploaded')[:24],
                f"[{status_color}]{has_remote}[/{status_color}]",
                (skill.get('last_sync') or 'Never')[:19]
            )

        console.print(table)
        console.print()


@main.command()
def status():
    """Show sync status for all skills."""
    config = load_json(get_config_file())
    if not config:
        console.print("[red]Error: Not initialized. Run 'skill-manager init' first.[/red]")
        sys.exit(1)

    registry = SkillRegistry()
    statuses = registry.get_sync_status()

    console.print(f"\n[bold]Sync Status:[/bold]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Skill")
    table.add_column("Local")
    table.add_column("Remote")
    table.add_column("Changes")
    table.add_column("Last Sync")

    for status in statuses:
        local_mark = "[green]✓[/green]" if status['has_local'] else "[red]✗[/red]"
        remote_mark = "[green]✓[/green]" if status['has_remote'] else "[yellow]✗[/yellow]"
        changes_mark = "[yellow]Yes[/yellow]" if status['has_local_changes'] else "[green]No[/green]"

        table.add_row(
            status['name'],
            local_mark,
            remote_mark,
            changes_mark,
            (status.get('last_sync') or 'Never')[:19]
        )

    console.print(table)
    console.print()


@main.command()
@click.argument('skill_name')
@click.option('--direction', type=click.Choice(['push', 'pull']), default='push', help='Sync direction')
def sync(skill_name, direction):
    """Sync a skill between local and remote."""
    config = load_json(get_config_file())
    if not config:
        console.print("[red]Error: Not initialized. Run 'skill-manager init' first.[/red]")
        sys.exit(1)

    api_client = AnthropicSkillsClient(api_key=config.get('api_key'))
    registry = SkillRegistry()
    sync_engine = SyncEngine(api_client, registry)

    console.print(f"\n[bold]Syncing skill:[/bold] {skill_name} ({direction})")

    try:
        result = sync_engine.sync_skill(skill_name, direction=direction)

        if result['action'] == 'skipped':
            console.print(f"\n[yellow]⊘ Skipped: {result['reason']}[/yellow]\n")
        else:
            console.print(f"\n[green]✓ Sync complete![/green]")
            console.print(f"  Action: {result['action']}")
            console.print(f"  Version: {result.get('version', 'N/A')}\n")

    except Exception as e:
        console.print(f"\n[red]✗ Sync failed: {e}[/red]\n")
        sys.exit(1)


@main.command()
@click.option('--direction', type=click.Choice(['push', 'pull']), default='push', help='Sync direction')
def sync_all(direction):
    """Sync all skills."""
    config = load_json(get_config_file())
    if not config:
        console.print("[red]Error: Not initialized. Run 'skill-manager init' first.[/red]")
        sys.exit(1)

    api_client = AnthropicSkillsClient(api_key=config.get('api_key'))
    registry = SkillRegistry()
    sync_engine = SyncEngine(api_client, registry)

    console.print(f"\n[bold]Syncing all skills ({direction})...[/bold]\n")

    results = sync_engine.sync_all(direction=direction)

    # Show synced skills
    if results['synced']:
        console.print(f"[green]✓ Synced ({len(results['synced'])}):[/green]")
        for item in results['synced']:
            console.print(f"  • {item['name']} ({item['action']})")
        console.print()

    # Show skipped skills
    if results['skipped']:
        console.print(f"[yellow]⊘ Skipped ({len(results['skipped'])}):[/yellow]")
        for item in results['skipped']:
            console.print(f"  • {item['name']} - {item['reason']}")
        console.print()

    # Show failed skills
    if results['failed']:
        console.print(f"[red]✗ Failed ({len(results['failed'])}):[/red]")
        for item in results['failed']:
            console.print(f"  • {item['name']} - {item['error']}")
        console.print()


if __name__ == '__main__':
    main()
