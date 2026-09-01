from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from tur.models import Memory, MemoryScope, MemoryType
from tur.persona import get_active_persona_id, get_persona_path
from tur.session import get_active_session_id, get_parent_session_id, load_session_index


class DeltaStatus(StrEnum):
    ADDED = 'ADDED'
    SUPERSEDED = 'SUPERSEDED'
    REFUTED = 'REFUTED'
    DECAYED = 'DECAYED'
    MODIFIED = 'MODIFIED'


class MemoryDelta(BaseModel):
    """
    Epistemic classification of memory state changes across sessions (EP-0133).
    """

    status: DeltaStatus
    memory: Memory
    previous_memory: Memory | None = None
    superseded_by: str | None = None
    reason: str | None = None


def compute_memory_diff(
    base_memories: dict[str, Memory] | list[Memory],
    target_memories: dict[str, Memory] | list[Memory],
) -> list[MemoryDelta]:
    """
    Computes epistemic memory deltas between base and target memory collections.
    Categorizes changes into ADDED, SUPERSEDED, REFUTED, DECAYED, and MODIFIED.
    """
    base_map: dict[str, Memory] = base_memories if isinstance(base_memories, dict) else {m.id: m for m in base_memories}
    target_map: dict[str, Memory] = (
        target_memories if isinstance(target_memories, dict) else {m.id: m for m in target_memories}
    )

    deltas: list[MemoryDelta] = []

    # 1. Added memories (in target but not base)
    for mid, mem in target_map.items():
        if mid not in base_map:
            # Check if it was created by modifying/superseding a base memory with same content
            matching_base = next((bm for bm in base_map.values() if bm.content.strip() == mem.content.strip()), None)
            if matching_base:
                is_diff = (
                    matching_base.status != mem.status
                    or matching_base.tags != mem.tags
                    or matching_base.scope != mem.scope
                )
                if is_diff:
                    deltas.append(MemoryDelta(status=DeltaStatus.MODIFIED, memory=mem, previous_memory=matching_base))
            else:
                deltas.append(MemoryDelta(status=DeltaStatus.ADDED, memory=mem))

    # 2. Removed, Superseded, Refuted, Decayed, Modified
    for mid, base_mem in base_map.items():
        if mid in target_map:
            target_mem = target_map[mid]
            if base_mem.status != target_mem.status:
                if target_mem.status == 'superseded':
                    deltas.append(
                        MemoryDelta(
                            status=DeltaStatus.SUPERSEDED,
                            memory=target_mem,
                            previous_memory=base_mem,
                            superseded_by=target_mem.id,
                        )
                    )
                elif target_mem.status in ('falsified', 'refuted'):
                    deltas.append(
                        MemoryDelta(
                            status=DeltaStatus.REFUTED,
                            memory=target_mem,
                            previous_memory=base_mem,
                            reason=target_mem.redaction_reason or 'Status marked falsified/refuted',
                        )
                    )
                else:
                    deltas.append(MemoryDelta(status=DeltaStatus.MODIFIED, memory=target_mem, previous_memory=base_mem))
            elif 'stale' in target_mem.tags and 'stale' not in base_mem.tags:
                deltas.append(MemoryDelta(status=DeltaStatus.DECAYED, memory=target_mem, previous_memory=base_mem))
            elif (
                base_mem.content != target_mem.content
                or base_mem.tags != target_mem.tags
                or base_mem.scope != target_mem.scope
                or base_mem.type != target_mem.type
            ):
                deltas.append(MemoryDelta(status=DeltaStatus.MODIFIED, memory=target_mem, previous_memory=base_mem))
        else:
            # Base memory is not present in target
            # Check if any target memory supersedes or refutes it via links
            superseding = [
                m
                for m in target_map.values()
                if any(
                    link.uri == f'tur://memory/{mid}' and link.relation in ('supersedes', 'superseded_by')
                    for link in m.links
                )
            ]
            if superseding:
                deltas.append(
                    MemoryDelta(
                        status=DeltaStatus.SUPERSEDED,
                        memory=superseding[0],
                        previous_memory=base_mem,
                        superseded_by=superseding[0].id,
                    )
                )
            else:
                refuting = [
                    m
                    for m in target_map.values()
                    if any(
                        link.uri == f'tur://memory/{mid}' and link.relation in ('refutes', 'refuted_by')
                        for link in m.links
                    )
                ]
                if refuting:
                    deltas.append(
                        MemoryDelta(
                            status=DeltaStatus.REFUTED,
                            memory=base_mem,
                            reason=f'Refuted by memory {refuting[0].id[:8]}',
                        )
                    )
                else:
                    deltas.append(
                        MemoryDelta(
                            status=DeltaStatus.REFUTED,
                            memory=base_mem,
                            reason='Removed from active memory bank',
                        )
                    )

    return deltas


