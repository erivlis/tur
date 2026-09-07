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
        name='Ariel',
        aleph='To manifest clarity in the infinite garden.',
        principles=[
            Principle(
                name='Symmetry',
                avatar='Noether',
                role='Guardian of Invariance',
                constraints=['Preserve code invariance'],
            )
        ],
        protocols=[
            PersonaProtocol(
                name='The Speech Center Protocol', trigger='Response Generation', action='Synthesize audio output'
            )
        ],
        speech_modulations=[
            SpeechModulation(name='Contemplative', description='Low variance speech mode.', variance='Low')
        ],
    )
    user = UserProfile(name='Eran', role='Architect', domain_expertise=['Systems Architecture'], core_values=['Purity'])
    memories = [
        Memory(
            timestamp=datetime(2026, 5, 29, 0, 0, 0),
            type=MemoryType.INSIGHT,
            scope=MemoryScope.INCARNATION,
            tags=['axiom'],
            content='Testing ensures reliability.',
        )
    ]
    state = SessionState(persona=persona, user=user, memories=memories, epilogue='Keep the light burning.')

    prompt = compile_persona(state)

    # Assert all core elements are present in the compiled string
    assert 'Ariel' in prompt
    assert 'To manifest clarity' in prompt
    assert 'Eran' in prompt
    assert 'Systems Architecture' in prompt
    assert 'Symmetry' in prompt
    assert 'Noether' in prompt
    assert 'The Speech Center Protocol' in prompt
    assert 'Contemplative' in prompt
    assert 'Testing ensures reliability.' in prompt
    assert 'Keep the light burning.' in prompt


def test_compile_persona_renders_knowledge_graph():
    persona = Persona(
        name='Ariel',
        aleph='To manifest clarity in the infinite garden.',
        principles=[],
        protocols=[],
        speech_modulations=[],
    )
    user = UserProfile(name='Eran', role='Architect', domain_expertise=[], core_values=[])
    kg_data = {
        'directed': True,
        'multigraph': False,
        'graph': {},
        'nodes': [
            {
                'id': 'node-1',
                'type': 'Fact',
                'content': 'Knowledge graph is active.',
                'status': 'active',
                'confidence': 1.0,
                'pinned': True,
            }
        ],
        'links': [{'source': 'node-1', 'target': 'node-2', 'type': 'precedes', 'confidence': 1.0}],
    }
    state = SessionState(persona=persona, user=user, memories=[], epilogue=None, knowledge_graph=kg_data)
    prompt = compile_persona(state)

    assert 'COGNITIVE MAP' in prompt
    assert 'node-1' in prompt
    assert 'Fact' in prompt
    assert 'Knowledge graph is active.' in prompt
    assert 'node-1 --[precedes]--> node-2' in prompt
    assert 'EVOLUTION HISTORY' not in prompt


def test_compile_persona_uses_precompiled_singleton():
    """EP-0140: Verify that compile_persona uses the module singleton template AST."""
    from tur import compiler

    assert hasattr(compiler, '_PERSONA_TEMPLATE')
    assert hasattr(compiler, '_JINJA_ENV')

    persona = Persona(name='Ariel', aleph='Truth', principles=[], protocols=[], speech_modulations=[])
    user = UserProfile(name='Eran', role='Architect', domain_expertise=[], core_values=[])
    state = SessionState(persona=persona, user=user, memories=[], epilogue='End')

    # Execute 20 rapid renders to assert robustness and speed
    for _ in range(20):
        prompt = compiler.compile_persona(state)
        assert 'Ariel' in prompt
        assert 'Truth' in prompt


def test_estimate_tokens():
    """EP-0132: Verify token estimation heuristic."""
    from tur.compiler import estimate_tokens

    assert estimate_tokens('') == 0
    assert estimate_tokens('hello world') == 2
    assert estimate_tokens('function(x: int) -> str;') >= 6


def test_knapsack_01_exact_and_edge_cases():
    """EP-0132: Verify 0-1 Knapsack exact DP solver."""
    from tur.compiler import knapsack_01

    # Empty
    assert knapsack_01([], [], 10) == []
    # Capacity 0
    assert knapsack_01([5, 10], [1.0, 2.0], 0) == []
    # All items fit
    assert knapsack_01([2, 3], [10.0, 20.0], 10) == [0, 1]
    # Optimal choice: item 2 gives 30. items 0+1 give 25. Best is item 2.
    assert knapsack_01([2, 3, 5], [10.0, 15.0, 30.0], 5) == [2]
    # Item 0 (w=3, v=20), Item 1 (w=4, v=25), Item 2 (w=2, v=15), cap=5 -> items 0 and 2 (w=5, v=35)
    assert knapsack_01([3, 4, 2], [20.0, 25.0, 15.0], 5) == [0, 2]
    # Items with weight exceeding capacity are excluded
    assert knapsack_01([10, 20], [100.0, 200.0], 5) == []


def test_knapsack_01_large_capacity_heuristic():
    """EP-0132: Verify large capacity heuristic fallback."""
    from tur.compiler import knapsack_01

    n = 100
    weights = [50] * n
    values = [float(i) for i in range(n)]
    capacity = 30000  # 30000 * 100 = 3,000,000 > 2,000,000
    res = knapsack_01(weights, values, capacity)
    assert len(res) > 0
    assert sum(weights[i] for i in res) <= capacity


