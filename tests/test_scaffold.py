from pathlib import Path

import pytest
from typer.testing import CliRunner

from tur.cli.agent import app as agent_app
from tur.scaffold import generate_agents_md, scaffold_workspace

runner = CliRunner()


def test_generate_agents_md_aaif():
    """Verify default AAIF agent guidelines generation."""
    content = generate_agents_md('aaif')
    assert '# AI Agent Guidelines' in content
    assert 'Turn Zero Initialization (Awakening)' in content
    assert 'State Management Lifecycle' in content
    assert 'Symmetrical Isolation Invariant (Boundary Constraint)' in content
    assert '.tur/' in content


def test_generate_agents_md_claude():
    """Verify Claude Code guidelines generation."""
    content = generate_agents_md('claude')
    assert '# Claude Code Guidelines for Tur' in content
    assert 'AGENTS.md' in content
    assert 'tur wake' in content


def test_generate_agents_md_invalid():
    """Verify error on unsupported format."""
    with pytest.raises(ValueError, match="Unsupported scaffold format 'unknown'"):
        generate_agents_md('unknown')


def test_scaffold_workspace_default(tmp_path: Path):
    """Verify scaffold_workspace writes AGENTS.md by default."""
    target = scaffold_workspace(workspace_dir=tmp_path)
    assert target == tmp_path / 'AGENTS.md'
    assert target.exists()
    assert '# AI Agent Guidelines' in target.read_text(encoding='utf-8')


def test_scaffold_workspace_claude(tmp_path: Path):
    """Verify scaffold_workspace writes CLAUDE.md when format is claude."""
    target = scaffold_workspace(workspace_dir=tmp_path, format='claude')
    assert target == tmp_path / 'CLAUDE.md'
    assert target.exists()
    assert '# Claude Code Guidelines for Tur' in target.read_text(encoding='utf-8')


def test_scaffold_workspace_collision_error(tmp_path: Path):
    """Verify scaffold_workspace raises FileExistsError if target exists without force."""
    scaffold_workspace(workspace_dir=tmp_path)
    with pytest.raises(FileExistsError, match='Target scaffold file already exists'):
        scaffold_workspace(workspace_dir=tmp_path)


def test_scaffold_workspace_force_overwrite(tmp_path: Path):
    """Verify scaffold_workspace overwrites if force=True."""
    target = scaffold_workspace(workspace_dir=tmp_path)
    target.write_text('stale content', encoding='utf-8')
    scaffold_workspace(workspace_dir=tmp_path, force=True)
    assert '# AI Agent Guidelines' in target.read_text(encoding='utf-8')


def test_scaffold_workspace_custom_output(tmp_path: Path):
    """Verify scaffold_workspace writes to custom output path."""
    custom_path = tmp_path / 'sub' / 'CUSTOM_AGENTS.md'
    target = scaffold_workspace(workspace_dir=tmp_path, output_file=custom_path)
    assert target == custom_path
    assert custom_path.exists()


def test_cli_scaffold_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify CLI 'tur scaffold' command execution."""
    monkeypatch.chdir(tmp_path)
    res = runner.invoke(agent_app, ['scaffold'])
    assert res.exit_code == 0
    assert (tmp_path / 'AGENTS.md').exists()

    # Re-run without force should fail gracefully
    res_collide = runner.invoke(agent_app, ['scaffold'])
    assert res_collide.exit_code == 1

    # Re-run with --force should succeed
    res_force = runner.invoke(agent_app, ['scaffold', '--force', '--format', 'claude'])
    assert res_force.exit_code == 0
    assert (tmp_path / 'CLAUDE.md').exists()
