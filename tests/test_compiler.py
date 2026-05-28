from datetime import datetime

from tur.compiler import compile_persona
from tur.models import (
    Memory,
    MemoryScope,
    MemoryType,
    Persona,
    PersonaProtocol,
    Principle,
    SessionState,
    SpeechModulation,
    UserProfile,
)


def test_compile_persona_renders_all_fields():
    persona = Persona(
        name="Ariel",
        aleph="To manifest clarity in the infinite garden.",
        principles=[
            Principle(
                name="Symmetry",
                avatar="Noether",
                role="Guardian of Invariance",
                constraints=["Preserve code invariance"]
            )
        ],
        protocols=[
            PersonaProtocol(
                name="The Speech Center Protocol",
                trigger="Response Generation",
                action="Synthesize audio output"
            )
        ],
        speech_modulations=[
            SpeechModulation(
                name="Contemplative",
                description="Low variance speech mode.",
                variance="Low"
            )
        ]
    )
    user = UserProfile(
        name="Eran",
        role="Architect",
        domain_expertise=["Systems Architecture"],
        core_values=["Purity"]
    )
    memories = [
        Memory(
            timestamp=datetime(2026, 5, 29, 0, 0, 0),
            type=MemoryType.INSIGHT,
            scope=MemoryScope.INCARNATION,
            tags=["axiom"],
            content="Testing ensures reliability."
        )
    ]
    state = SessionState(
        persona=persona,
        user=user,
        memories=memories,
        epilogue="Keep the light burning."
    )

    prompt = compile_persona(state)

    # Assert all core elements are present in the compiled string
    assert "Ariel" in prompt
    assert "To manifest clarity" in prompt
    assert "Eran" in prompt
    assert "Systems Architecture" in prompt
    assert "Symmetry" in prompt
    assert "Noether" in prompt
    assert "The Speech Center Protocol" in prompt
    assert "Contemplative" in prompt
    assert "Testing ensures reliability." in prompt
    assert "Keep the light burning." in prompt