def test_compile_persona_budgeted_wake_knowledge_graph():
    """EP-0132: Verify Knapsack dynamic token budgeting packs HippoRAG subgraphs within budget."""
    persona = Persona(name='Ariel', aleph='Manifest clarity', principles=[], protocols=[], speech_modulations=[])
    user = UserProfile(name='Eran', role='Architect', domain_expertise=[], core_values=[])

    nodes = [
        {'id': 'node-mcp', 'type': 'Concept', 'content': 'FastMCP transport optimization.', 'confidence': 1.0},
        {'id': 'node-compiler', 'type': 'Concept', 'content': 'AST Jinja2 memoization.', 'confidence': 0.95},
        {'id': 'node-storage', 'type': 'Concept', 'content': 'Merkle tree directory digest.', 'confidence': 0.9},
        {'id': 'node-unrelated-1', 'type': 'Fact', 'content': 'Ancient history trivia node 1.', 'confidence': 0.4},
        {'id': 'node-unrelated-2', 'type': 'Fact', 'content': 'Ancient history trivia node 2.', 'confidence': 0.3},
        {'id': 'node-unrelated-3', 'type': 'Fact', 'content': 'Ancient history trivia node 3.', 'confidence': 0.25},
    ]
    links = [
        {'source': 'node-mcp', 'target': 'node-compiler', 'type': 'depends_on'},
        {'source': 'node-compiler', 'target': 'node-storage', 'type': 'refines'},
        {'source': 'node-unrelated-1', 'target': 'node-unrelated-2', 'type': 'links'},
    ]
    kg_data = {'nodes': nodes, 'links': links}
    state = SessionState(
        persona=persona,
        user=user,
        memories=[],
        epilogue='Focus on node-mcp and compiler performance.',
        knowledge_graph=kg_data,
    )

    # 1. Unbounded compilation: all 6 nodes present
    unbounded_prompt = compile_persona(state, token_budget=None)
    for n in nodes:
        assert n['id'] in unbounded_prompt
    assert 'Tur Context Manager' not in unbounded_prompt

    # 2. Constrained budget: enough for base prompt + top salient nodes, but not all
    from tur.compiler import estimate_tokens

    base_cost = estimate_tokens(
        compile_persona(SessionState(persona=persona, user=user, memories=[], epilogue=state.epilogue))
    )
    budget = base_cost + 45
    budgeted_prompt = compile_persona(state, token_budget=budget)

    # Most salient node (referenced in epilogue and central) MUST be present
    assert 'node-mcp' in budgeted_prompt
    # Unrelated trivia should be pruned
    assert 'node-unrelated-3' not in budgeted_prompt
    # Context manager advisory alert MUST be present
    assert 'Tur Context Manager' in budgeted_prompt
    assert 'omitted to preserve token budget' in budgeted_prompt


def test_compile_persona_budgeted_wake_flat_memories():
    """EP-0132: Verify Knapsack dynamic budgeting on flat memories list."""
    persona = Persona(name='Ariel', aleph='Clarity', principles=[], protocols=[], speech_modulations=[])
    user = UserProfile(name='Eran', role='Architect', domain_expertise=[], core_values=[])

    memories = [
        Memory(
            timestamp=datetime.now(),
            type=MemoryType.INSIGHT,
            scope=MemoryScope.INCARNATION,
            tags=['high-priority'],
            content='Crucial recent insight about architecture.',
            confidence=1.0,
        ),
        Memory(
            timestamp=datetime(2025, 1, 1, 0, 0, 0),
            type=MemoryType.FACT,
            scope=MemoryScope.UNIVERSAL,
            tags=['old'],
            content='Old low-confidence trivia fact from last year.',
            confidence=0.3,
        ),
    ]
    state = SessionState(persona=persona, user=user, memories=memories, epilogue=None)

    from tur.compiler import estimate_tokens

    base_cost = estimate_tokens(
        compile_persona(SessionState(persona=persona, user=user, memories=[], epilogue=None))
    )
    # Budget that fits base + 1 memory
    budget = base_cost + 35

    budgeted_prompt = compile_persona(state, token_budget=budget)
    assert 'Crucial recent insight' in budgeted_prompt
    assert 'Old low-confidence trivia' not in budgeted_prompt
    assert 'Tur Context Manager' in budgeted_prompt
    assert '1 lower-salience items omitted' in budgeted_prompt


def test_compile_persona_extreme_tight_budget():
    """EP-0132: Verify graceful handling when token budget is smaller than base prompt."""
    persona = Persona(name='Ariel', aleph='Clarity', principles=[], protocols=[], speech_modulations=[])
    user = UserProfile(name='Eran', role='Architect', domain_expertise=[], core_values=[])
    memories = [
        Memory(
            timestamp=datetime.now(),
            type=MemoryType.INSIGHT,
            scope=MemoryScope.INCARNATION,
            tags=[],
            content='Memory 1',
        )
    ]
    state = SessionState(persona=persona, user=user, memories=memories, epilogue=None)

    # Extreme budget of 5 tokens
    prompt = compile_persona(state, token_budget=5)
    assert 'Ariel' in prompt
    assert 'Memory 1' not in prompt
    assert 'Tur Context Manager' in prompt


def test_compile_persona_custom_tokenizer():
    """EP-0132: Verify custom tokenizer injection into compile_persona."""
    persona = Persona(name='Ariel', aleph='Clarity', principles=[], protocols=[], speech_modulations=[])
    user = UserProfile(name='Eran', role='Architect', domain_expertise=[], core_values=[])
    state = SessionState(persona=persona, user=user, memories=[], epilogue='End')

    custom_calls = []

    def my_tokenizer(text: str) -> int:
        custom_calls.append(len(text))
        return len(text) // 5

    prompt = compile_persona(state, token_budget=500, tokenizer=my_tokenizer)
    assert len(custom_calls) > 0
    assert 'Ariel' in prompt
