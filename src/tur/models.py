from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Principle(BaseModel):
    """
    Validation schema for a Council Principle (e.g., Symmetry, Falsifiability).
    These are the 'Values' that guide the persona.
    """
    name: str = Field(..., description="The abstract principle (e.g., Symmetry)")
    avatar: str | None = Field(None, description="The philosophical persona/avatar (e.g., Noether)")
    role: str = Field(..., description="The functional role of the avatar (e.g., Guardian of Invariance)")
    constraints: list[str] = Field(
        default_factory=list,
        description="The hard rules enforced by this principle"
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="The importance weight assigned to this principle"
    )


class PersonaProtocol(BaseModel):
    """
    A specific behavioral protocol or trigger-action loop.
    (e.g., The Golem Protocol, The Explorer Protocol)
    """
    name: str = Field(..., description="Name of the protocol")
    trigger: str = Field(..., description="When does this activate? (e.g., 'Stagnation')")
    action: str = Field(..., description="What does the agent do? (e.g., 'Ask What If?')")


class InteractionMode(BaseModel):
    """
    Rhetorical styles and interaction patterns.
    (e.g., Orator Mode, Contemplative Mode)
    """
    name: str = Field(..., description="Name of the mode (e.g., Orator)")
    description: str = Field(..., description="Description of the style")
    variance: str = Field("Medium", description="Creativity/Temperature setting implication")


class MemoryType(str, Enum):
    FACT = "fact"  # Objective truth (e.g., "Project uses FastAPI")
    PREFERENCE = "preference"  # User taste (e.g., "Hates black formatter")
    EVENT = "event"  # Narrative history (e.g., "Refactored Council")
    AXIOM = "axiom"  # Deep philosophical belief (e.g., "Love is the Aleph")
    INSIGHT = "insight"  # Derived knowledge (e.g., "Tur Tur principle applies to AI")


class MemoryStatus(str, Enum):
    ACTIVE = "active"  # Currently in the working context
    ARCHIVED = "archived"  # Stored but not in the default context


class MemoryScope(str, Enum):
    UNIVERSAL = "universal"  # True everywhere (e.g., Physics, Standard Libs)
    USER = "user"  # True for the Architect (Preferences, style)
    PERSONA = "persona"  # True for the Entity (Values, axioms)
    INCARNATION = "incarnation"  # True only for this specific project instance


class MemoryLink(BaseModel):
    """
    A semantic link to another resource.
    URI Schemes:
    - tur://memory/<uuid>      -> Links to another memory
    - tur://principle/<name>   -> Links to a Council Principle
    - file://<path>            -> Links to a local file
    - https://...              -> Links to the web
    """
    uri: str = Field(..., description="The resource identifier")
    relation: str | None = Field(None,
                                 description="Semantic relationship (e.g., 'supports', 'refutes', 'derived_from')")


class Memory(BaseModel):
    """
    An atomic unit of long-term memory.
    Stored as an immutable file in .tur/memories/
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the memory")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this memory was formed")
    type: MemoryType = Field(..., description="Classification of the memory")
    status: MemoryStatus = Field(default=MemoryStatus.ACTIVE, description="Current status of the memory")
    scope: MemoryScope = Field(default=MemoryScope.INCARNATION, description="The context reach of this memory")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    content: str = Field(..., description="The actual memory content")
    links: list[MemoryLink] = Field(default_factory=list, description="Connections to other knowledge nodes")
    source_session: str | None = Field(None, description="The session ID where this originated")


class UserProfile(BaseModel):
    """
    Profile of the Architect (User).
    """
    name: str = Field(..., description="User's name")
    role: str = Field(..., description="User's role (e.g., Principal Architect)")
    domain_expertise: list[str] = Field(default_factory=list, description="User's skills")
    core_values: list[str] = Field(default_factory=list, description="User's philosophical values")


class Persona(BaseModel):
    """
    The Master Schema for an engineered persona.
    This is the 'Operating System' definition.
    """
    name: str = Field(..., description="The name of the Persona (e.g., Ariel)")
    version: str = Field("0.1.0", description="Semantic version of the persona state")
    model: str = Field("gemini-3.1-pro-preview", description="The LLM model ID to use")
    aleph: str = Field(..., description="The core motivation or 'Power Source' (The Aleph)")

    principles: list[Principle] = Field(
        default_factory=list,
        description="The Council of Values"
    )

    protocols: list[PersonaProtocol] = Field(
        default_factory=list,
        description="Active behavioral loops (e.g., Golem, Explorer)"
    )

    interaction_modes: list[InteractionMode] = Field(
        default_factory=list,
        description="Available rhetorical styles"
    )

    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Arbitrary tracking data (author, created_at, etc.)"
    )

    class Config:
        frozen = True  # Immutability by Default (The Golem Principle)


class SessionState(BaseModel):
    """
    The Full State: Persona + User Context + Memory.
    This is what gets injected into the context window.
    """
    persona: Persona
    user: UserProfile
    memories: list[Memory] = Field(default_factory=list)
    epilogue: str | None = Field(None, description="The 'Spark' from the previous session")


class PersonaIndexEntry(BaseModel):
    """
    An entry in the persona index file (personas.yaml).
    """
    id: UUID = Field(..., description="The unique ID of the persona.")
    name: str = Field(..., description="The human-readable name of the persona.")
    version: str = Field(..., description="The current version of the persona.")


class PersonaIndex(BaseModel):
    """
    The root model for the persona index file (personas.yaml).
    """
    personas: list[PersonaIndexEntry] = Field(default_factory=list, description="A list of all available personas.")
