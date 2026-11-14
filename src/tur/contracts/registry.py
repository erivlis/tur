"""
Canonical registry and validation routines for Cognitive Skill Contracts (EP-0137).
"""

import json
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from tur.contracts.dreaming import DreamingDeltaInput, DreamingDeltaOutput
from tur.contracts.forge import PersonaForgeInput, PersonaForgeOutput
from tur.contracts.verification import VerificationInput, VerificationOutput


@dataclass(frozen=True)
class ContractDefinition:
    """Metadata and schemas defining a cognitive skill contract."""

    name: str
    aliases: list[str] = field(default_factory=list)
    input_schema: type[BaseModel] = BaseModel
    output_schema: type[BaseModel] = BaseModel
    description: str = ''


_REGISTRY: dict[str, ContractDefinition] = {}


def register_contract(definition: ContractDefinition) -> None:
    """Registers a contract definition under its primary name and all aliases."""
    _REGISTRY[definition.name.lower()] = definition
    for alias in definition.aliases:
        _REGISTRY[alias.lower()] = definition


def get_contract(name: str) -> ContractDefinition:
    """Retrieves a contract definition by name or alias."""
    key = name.strip().lower()
    if key not in _REGISTRY:
        available = sorted({c.name for c in _REGISTRY.values()})
        raise KeyError(f"Unknown cognitive contract '{name}'. Available contracts: {', '.join(available)}")
    return _REGISTRY[key]


def list_contracts() -> list[ContractDefinition]:
    """Returns all unique registered contract definitions."""
    seen: set[str] = set()
    result: list[ContractDefinition] = []
    for defn in _REGISTRY.values():
        if defn.name not in seen:
            seen.add(defn.name)
            result.append(defn)
    return sorted(result, key=lambda c: c.name)


def validate_contract(
    name: str,
    payload: Any,
    is_output: bool = True,
) -> BaseModel:
    """
    Validates a raw payload (dict, JSON string, or model instance) against a registered contract.
    """
    contract = get_contract(name)
    target_schema = contract.output_schema if is_output else contract.input_schema

    if isinstance(payload, target_schema):
        return payload

    if isinstance(payload, str):
        cleaned = payload.strip()
        # strip markdown fences if present
        if cleaned.startswith('```'):
            lines = cleaned.splitlines()
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].startswith('```'):
                lines = lines[:-1]
            cleaned = '\n'.join(lines).strip()
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Payload for contract '{name}' is not valid JSON: {e}") from e
    elif isinstance(payload, dict):
        data = payload
    else:
        raise TypeError(
            f'Expected dict, JSON string, or {target_schema.__name__} instance, got {type(payload).__name__}'
        )

    return target_schema.model_validate(data)


# Built-in Contract Registrations
register_contract(
    ContractDefinition(
        name='forge',
        aliases=['persona-forge', 'persona_forge', 'persona_init'],
        input_schema=PersonaForgeInput,
        output_schema=PersonaForgeOutput,
        description='Interactive persona genesis, scaffolding, and constitutional crystallization.',
    )
)

register_contract(
    ContractDefinition(
        name='dreaming',
        aliases=['dreaming-compactor', 'dreaming_compactor', 'compactor', 'sleep'],
        input_schema=DreamingDeltaInput,
        output_schema=DreamingDeltaOutput,
        description='Dehydrates session notes and chat logs into durable L1 memories and L2 graph deltas.',
    )
)

register_contract(
    ContractDefinition(
        name='verification',
        aliases=['codebase-verification', 'codebase_verification', 'verify'],
        input_schema=VerificationInput,
        output_schema=VerificationOutput,
        description='Audits working memory claims against Git repository and filesystem ground truth.',
    )
)
