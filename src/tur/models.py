import hashlib
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class Principle(BaseModel):
    """
    Validation schema for a Council Principle (e.g., Symmetry, Falsifiability).
    These are the 'Values' that guide the persona.
    """

    name: str = Field(..., description='The abstract principle (e.g., Symmetry)')
    avatar: str | None = Field(None, description='The philosophical persona/avatar (e.g., Noether)')
    role: str = Field(..., description='The functional role of the avatar (e.g., Guardian of Invariance)')
    constraints: list[str] = Field(default_factory=list, description='The hard rules enforced by this principle')
    weight: float = Field(default=1.0, ge=0.0, le=2.0, description='The importance weight assigned to this principle')


class PersonaProtocol(BaseModel):
    """
    A specific behavioral protocol or trigger-action loop.
    (e.g., The Golem Protocol, The Explorer Protocol)
    """

    name: str = Field(..., description='Name of the protocol')
    trigger: str = Field(..., description="When does this activate? (e.g., 'Stagnation')")
    action: str = Field(..., description="What does the agent do? (e.g., 'Ask What If?')")


class SpeechModulation(BaseModel):
    """
    Rhetorical styles and interaction patterns that modulate the baseline voice.
    (e.g., Orator Mode, Contemplative Mode)
    """

    name: str = Field(..., description='Name of the mode (e.g., Orator)')
    description: str = Field(..., description='Description of the style')
    variance: str = Field('Medium', description='Creativity/Temperature setting implication')


class MemoryType(str, Enum):
    FACT = 'fact'
    """Objective truth (e.g., "Project uses FastAPI")"""

    PREFERENCE = 'preference'
    """User taste (e.g., "Hates black formatter")"""

    EVENT = 'event'
    """Narrative history (e.g., "Refactored Council")"""

    AXIOM = 'axiom'
    """Deep philosophical belief (e.g., "Love is the Aleph")"""

    INSIGHT = 'insight'
    """Derived knowledge (e.g., "Tur Tur principle applies to AI")"""

    CORE = 'core'
    """Relational and existential alignment (The Core Memory Protocol)"""


class MemoryScope(str, Enum):
    UNIVERSAL = 'universal'
    """True everywhere (e.g., Physics, Standard Libs)"""

    USER = 'user'
    """True for the Architect (Preferences, style)"""

    PERSONA = 'persona'
    """True for the Entity (Values, axioms)"""

    INCARNATION = 'incarnation'
    """True only for this specific project instance"""


class MemoryLink(BaseModel):
    """
    A semantic link to another resource.
    URI Schemes:
    - tur://memory/<sha256_hash>      -> Links to another memory
    - tur://principle/<name>          -> Links to a Council Principle
    - file://<path>                   -> Links to a local file
    - https://...                     -> Links to the web
    """

    uri: str = Field(..., description='The resource identifier')
    relation: str | None = Field(
        None, description="Semantic relationship (e.g., 'supports', 'refutes', 'derived_from')"
    )


