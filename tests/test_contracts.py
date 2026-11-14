"""
Unit and integration tests for Cognitive Skill Contracts (EP-0137).
"""

import json

import pytest
from typer.testing import CliRunner

from tur.cli.admin import app as admin_app
from tur.contracts import (
    AxiomPayload,
    DreamingDeltaInput,
    DreamingDeltaOutput,
    DreamingMemoryRecord,
    PersonaForgeInput,
    PersonaForgeOutput,
    PrinciplePayload,
    RefutationLink,
    SupersessionLink,
    VerificationInput,
    VerificationOutput,
    VerificationProvenance,
    apply_dreaming_output,
    apply_forge_output,
    format_contract_delegation,
    get_contract,
    list_contracts,
    validate_contract,
)
from tur.memory import MemoryManager
from tur.models import MemoryScope, MemoryType

runner = CliRunner()


class TestContractSchemas:
    def test_persona_forge_schemas(self):
        inp = PersonaForgeInput(
            project_name='tur-test',
            detected_tech_stack=['Python', 'FastMCP'],
            target_harnesses=['claude-code'],
        )
        assert inp.project_name == 'tur-test'
        assert 'Python' in inp.detected_tech_stack

        out = PersonaForgeOutput(
            name='Daedalus',
            aleph='To construct resilient systems.',
            initial_axioms=[AxiomPayload(content='State transitions must be atomic.', scope=MemoryScope.INCARNATION)],
            initial_principles=[
                PrinciplePayload(
                    name='Symmetry',
                    avatar='Noether',
                    role='Guardian of Invariance',
                    weight=1.5,
                    constraints=['Conserve complexity'],
                )
            ],
        )
        assert out.name == 'Daedalus'
        assert len(out.initial_axioms) == 1
        assert len(out.initial_principles) == 1

    def test_dreaming_delta_schemas(self):
        inp = DreamingDeltaInput(
            session_id='session-123',
            session_notes=[{'timestamp': '2026-11-14T10:00:00Z', 'content': 'Refactored module.'}],
        )
        assert inp.session_id == 'session-123'
        assert len(inp.session_notes) == 1

        out = DreamingDeltaOutput(
            epilogue='Session complete.',
            added_memories=[
                DreamingMemoryRecord(
                    type=MemoryType.FACT,
                    scope=MemoryScope.INCARNATION,
                    content='Refactored module into domain packages.',
                )
            ],
            superseded_memories=[
                SupersessionLink(
                    superseded_id='concept-old',
                    superseding_id='concept-new',
                    reason='Updated architecture.',
                )
            ],
            tms_refutations=[
                RefutationLink(
                    refuted_id='concept-bad',
                    refuting_id='concept-good',
                    reason='Empirical refutation.',
                )
            ],
        )
        assert len(out.added_memories) == 1
        assert len(out.superseded_memories) == 1
        assert len(out.tms_refutations) == 1

    def test_dreaming_delta_legacy_memories_alias(self):
        legacy_data = {'memories': [{'type': 'fact', 'scope': 'incarnation', 'content': 'Legacy format memory.'}]}
        validated = DreamingDeltaOutput.model_validate(legacy_data)
        assert len(validated.added_memories) == 1
        assert validated.added_memories[0].content == 'Legacy format memory.'

    def test_verification_schemas(self):
        inp = VerificationInput(
            memory_id='concept-abc',
            content='Module uses WAL mode.',
            provenance=VerificationProvenance(git_sha='abcdef123456', context_ref='src/db.py#L10'),
        )
        assert inp.memory_id == 'concept-abc'
        assert inp.provenance.git_sha == 'abcdef123456'

        out = VerificationOutput(
            memory_id='concept-abc',
            status='fresh',
            confidence_adjustment=0.1,
            is_contradicted=False,
            evidence='Line 10 contains WAL configuration.',
        )
        assert out.status == 'fresh'
        assert not out.is_contradicted


class TestContractRegistry:
    def test_list_and_get_contracts(self):
        contracts = list_contracts()
        names = {c.name for c in contracts}
        assert 'forge' in names
        assert 'dreaming' in names
        assert 'verification' in names

        forge = get_contract('forge')
        assert forge.name == 'forge'
        assert forge.output_schema == PersonaForgeOutput

        # Test aliases
        assert get_contract('persona-forge') == forge
        assert get_contract('persona_forge') == forge

        with pytest.raises(KeyError, match='Unknown cognitive contract'):
            get_contract('non_existent_contract')

    def test_validate_contract(self):
        valid_payload = {
            'name': 'Icarus',
            'aleph': 'To reach the sun.',
        }
        res = validate_contract('forge', valid_payload)
        assert isinstance(res, PersonaForgeOutput)
        assert res.name == 'Icarus'

        with pytest.raises(Exception):
            validate_contract('forge', {'name': 'NoAleph'})

        # Test invalid contract name
        with pytest.raises(KeyError):
            validate_contract('fake_contract', valid_payload)


