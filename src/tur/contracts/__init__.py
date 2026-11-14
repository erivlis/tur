"""
Contracts package for Contract-Driven Cognitive Skills & Pluggable Forge Architecture (EP-0137).
"""

from tur.contracts.dreaming import (
    CoreMemoryStaging,
    DreamingDeltaInput,
    DreamingDeltaOutput,
    DreamingMemoryRecord,
    DreamingSessionNote,
    RefutationLink,
    SupersessionLink,
)
from tur.contracts.executor import (
    apply_dreaming_output,
    apply_forge_output,
    execute_external_skill_command,
    format_contract_delegation,
)
from tur.contracts.forge import (
    AxiomPayload,
    PersonaForgeInput,
    PersonaForgeOutput,
    PrinciplePayload,
)
from tur.contracts.registry import (
    ContractDefinition,
    get_contract,
    list_contracts,
    register_contract,
    validate_contract,
)
from tur.contracts.verification import (
    VerificationInput,
    VerificationOutput,
    VerificationProvenance,
)

__all__ = [
    # Forge
    "AxiomPayload",
    "PersonaForgeInput",
    "PersonaForgeOutput",
    "PrinciplePayload",
    # Dreaming
    "CoreMemoryStaging",
    "DreamingDeltaInput",
    "DreamingDeltaOutput",
    "DreamingMemoryRecord",
    "DreamingSessionNote",
    "RefutationLink",
    "SupersessionLink",
    # Verification
    "VerificationInput",
    "VerificationOutput",
    "VerificationProvenance",
    # Registry
    "ContractDefinition",
    "get_contract",
    "list_contracts",
    "register_contract",
    "validate_contract",
    # Executor
    "apply_dreaming_output",
    "apply_forge_output",
    "execute_external_skill_command",
    "format_contract_delegation",
]
