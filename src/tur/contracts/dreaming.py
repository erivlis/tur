"""
Pydantic contracts for dreaming compaction and session delta extraction (EP-0137).
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from tur.models import MemoryScope, MemoryType


class DreamingSessionNote(BaseModel):
    """A chronological session note from the active session scratchpad."""

    timestamp: str | datetime = Field(..., description="Timestamp of the note.")
    content: str = Field(..., description="Note text content.")


class DreamingDeltaInput(BaseModel):
    """Context input payload provided to the dreaming compactor skill."""

    session_id: str = Field(..., description="Unique ID of the session being dehydrated.")
    session_notes: list[DreamingSessionNote] = Field(
        default_factory=list,
        description="Chronological notes recorded during the session.",
    )
    active_l2_graph: dict[str, Any] = Field(
        default_factory=dict,
        description="Active L2 cognitive map nodes and edges before compaction.",
    )
    chat_log: str = Field(
        default="",
        description="Optional full session chat log or transcript.",
    )


class SupersessionLink(BaseModel):
    """Link indicating that an older memory is superseded by a newer one."""

    superseded_id: str = Field(..., description="Memory ID being superseded/replaced.")
    superseding_id: str = Field(..., description="New memory ID that supersedes it.")
    reason: str | None = Field(None, description="Explanation for the supersession.")


class RefutationLink(BaseModel):
    """Link recording a TMS contradiction and refutation."""

    refuted_id: str = Field(..., description="Memory ID being refuted.")
    refuting_id: str = Field(..., description="Memory ID providing counter-evidence.")
    reason: str | None = Field(None, description="Detailed refutation rationale.")


class CoreMemoryStaging(BaseModel):
    """A high-leverage memory candidate staged for constitutional elevation."""

    content: str = Field(..., description="Candidate core principle or existential alignment.")
    principle: str | None = Field(None, description="Related Council principle name if applicable.")
    type: str = Field(default="axiom", description="Type of core candidate (axiom, covenant).")
    scope: MemoryScope | str = Field(default=MemoryScope.PERSONA, description="Target scope.")


class DreamingMemoryRecord(BaseModel):
    """An individual memory item to be recorded into the persistent L1 ledger."""

    id: str | None = Field(None, description="Optional explicit hash ID or semantic identifier.")
    type: MemoryType | str = Field(
        default=MemoryType.FACT,
        description="Memory classification (fact, preference, insight, axiom, core, event).",
    )
    scope: MemoryScope | str = Field(
        default=MemoryScope.INCARNATION,
        description="Scope of applicability (incarnation, universal, persona, user).",
    )
    content: str = Field(..., description="Durable memory content.")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score.")
    tags: list[str] = Field(default_factory=list, description="Categorical tags.")


class DreamingDeltaOutput(BaseModel):
    """Target output schema returned by the dreaming compactor skill."""

    epilogue: str = Field(
        default="",
        description="Consolidated narrative epilogue / spark summarizing the session.",
    )
    added_memories: list[DreamingMemoryRecord] = Field(
        default_factory=list,
        description="New durable L1 memories extracted from the session.",
    )
    superseded_memories: list[SupersessionLink] = Field(
        default_factory=list,
        description="Outdated memory references superseded by newer discoveries.",
    )
    tms_refutations: list[RefutationLink] = Field(
        default_factory=list,
        description="TMS contradiction refutations derived during dreaming.",
    )
    staged_core_memories: list[CoreMemoryStaging] = Field(
        default_factory=list,
        description="Memories nominated for constitutional elevation or Tether anchor.",
    )

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "DreamingDeltaOutput":
        if isinstance(obj, dict) and "memories" in obj and "added_memories" not in obj:
            obj = dict(obj)
            obj["added_memories"] = obj.pop("memories")
        return super().model_validate(obj, *args, **kwargs)

