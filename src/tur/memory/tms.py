"""
src/tur/memory/tms.py - Active TMS Contradiction Interruption Protocol (EP-0134).

Proactively queries active Layer 1 / Layer 2 memories during ingestion (tur learn)
to detect semantic contradictions, incompatible axioms, or opposing polarities.
Enforces the Golem Core Memory Protection Invariant to prevent unapproved agent
supersession of human-governed Core and Axiom tier knowledge.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field

from tur.models import Memory, MemoryLink, MemoryScope, MemoryType
from tur.text import tokenize_words

STOPWORDS: set[str] = {
    'the',
    'a',
    'an',
    'is',
    'are',
    'was',
    'were',
    'in',
    'on',
    'at',
    'to',
    'for',
    'of',
    'with',
    'by',
    'from',
    'and',
    'or',
    'as',
    'that',
    'this',
    'it',
    'its',
    'be',
    'been',
    'being',
    'all',
    'any',
    'both',
    'each',
    'more',
    'most',
    'other',
    'some',
    'such',
    'than',
    'too',
    'very',
    'can',
    'will',
    'should',
    'would',
    'do',
    'does',
    'did',
    'having',
    'have',
    'has',
    'had',
    'via',
    'using',
    'runs',
    'run',
}

NEGATION_MARKERS: set[str] = {
    'not',
    'never',
    'no',
    'cannot',
    'neither',
    'nor',
    'deprecated',
    'removed',
    'replaces',
    'superseded',
    'disabled',
    'switched',
    'instead',
    'eliminated',
    'abandoned',
    'obsolete',
    'discontinued',
    'refuted',
    'false',
}

ANTONYM_PAIRS: list[tuple[str, str]] = [
    ('enabled', 'disabled'),
    ('enable', 'disable'),
    ('synchronous', 'asynchronous'),
    ('sync', 'async'),
    ('mutable', 'immutable'),
    ('local', 'global'),
    ('centralized', 'decentralized'),
    ('active', 'inactive'),
    ('deprecated', 'recommended'),
    ('allowed', 'forbidden'),
    ('allow', 'forbid'),
    ('true', 'false'),
    ('internal', 'external'),
    ('monolith', 'microservices'),
    ('monolithic', 'modular'),
    ('required', 'optional'),
]


class InvariantMemoryError(RuntimeError):
    """
    Raised when an agent attempts to violate, refute, or supersede human-governed
    Core or Axiom tier memories without explicit human authorization via tur-adm.
    """


class TMSConflict(BaseModel):
    """Represents a detected contradiction between an active memory and a candidate assertion."""

    existing_memory_id: str
    existing_content: str
    existing_type: MemoryType
    new_content: str
    conflict_reason: str
    is_core_or_axiom: bool = False
    suggested_action: Literal['supersede', 'refute', 'scope_branch', 'abort'] = 'supersede'
    resolution_options: list[str] = Field(default_factory=lambda: ['supersede', 'refute', 'scope_branch', 'abort'])

    def to_dict(self) -> dict[str, Any]:
        return {
            'status': 'conflict_detected',
            'conflicting_memory_id': self.existing_memory_id,
            'existing_content': self.existing_content,
            'new_content': self.new_content,
            'conflict_reason': self.conflict_reason,
            'is_core_or_axiom': self.is_core_or_axiom,
            'suggested_action': self.suggested_action,
            'resolution_options': self.resolution_options,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class TMSConflictError(RuntimeError):
    """Raised when active memory contradiction is detected at ingestion time."""

    def __init__(self, message: str, conflicts: list[TMSConflict]):
        super().__init__(message)
        self.conflicts = conflicts


class ContradictionInterceptor:
    """
    Proactively checks candidate memory assertions against active long-term memories
    for polarity conflicts, mutually exclusive assertions, and core memory violations.
    """

    def __init__(self, memory_manager: Any):
        self.memory_manager = memory_manager

    @staticmethod
    def _extract_keywords(text: str) -> set[str]:
        words = tokenize_words(text.lower())
        return {w for w in words if len(w) > 2 and w not in STOPWORDS}

    @staticmethod
    def _has_negation_divergence(words_a: set[str], words_b: set[str]) -> bool:
        neg_a = bool(words_a.intersection(NEGATION_MARKERS))
        neg_b = bool(words_b.intersection(NEGATION_MARKERS))
        return neg_a != neg_b

    @staticmethod
    def _has_antonym_divergence(words_a: set[str], words_b: set[str]) -> str | None:
        for term1, term2 in ANTONYM_PAIRS:
            if (term1 in words_a and term2 in words_b) or (term2 in words_a and term1 in words_b):
                return f"Antonym collision: '{term1}' vs '{term2}'"
        return None

    def check_conflicts(
        self,
        content: str,
        type: MemoryType = MemoryType.FACT,
        scope: MemoryScope = MemoryScope.INCARNATION,
        candidate_memories: list[Memory] | None = None,
    ) -> list[TMSConflict]:
        """
        Evaluates an incoming assertion against active memories.
        Returns a list of detected TMSConflict objects.
        """
        if not content:
            return []

        active_memories = candidate_memories
        if active_memories is None:
            all_mems = self.memory_manager.load_all(include_archived=False)
            active_memories = [
                m
                for m in all_mems
                if getattr(m, 'status', 'active') in ('active', None) and not getattr(m, 'redacted', False)
            ]

        new_words = set(tokenize_words(content.lower()))
        new_keywords = self._extract_keywords(content)

        conflicts: list[TMSConflict] = []

        for mem in active_memories:
            # Check scope relevance: incarnation checks against incarnation, persona, universal
            # Skip if comparing unrelated local contexts
            if scope == MemoryScope.INCARNATION and mem.scope not in (
                MemoryScope.INCARNATION,
                MemoryScope.UNIVERSAL,
                MemoryScope.PERSONA,
            ):
                continue

            existing_words = set(tokenize_words(mem.content.lower()))
            existing_keywords = self._extract_keywords(mem.content)

            overlap = new_keywords.intersection(existing_keywords)
            if not overlap:
                continue

            # Degree of topical overlap
            overlap_ratio = len(overlap) / max(1, min(len(new_keywords), len(existing_keywords)))

            conflict_reason: str | None = None

            # 1. Antonym divergence on shared topic
            antonym_reason = self._has_antonym_divergence(existing_words, new_words)
            if antonym_reason and (len(overlap) >= 1 or overlap_ratio >= 0.25):
                conflict_reason = antonym_reason

            # 2. Negation divergence on shared topic
            elif self._has_negation_divergence(existing_words, new_words) and (
                len(overlap) >= 2 or overlap_ratio >= 0.4
            ):
                conflict_reason = f'Polarity divergence on shared topic terms: {", ".join(sorted(overlap)[:4])}'

            # 3. Competing entity / predicate collision with high topical overlap
            # (e.g. "Database migrations run via Alembic" vs "Database migrations run via Prisma Migrate")
            elif len(overlap) >= 2 and overlap_ratio >= 0.5:
                diff_existing = existing_keywords - overlap
                diff_new = new_keywords - overlap
                if diff_existing and diff_new and (diff_existing != diff_new):
                    conflict_reason = (
                        f"Competing assertion on shared topic: '{', '.join(sorted(overlap)[:4])}' "
                        f'(existing: {", ".join(sorted(diff_existing)[:3])} vs new: {", ".join(sorted(diff_new)[:3])})'
                    )

            if conflict_reason:
                is_core = mem.type in (MemoryType.CORE, MemoryType.AXIOM)
                conflicts.append(
                    TMSConflict(
                        existing_memory_id=mem.id,
                        existing_content=mem.content,
                        existing_type=mem.type,
                        new_content=content,
                        conflict_reason=conflict_reason,
                        is_core_or_axiom=is_core,
                        suggested_action='abort' if is_core else 'supersede',
                    )
                )

        return conflicts

    def resolve_supersession(
        self,
        superseded_id: str,
        new_memory: Memory,
    ) -> Memory:
        """
        Executes supersession of an existing memory by a newly created memory.
        Enforces Golem Core Memory Protection Invariant.
        """
        all_mems = self.memory_manager.load_all()
        target_mem = next(
            (m for m in all_mems if m.id == superseded_id or m.id.startswith(superseded_id)),
            None,
        )
        if not target_mem:
            raise FileNotFoundError(f"No memory found matching ID '{superseded_id}'")

        if target_mem.type in (MemoryType.CORE, MemoryType.AXIOM):
            raise InvariantMemoryError(
                f"[Invariant Memory Error]: Assertion contradicts Invariant Memory '{target_mem.id}'. "
                'Agent cannot supersede human-governed Invariant memories. '
                'To propose a change, submit via `tur-adm proposal`.'
            )

        # Update target memory to superseded status and link to new memory
        target_mem.status = 'superseded'
        link_uri = f'tur://memory/{new_memory.id}'
        if not any(link.uri == link_uri and link.relation == 'superseded_by' for link in target_mem.links):
            target_mem.links.append(MemoryLink(uri=link_uri, relation='superseded_by'))

        # Add backlink on new memory
        backlink_uri = f'tur://memory/{target_mem.id}'
        if not any(link.uri == backlink_uri and link.relation == 'supersedes' for link in new_memory.links):
            new_memory.links.append(MemoryLink(uri=backlink_uri, relation='supersedes'))

        self.memory_manager.save(target_mem)
        return target_mem
