import pytest

from tur.vector_clock import VectorClock


def test_vector_clock_initialization():
    assert VectorClock(None) == {}
    assert VectorClock('') == {}
    assert VectorClock('invalid-json') == {}
    assert VectorClock({'agent_a': 1, 'agent_b': 2}) == {'agent_a': 1, 'agent_b': 2}
    assert VectorClock('{"agent_a": 3, "agent_b": 4}') == {'agent_a': 3, 'agent_b': 4}


def test_vector_clock_tick():
    clock = VectorClock({'agent_A': 1, 'agent_B': 2})
    ticked = clock.tick('agent_A')
    assert ticked == {'agent_A': 2, 'agent_B': 2}
    # Original is not mutated
    assert clock == {'agent_A': 1, 'agent_B': 2}

    # Ticking a new agent
    ticked_new = clock.tick('agent_C')
    assert ticked_new == {'agent_A': 1, 'agent_B': 2, 'agent_C': 1}


def test_vector_clock_lattice_merge():
    clock_a = VectorClock({'agent_A': 2, 'agent_B': 1})
    clock_b = VectorClock({'agent_A': 1, 'agent_B': 3, 'agent_C': 1})
    merged = clock_a | clock_b
    assert merged == {'agent_A': 2, 'agent_B': 3, 'agent_C': 1}
    assert isinstance(merged, VectorClock)


def test_causal_precedence_and_succession():
    # a < b: forall k: V_a[k] <= V_b[k] and exists m: V_a[m] < V_b[m]
    clock_a = VectorClock({'agent_A': 1, 'agent_B': 1})
    clock_b = VectorClock({'agent_A': 2, 'agent_B': 1})
    clock_c = VectorClock({'agent_A': 2, 'agent_B': 2})

    assert (clock_a < clock_b) is True
    assert (clock_b < clock_c) is True
    assert (clock_a < clock_c) is True  # Transitivity

    assert (clock_b > clock_a) is True
    assert (clock_c > clock_b) is True
    assert (clock_c > clock_a) is True

    # Reflexivity: a does not precede a
    assert (clock_a < clock_a) is False
    assert (clock_a <= clock_a) is True
    assert (clock_a >= clock_a) is True

    # Reverse: b does not precede a
    assert (clock_b < clock_a) is False


def test_concurrency_detection():
    # Concurrent events: independent branches
    clock_alpha = VectorClock({'agent_A': 2, 'agent_B': 1})
    clock_beta = VectorClock({'agent_A': 1, 'agent_B': 2})

    assert (clock_alpha < clock_beta) is False
    assert (clock_beta < clock_alpha) is False
    assert (clock_alpha > clock_beta) is False
    assert (clock_beta > clock_alpha) is False
    assert clock_alpha.is_concurrent_with(clock_beta) is True

    # Identical clocks are not concurrent
    assert clock_alpha.is_concurrent_with(clock_alpha) is False

    # Causally ordered clocks are not concurrent
    clock_gamma = VectorClock({'agent_A': 3, 'agent_B': 2})
    assert clock_alpha.is_concurrent_with(clock_gamma) is False


def test_is_causally_ready():
    agent_clock = VectorClock({'agent_A': 2, 'agent_B': 1})

    # Next expected message from agent_A: clock must have agent_A == 3 and agent_B <= 1
    ready_sig = VectorClock({'agent_A': 3, 'agent_B': 1})
    assert ready_sig.is_ready(agent_clock, sender_id='agent_A') is True

    # Out of order message from agent_A: agent_A == 4 (skipped 3)
    out_of_order = VectorClock({'agent_A': 4, 'agent_B': 1})
    assert out_of_order.is_ready(agent_clock, sender_id='agent_A') is False

    # Dependent on unreceived message from agent_C
    missing_dep = VectorClock({'agent_A': 3, 'agent_B': 1, 'agent_C': 1})
    assert missing_dep.is_ready(agent_clock, sender_id='agent_A') is False

    # Empty legacy clock is always ready
    assert VectorClock({}).is_ready(agent_clock, sender_id='agent_A') is True


def test_vector_clock_immutability_and_hash():
    v1 = VectorClock({'agent_A': 1, 'agent_B': 1})
    v2 = VectorClock({'agent_A': 2, 'agent_B': 1})

    assert hash(v1) == hash(VectorClock({'agent_A': 1, 'agent_B': 1}))
    clock_set = {v1, v2}
    assert v1 in clock_set
    assert VectorClock({'agent_A': 1, 'agent_B': 1}) in clock_set
    assert v1['unknown_agent'] == 0

    with pytest.raises(TypeError, match='does not support addition'):
        _ = v1 + v2

    assert v1.to_dict() == {'agent_A': 1, 'agent_B': 1}
    assert 'agent_A' in v1.to_json()


def test_vector_clock_sort():
    v1 = VectorClock({'agent_A': 1, 'agent_B': 0})
    v2 = VectorClock({'agent_A': 2, 'agent_B': 0})
    v3 = VectorClock({'agent_A': 2, 'agent_B': 1})

    # Sort raw VectorClock objects
    shuffled = [v3, v1, v2]
    sorted_clocks = VectorClock.sort(shuffled)
    assert sorted_clocks == [v1, v2, v3]

    # Sort with custom key extractor
    records = [{'id': 'c', 'clock': v3}, {'id': 'a', 'clock': v1}, {'id': 'b', 'clock': v2}]
    sorted_records = VectorClock.sort(records, key=lambda r: r['clock'])
    assert [r['id'] for r in sorted_records] == ['a', 'b', 'c']


def test_sort_signals_causally():
    from tur.session import sort_signals_causally

    sig1 = {'id': 's1', 'vector_clock': {'agent_A': 1, 'agent_B': 0}, 'sequence': 1}
    sig2 = {'id': 's2', 'vector_clock': {'agent_A': 2, 'agent_B': 0}, 'sequence': 2}
    sig3 = {'id': 's3', 'vector_clock': {'agent_A': 2, 'agent_B': 1}, 'sequence': 3}

    shuffled = [sig3, sig1, sig2]
    sorted_signals = sort_signals_causally(shuffled)
    assert [s['id'] for s in sorted_signals] == ['s1', 's2', 's3']