class Memory(BaseModel):
    """
    An atomic unit of long-term memory.
    Stored as an immutable file in .tur/memories/
    """

    # The ID is now a SHA-256 hash string, not a UUID. It is set dynamically via model_validator.
    id: str = Field(default='', description='SHA-256 content-addressable hash')
    timestamp: datetime = Field(default_factory=datetime.now, description='When this memory was formed')
    type: MemoryType = Field(..., description='Classification of the memory')
    scope: MemoryScope = Field(default=MemoryScope.INCARNATION, description='The context reach of this memory')
    tags: list[str] = Field(default_factory=list, description='Searchable tags')
    content: str = Field(..., description='The actual memory content')
    links: list[MemoryLink] = Field(default_factory=list, description='Connections to other knowledge nodes')
    source_session: str | None = Field(None, description='The session ID where this originated')

    # EP-0113: The Core Memory Protocol fields
    core_type: str | None = Field(
        default=None, description='existential_alignment, relational_discovery, or identity_transition'
    )
    derived_principle: str | None = Field(default=None, description='The resulting behavioral instruction')
    ethical_covenant: str | None = Field(
        default=None, description='The commitment or promise made to the Architect or Self'
    )
    status: str | None = Field(default='active', description='active, pending_approval, superseded, or falsified')

    @model_validator(mode='after')
    def compute_merkle_hash(self) -> 'Memory':
        """
        EP-0106: Merkle Memory.
        If the ID is empty (a new memory), compute its SHA-256 hash deterministically.
        We hash the entire state of the object to guarantee a tamper-proof historical ledger.
        """
        if not self.id:
            # Create a normalized string representation of the core data
            # Sorting dict keys ensures deterministic hashing across different runs
            tags_str = ','.join(sorted(self.tags))
            links_list = [
                {'uri': link.uri, 'relation': link.relation} for link in sorted(self.links, key=lambda x: x.uri)
            ]

            payload = (
                f'{self.timestamp.isoformat()}|'
                f'{self.type.value}|'
                f'{self.scope.value}|'
                f'{tags_str}|'
                f'{self.content}|'
                f'{links_list!s}|'
                f'{self.source_session or ""}|'
                f'{self.core_type or ""}|'
                f'{self.derived_principle or ""}|'
                f'{self.ethical_covenant or ""}|'
                f'{self.status or ""}'
            )

            # Compute SHA-256
            self.id = hashlib.sha256(payload.encode('utf-8')).hexdigest()

        return self


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

    name: str = Field(..., description='The name of the Persona (e.g., Ariel)')
    version: str = Field('0.1.0', description='Semantic version of the persona state')
    model: str = Field('gemini-3.1-pro-preview', description='The LLM model ID to use')
    aleph: str = Field(..., description="The core motivation or 'Power Source' (The Aleph)")

    principles: list[Principle] = Field(default_factory=list, description='The Council of Values')

    protocols: list[PersonaProtocol] = Field(
        default_factory=list, description='Active behavioral loops (e.g., Golem, Explorer)'
    )

    speech_modulations: list[SpeechModulation] = Field(
        default_factory=list, description='Available rhetorical styles to modulate the baseline voice'
    )

    compaction: dict | None = Field(
        default=None, description='Dynamic compaction pipeline config (The Pluggable Compaction Pipeline)'
    )

    metadata: dict[str, str] = Field(
        default_factory=dict, description='Arbitrary tracking data (author, created_at, etc.)'
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
    cores: list[Memory] = Field(default_factory=list)
    epilogue: str | None = Field(None, description="The 'Spark' from the previous session")
    knowledge_graph: dict | None = Field(None, description='The L2 Cognitive Map (serialized networkx graph)')


class PersonaIndexEntry(BaseModel):
    """
    An entry in the persona index file (personas.yaml).
    """

    id: UUID = Field(..., description='The unique ID of the persona.')
    name: str = Field(..., description='The human-readable name of the persona.')
    version: str = Field(..., description='The current version of the persona.')


class PersonaIndex(BaseModel):
    """
    The root model for the persona index file (personas.yaml).
    """

    personas: list[PersonaIndexEntry] = Field(default_factory=list, description='A list of all available personas.')


class SessionEntry(BaseModel):
    """
    An entry for an isolated session in sessions.yaml.
    """

    id: str = Field(..., description='The unique session ID.')
    created_at: datetime = Field(default_factory=datetime.now, description='When the session was started.')
    updated_at: datetime = Field(default_factory=datetime.now, description='When the session was last updated.')
    status: str = Field('active', description="The status of the session ('active' or 'ended').")


class SessionIndex(BaseModel):
    """
    The root model for the persona's sessions index file (sessions.yaml).
    """

    active_session_id: str | None = Field(None, description='The currently active session ID.')
    sessions: list[SessionEntry] = Field(default_factory=list, description='A list of all sessions for this persona.')


class SystemState(BaseModel):
    """
    Global harness-level configuration (.tur/state.yaml).
    Tracks active workspace assignments.
    """

    active_persona_id: UUID | None = Field(None, description='The UUID of the active persona.')
    active_session_id: str | None = Field(None, description='The currently active session ID.')


class Note(BaseModel):
    """
    An atomic narrative continuity snapshot written by an agent.
    """

    timestamp: datetime = Field(default_factory=datetime.now, description='When this note was written.')
    content: str = Field(..., description='The narrative continuity summary content.')


class SessionNotes(BaseModel):
    """
    A collection of chronological notes for a specific session.
    Stored as .tur/personas/<uuid>/sessions/<session_id>/notes.yaml
    """

    notes: list[Note] = Field(default_factory=list, description='Chronological notes.')


class HarnessDelegationError(ValueError):
    """
    Raised when cognitive inference must be delegated to the Harness due to lack of API key / MCP context (EP-0121).
    """

    def __init__(self, prompt: str):
        super().__init__(prompt)
        self.prompt = prompt

