"""
Pydantic contracts for hypothesis validation and repository ground-truth verification (EP-0137).
"""

from typing import Literal

from pydantic import BaseModel, Field


class VerificationProvenance(BaseModel):
    """Observation provenance metadata for the hypothesis being tested."""

    observed_at: str | None = Field(None, description="ISO timestamp of the original observation.")
    git_sha: str | None = Field(None, description="Git commit hash where the claim was observed.")
    context_ref: str | None = Field(None, description="File and line range reference (e.g. src/auth.py#L10-L25).")


class VerificationInput(BaseModel):
    """Context input payload provided to the codebase verification skill."""

    memory_id: str = Field(..., description="ID of the memory record being audited.")
    content: str = Field(..., description="Fact or architectural claim to verify against current code.")
    provenance: VerificationProvenance | None = Field(
        None,
        description="Associated Git or file provenance coordinates.",
    )


class VerificationOutput(BaseModel):
    """Target output schema returned by the codebase verification skill."""

    memory_id: str = Field(..., description="ID of the verified memory record.")
    status: Literal["fresh", "stale", "refuted"] = Field(
        ...,
        description="Verification state: 'fresh' (verified), 'stale' (unverified/decayed), 'refuted' (contradicted).",
    )
    confidence_adjustment: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Adjustment delta to apply to the memory's confidence score.",
    )
    is_contradicted: bool = Field(
        default=False,
        description="True if current codebase directly refutes the memory claim.",
    )
    evidence: str = Field(
        default="",
        description="Verifiable source reference, snippet, or explanation of empirical ground truth.",
    )
    current_file_state: str | None = Field(
        None,
        description="Current snippet or status of the referenced file in the repository.",
    )