class TestContractExecutors:
    def test_apply_forge_output(self, tmp_path):
        out = PersonaForgeOutput(
            name='TestForgePersona',
            aleph='Test Aleph Purpose',
            version='1.0.0',
            description='Created by test',
            agents_md_content='# AGENTS\nOperational guidelines for testing.',
            constitution_content='---\n'
            'name: TestForgePersona\n'
            'version: 1.0.0\n'
            'aleph: Test Aleph Purpose\n'
            '---\n'
            '# Persona Constitution\n',
            initial_axioms=[AxiomPayload(content='Axiom 1: Rigor over speed.', scope=MemoryScope.INCARNATION)],
            initial_principles=[PrinciplePayload(name='Rigor', role='Testing', weight=1.0)],
        )

        base_dir = tmp_path / 'global_tur'
        workspace_dir = tmp_path / 'workspace'
        workspace_dir.mkdir(parents=True, exist_ok=True)

        persona_id, persona_name = apply_forge_output(
            out,
            base_dir=base_dir,
            workspace_dir=workspace_dir,
        )

        assert persona_name == 'TestForgePersona'
        persona_folder = base_dir / 'personas' / persona_id
        assert persona_folder.exists()
        assert (persona_folder / 'CONSTITUTION.md').exists()
        assert (persona_folder / 'persona.yaml').exists()
        assert (workspace_dir / 'AGENTS.md').exists()

        # Check seeded axioms in MemoryManager
        manager = MemoryManager(base_dir=persona_folder)
        memories = manager.load_all()
        assert any('Axiom 1: Rigor over speed.' in m.content for m in memories)

    def test_apply_dreaming_output(self, tmp_path, monkeypatch):
        # Create dummy persona
        base_dir = tmp_path / 'tur_home'
        persona_id = '11111111-2222-3333-4444-555555555555'
        persona_folder = base_dir / 'personas' / persona_id
        persona_folder.mkdir(parents=True, exist_ok=True)
        (persona_folder / 'CONSTITUTION.md').write_text('# Constitution\n', encoding='utf-8')

        # Create personas.yaml index
        import yaml

        index_data = {'personas': [{'id': persona_id, 'name': 'TestDreamPersona', 'version': '0.1.0'}]}
        (base_dir / 'personas.yaml').write_text(yaml.dump(index_data), encoding='utf-8')

        monkeypatch.setattr('tur.persona.resolve_personas_base_dir', lambda: base_dir)

        out = DreamingDeltaOutput(
            epilogue='Session finished cleanly.',
            added_memories=[
                DreamingMemoryRecord(
                    type=MemoryType.FACT,
                    scope=MemoryScope.UNIVERSAL,
                    content='Contract-driven skills eliminate prompt bloat.',
                )
            ],
            staged_core_memories=[{'content': 'Sovereign isolation is an absolute invariant.', 'scope': 'persona'}],
        )

        counts = apply_dreaming_output(out, active_id=persona_id, session_id='sess-001')
        assert counts['added'] == 1
        assert counts['staged_core'] == 1

        manager = MemoryManager(base_dir=persona_folder)
        memories = manager.load_all()
        assert any('Contract-driven skills' in m.content for m in memories)

    def test_format_contract_delegation(self):
        inp = PersonaForgeInput(project_name='delegation-test')
        prompt = format_contract_delegation(
            contract_name='forge',
            input_payload=inp,
            primary_commit_cmd="tur-adm persona init --commit '<JSON>'",
        )
        assert '# TUR DELEGATION: Forge Cognitive Delegation' in prompt
        assert 'PersonaForgeOutput' in prompt
        assert 'tur-adm persona init --commit' in prompt


class TestContractCLI:
    def test_contract_list_cli(self):
        res = runner.invoke(admin_app, ['contract', 'list'])
        assert res.exit_code == 0
        assert 'forge' in res.output
        assert 'dreaming' in res.output
        assert 'verification' in res.output

    def test_contract_list_json_cli(self):
        res = runner.invoke(admin_app, ['contract', 'list', '--json'])
        assert res.exit_code == 0
        data = json.loads(res.output)
        names = [d['name'] for d in data]
        assert 'forge' in names

    def test_contract_show_cli(self):
        res = runner.invoke(admin_app, ['contract', 'show', 'forge'])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data['title'] == 'PersonaForgeOutput'

    def test_contract_validate_cli(self, tmp_path):
        payload = {
            'name': 'CLIForgeBot',
            'aleph': 'Test aleph for CLI validation.',
        }
        json_file = tmp_path / 'valid_forge.json'
        json_file.write_text(json.dumps(payload), encoding='utf-8')

        res = runner.invoke(admin_app, ['contract', 'validate', 'forge', str(json_file)])
        assert res.exit_code == 0
        assert 'Valid PersonaForgeOutput payload' in res.output

    def test_contract_validate_cli_invalid(self, tmp_path):
        payload = {'name': 'Incomplete'}
        json_file = tmp_path / 'invalid_forge.json'
        json_file.write_text(json.dumps(payload), encoding='utf-8')

        res = runner.invoke(admin_app, ['contract', 'validate', 'forge', str(json_file)])
        assert res.exit_code == 1

    def test_persona_init_commit_cli(self, tmp_path, monkeypatch):
        base_dir = tmp_path / 'global_tur'
        monkeypatch.setattr('tur.paths.resolve_personas_base_dir', lambda: base_dir)
        monkeypatch.setattr('tur.persona.resolve_personas_base_dir', lambda: base_dir)
        monkeypatch.setattr('tur.cli.admin.resolve_personas_base_dir', lambda: base_dir)

        payload = {
            'name': 'CommitBot',
            'aleph': 'Created via CLI commit option.',
        }
        json_file = tmp_path / 'commit_persona.json'
        json_file.write_text(json.dumps(payload), encoding='utf-8')

        res = runner.invoke(admin_app, ['persona', 'init', '--commit', str(json_file)])
        assert res.exit_code == 0
        assert "Persona 'CommitBot'" in res.output