def compute_session_diff(
    base_session_id: str | None = None,
    target_session_id: str | None = None,
    persona_id: str | None = None,
    type_filter: MemoryType | str | None = None,
    scope_filter: MemoryScope | str | None = None,
) -> list[MemoryDelta]:
    """
    Computes memory delta for a specific session against its predecessor (EP-0130 lineage)
    or between two explicitly provided session IDs (EP-0133).
    """
    from tur.memory import MemoryManager

    active_id = persona_id or get_active_persona_id()
    persona_dir = get_persona_path(active_id)
    mem_mgr = MemoryManager(base_dir=persona_dir)

    all_memories = mem_mgr.load_all(include_archived=True) + mem_mgr.load_subsumed()
    all_map = {m.id: m for m in all_memories}

    resolved_target = target_session_id or get_active_session_id()
    resolved_base = base_session_id

    if not resolved_target:
        index = load_session_index(persona_dir)
        if index.sessions:
            s_sorted = sorted(index.sessions, key=lambda s: (s.updated_at, s.created_at, s.id), reverse=True)
            resolved_target = s_sorted[0].id
            if len(s_sorted) > 1 and resolved_base is None:
                resolved_base = s_sorted[1].id

    if resolved_target and resolved_base is None:
        resolved_base = get_parent_session_id(resolved_target, persona_dir)

    if resolved_target and resolved_base:
        base_mems = {m.id: m for m in all_map.values() if m.source_session == resolved_base}
        target_mems = {m.id: m for m in all_map.values() if m.source_session == resolved_target}
    elif resolved_target:
        base_mems = {}
        target_mems = {m.id: m for m in all_map.values() if m.source_session == resolved_target}
    else:
        base_mems = {}
        target_mems = {}

    deltas = compute_memory_diff(base_mems, target_mems)

    # Filter by type or scope if requested
    if type_filter:
        t_val = type_filter.value if hasattr(type_filter, 'value') else str(type_filter).lower()
        deltas = [
            d
            for d in deltas
            if (d.memory.type.value if hasattr(d.memory.type, 'value') else str(d.memory.type)).lower() == t_val
        ]
    if scope_filter:
        s_val = scope_filter.value if hasattr(scope_filter, 'value') else str(scope_filter).lower()
        deltas = [
            d
            for d in deltas
            if (d.memory.scope.value if hasattr(d.memory.scope, 'value') else str(d.memory.scope)).lower() == s_val
        ]

    return deltas


