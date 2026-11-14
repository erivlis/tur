"""
Pydantic contracts for interactive persona forging and scaffolding (EP-0137).
"""

from typing import Any

from pydantic import BaseModel, Field

from tur.models import MemoryScope


class PrinciplePayload(BaseModel):
    """A principle to be embedded in the persona constitution."""

    name: str = Field(..., description="Principle name (e.g. 'Symmetry', 'Containment').")
    avatar: str | None = Field(None, description="Philosophical avatar (e.g. 'Noether', 'The Maharal').")
    role: str = Field(..., description="Functional role (e.g. 'Guardian of Invariance').")
    weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Importance weight [0.0..2.0].")
    constraints: list[str] = Field(default_factory=list, description="Hard invariant constraints.")


class AxiomPayload(BaseModel):
    """An initial core memory axiom to seed in the ledger."""

    content: str = Field(..., description="The axiom or immutable invariant statement.")
    scope: MemoryScope | str = Field(
        default=MemoryScope.INCARNATION,
        description="The scope of this axiom (incarnation, universal, persona, user).",
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score [0.0..1.0].")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization.")


class PersonaForgeInput(BaseModel):
    """Context input payload provided to the persona forge skill."""

    project_name: str = Field(..., description="The name of the target repository or project.")
    project_root: str = Field(default=".", description="Filesystem root of the workspace.")
    detected_tech_stack: list[str] = Field(
        default_factory=list,
        description="Detected languages, libraries, and frameworks.",
    )
    target_harnesses: list[str] = Field(
        default_factory=list,
        description="Target coding agent harnesses (e.g. claude-code, antigravity, pycharm).",
    )
    user_directives: dict[str, Any] = Field(
        default_factory=dict,
        description="User-supplied goals, desired timbre, and architectural preferences.",
    )


class PersonaForgeOutput(BaseModel):
    """Target output schema returned by the persona forge skill."""

    name: str = Field(..., description="The persona name (e.g. 'Ariel', 'Daedalus').")
    aleph: str = Field(..., description="The Aleph: the persona's core existential axiom or purpose.")
    version: str = Field(default="0.1.0", description="Initial semantic version string.")
    model: str = Field(default="gemini-3.1-pro-preview", description="Recommended inference model substrate.")
    description: str | None = Field(None, description="High-level description of the persona.")
    agents_md_content: str = Field(
        default="",
        description="Rendered markdown guidelines for repository root AGENTS.md.",
    )
    constitution_content: str = Field(
        default="",
        description="Rendered markdown for CONSTITUTION.md.",
    )
    initial_axioms: list[AxiomPayload] = Field(
        default_factory=list,
        description="Initial seed axioms to insert into the memory ledger.",
    )
    initial_principles: list[PrinciplePayload] = Field(
        default_factory=list,
        description="Constitutional principles guiding the persona.",
    )
