"""
Vector Clock Module (EP-0141).

Implements Lamport Vector Clocks V in N^k for the Inter-Agent Signal Protocol (IASP).
Provides an immutable Mapping value object with formal partial ordering (N^k, <=),
lattice maximum join (|), causal precedence (<, <=), concurrent conflict detection (a || b),
and topological causal sorting.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar

T = TypeVar('T')


class VectorClock(dict[str, int]):
    """
    Immutable Lamport Vector Clock Value Object (EP-0141).

    Maintains causal invariance across distributed agent manifestations.
    Subclasses dict for zero-friction JSON serialization (json.dumps), SQLite storage,
    and Pydantic models, while providing lattice maximum join (|), strict causal partial
    ordering (<, <=), concurrency testing, and default-zero evaluation.
    """

    def __init__(self, raw: Mapping[str, int] | str | None = None) -> None:
        data: dict[str, int] = {}
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw) if raw.strip() else {}
                if isinstance(parsed, dict):
                    data = {str(k): int(v) for k, v in parsed.items() if int(v) > 0}
            except Exception:
                data = {}
        elif isinstance(raw, Mapping):
            data = {str(k): int(v) for k, v in raw.items() if int(v) > 0}

        super().__init__(data)

    def __missing__(self, key: str) -> int:
        """Evaluates logical timestamp for agent_id, defaulting to 0 for unseen agents."""
        return 0

    def __getitem__(self, key: str) -> int:
        """Evaluates logical timestamp for agent_id, defaulting to 0 for unseen agents."""
        return self.get(key, 0)

    def __hash__(self) -> int:  # type: ignore[override]
        return hash(tuple(sorted((k, v) for k, v in self.items() if v > 0)))

    def __repr__(self) -> str:
        return f'VectorClock({dict(self)})'

    # -------------------------------------------------------------------------
    # Distributed Lamport Algebra & Operators
    # -------------------------------------------------------------------------

    def tick(self, agent_id: str) -> VectorClock:
        """
        Local emission tick (Rule 1): Advances the agent's logical counter by 1.
        V_i[i] <- V_i[i] + 1
        """
        new_data = dict(self)
        new_data[agent_id] = self[agent_id] + 1
        return VectorClock(new_data)

    def __or__(self, other: Mapping[str, int]) -> VectorClock:
        """
        Pointwise lattice maximum merge (Rule 2): V_j[k] <- max(V_j[k], V_sig[k]).
        """
        all_keys = self.keys() | other.keys()
        return VectorClock({k: max(self[k], other.get(k, 0)) for k in all_keys})

    def __lt__(self, other: Mapping[str, int]) -> bool:
        """
        Strict causal precedence (Rule 3a: a < b):
        forall k: V_a[k] <= V_b[k] and exists m: V_a[m] < V_b[m]
        """
        all_keys = self.keys() | other.keys()
        if not all_keys:
            return False
        all_le = all(self[k] <= other.get(k, 0) for k in all_keys)
        exists_lt = any(self[k] < other.get(k, 0) for k in all_keys)
        return all_le and exists_lt

    def __le__(self, other: Mapping[str, int]) -> bool:
        """Causal precedence or identity (a <= b)."""
        all_keys = self.keys() | other.keys()
        return all(self[k] <= other.get(k, 0) for k in all_keys)

    def __gt__(self, other: Mapping[str, int]) -> bool:
        """
        Strict causal succession (Rule 3a dual: a > b <==> b < a):
        forall k: V_a[k] >= V_b[k] and exists m: V_a[m] > V_b[m]
        """
        all_keys = self.keys() | other.keys()
        if not all_keys:
            return False
        all_ge = all(self[k] >= other.get(k, 0) for k in all_keys)
        exists_gt = any(self[k] > other.get(k, 0) for k in all_keys)
        return all_ge and exists_gt

    def __ge__(self, other: Mapping[str, int]) -> bool:
        """Causal subsumption or identity (a >= b <==> b <= a)."""
        all_keys = self.keys() | other.keys()
        return all(self[k] >= other.get(k, 0) for k in all_keys)

    def __add__(self, other: Any) -> Any:
        """
        Defensive prohibition of arithmetic vector addition.
        Raises TypeError to prevent double-counting shared causal histories.
        """
        raise TypeError(
            "VectorClock does not support addition '+' because summing clocks double-counts causal history. "
            "Use '|' (lattice maximum join) to merge clocks, or .tick(agent_id) to advance logical time."
        )

    def is_concurrent_with(self, other: Mapping[str, int]) -> bool:
        """
        Concurrent conflict detection (Rule 3b: a || b):
        not (a <= b) and not (b <= a) and a != b
        """
        if self == other:
            return False
        return not (self <= other) and not (other <= self)

    def is_ready(self, agent_clock: Mapping[str, int], sender_id: str) -> bool:
        """
        Verifies causal delivery readiness:
        1. For sender: sig[sender] == agent[sender] + 1
        2. For others: sig[k] <= agent[k]
        """
        if not self:
            return True
        for agent, count in self.items():
            if count <= 0:
                continue
            if agent == sender_id:
                if count != agent_clock.get(agent, 0) + 1:
                    return False
            elif count > agent_clock.get(agent, 0):
                return False
        return True

    def to_dict(self) -> dict[str, int]:
        """Returns a standard dictionary copy of the non-zero vector clock components."""
        return dict(self)

    def to_json(self) -> str:
        """Serializes vector clock components to a JSON string."""
        return json.dumps(self)

    @classmethod
    def sort(
        cls,
        items: Sequence[T],
        key: Callable[[T], Mapping[str, int] | str] | None = None,
    ) -> list[T]:
        """
        Topologically sorts items according to Lamport vector clock causal partial order.
        Accepts raw VectorClock objects or any collection of items with a key extractor.
        """
        if len(items) <= 1:
            return list(items)

        def _get_clock(x: T) -> VectorClock:
            if key is not None:
                extracted = key(x)
                return extracted if isinstance(extracted, cls) else cls(extracted)
            return x if isinstance(x, cls) else cls(x)  # type: ignore[arg-type]

        result: list[T] = []
        for item in items:
            item_clock = _get_clock(item)
            inserted = False
            for idx, existing in enumerate(result):
                existing_clock = _get_clock(existing)
                if item_clock < existing_clock:
                    result.insert(idx, item)
                    inserted = True
                    break
            if not inserted:
                result.append(item)

        return result