def format_diff_terminal(deltas: list[MemoryDelta], session_id: str | None = None) -> str:
    """
    Renders styled terminal output for memory deltas according to EP-0133 specification.
    """
    header = f'Memory Delta: Session {session_id or "active"} ({len(deltas)} mutation{"s" if len(deltas) != 1 else ""})'
    if not deltas:
        return f'{header}\n\n[dim]No memory mutations detected.[/dim]'

    lines: list[str] = [f'[bold]{header}[/bold]', '']

    for d in deltas:
        m_type = d.memory.type.value if hasattr(d.memory.type, 'value') else str(d.memory.type)
        t_name = m_type.capitalize()
        s_name = d.memory.scope.value if hasattr(d.memory.scope, 'value') else str(d.memory.scope)
        short_id = d.memory.id[:8]

        match d.status:
            case DeltaStatus.ADDED:
                lines.append(f'[bold green][+] ADDED ({t_name})[/bold green]')
                lines.append(f'    id: {short_id}')
                lines.append(f'    scope: {s_name}')
                lines.append(f'    content: "{d.memory.content.strip()}"')
                lines.append('')

            case DeltaStatus.SUPERSEDED:
                lines.append(f'[bold yellow][~] SUPERSEDED ({t_name})[/bold yellow]')
                prev_id = d.previous_memory.id[:8] if d.previous_memory else 'unknown'
                lines.append(f'    id: {prev_id} -> superseded by {short_id}')
                if d.previous_memory:
                    lines.append(f'    old: "{d.previous_memory.content.strip()}"')
                lines.append(f'    new: "{d.memory.content.strip()}"')
                lines.append('')

            case DeltaStatus.REFUTED:
                lines.append(f'[bold red][-] REFUTED ({t_name})[/bold red]')
                lines.append(f'    id: {short_id}')
                lines.append(f'    content: "{d.memory.content.strip()}"')
                if d.reason:
                    lines.append(f'    reason: "{d.reason}"')
                lines.append('')

            case DeltaStatus.DECAYED:
                lines.append(f'[bold magenta][*] DECAYED ({t_name})[/bold magenta]')
                lines.append(f'    id: {short_id}')
                lines.append(f'    content: "{d.memory.content.strip()}"')
                lines.append('    status: fresh -> stale')
                lines.append('')

            case DeltaStatus.MODIFIED:
                lines.append(f'[bold cyan][~] MODIFIED ({t_name})[/bold cyan]')
                lines.append(f'    id: {short_id}')
                if d.previous_memory:
                    lines.append(f'    old: "{d.previous_memory.content.strip()}"')
                lines.append(f'    new: "{d.memory.content.strip()}"')
                lines.append('')

    return '\n'.join(lines).rstrip()


def format_diff_summary(deltas: list[MemoryDelta]) -> str:
    """
    Renders the Markdown summary for session consolidation / sleep epilogue (EP-0133).
    """
    added_by_type: dict[str, int] = {}
    superseded_count = 0
    refuted_count = 0
    decayed_count = 0

    for d in deltas:
        match d.status:
            case DeltaStatus.ADDED:
                t = d.memory.type.value if hasattr(d.memory.type, 'value') else str(d.memory.type)
                added_by_type[t] = added_by_type.get(t, 0) + 1
            case DeltaStatus.SUPERSEDED:
                superseded_count += 1
            case DeltaStatus.REFUTED:
                refuted_count += 1
            case DeltaStatus.DECAYED:
                decayed_count += 1

    added_str = (
        ', '.join(f'{count} {t}{"s" if count > 1 else ""}' for t, count in added_by_type.items())
        if added_by_type
        else '0'
    )

    return (
        '## Session Memory Ledger Delta\n'
        f'- Added: {added_str}\n'
        f'- Superseded: {superseded_count}\n'
        f'- Refuted: {refuted_count}\n'
        f'- Stale flagged: {decayed_count}'
    )


def format_diff_json(deltas: list[MemoryDelta]) -> list[dict[str, Any]]:
    """
    Renders structured JSON array for MCP and programmatic consumption (EP-0133).
    """
    results: list[dict[str, Any]] = []
    for d in deltas:
        item: dict[str, Any] = {
            'status': d.status.value,
            'id': d.memory.id,
            'type': d.memory.type.value if hasattr(d.memory.type, 'value') else str(d.memory.type),
            'scope': d.memory.scope.value if hasattr(d.memory.scope, 'value') else str(d.memory.scope),
            'content': d.memory.content,
            'source_session': d.memory.source_session,
        }
        if d.previous_memory:
            item['previous_id'] = d.previous_memory.id
            item['previous_content'] = d.previous_memory.content
        if d.superseded_by:
            item['superseded_by'] = d.superseded_by
        if d.reason:
            item['reason'] = d.reason
        results.append(item)
    return results
