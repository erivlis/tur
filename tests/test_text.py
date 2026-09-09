"""
tests/test_text.py - Unit tests for tur.text canonical tokenization and regex substrate.
"""

import pytest

from tur.text import (
    get_entropy_pattern,
    is_safe_identifier,
    is_session_identifier,
    is_snake_identifier,
    tokenize_approx,
    tokenize_query,
    tokenize_words,
)


def test_tokenize_words():
    assert tokenize_words('') == []
    assert tokenize_words('hello world 123_foo') == ['hello', 'world', '123_foo']
    assert tokenize_words('special !@# characters... test') == ['special', 'characters', 'test']


def test_tokenize_approx():
    assert tokenize_approx('') == []
    tokens = tokenize_approx('hello, world! 123.')
    assert 'hello' in tokens
    assert ',' in tokens
    assert 'world' in tokens
    assert '!' in tokens
    assert '123' in tokens
    assert '.' in tokens


def test_tokenize_query():
    assert tokenize_query('') == []
    assert tokenize_query('   ') == []
    tokens = tokenize_query('Graph-Theoretic Semantic Retrieval & HippoRAG!')
    assert 'graph-theoretic' in tokens
    assert 'semantic' in tokens
    assert 'retrieval' in tokens
    assert 'hipporag' in tokens
    # Tokens shorter than min_length (2) should be excluded
    assert 'a' not in tokenize_query('a big test')


def test_is_safe_identifier():
    assert not is_safe_identifier('')
    assert is_safe_identifier('valid_name-123.foo')
    assert not is_safe_identifier('invalid/path')
    assert not is_safe_identifier('invalid name with spaces')
    assert not is_safe_identifier('invalid$char')


def test_is_session_identifier():
    assert not is_session_identifier('')
    assert is_session_identifier('20260825_190758_86152dcb')
    assert is_session_identifier('sess-123_abc')
    assert not is_session_identifier('sess.invalid.dot')
    assert not is_session_identifier('sess/invalid')


def test_is_snake_identifier():
    assert not is_snake_identifier('')
    assert is_snake_identifier('depends_on')
    assert is_snake_identifier('caused_by')
    assert is_snake_identifier('links')
    assert not is_snake_identifier('DependsOn')
    assert not is_snake_identifier('depends-on')
    assert not is_snake_identifier('depends on')


def test_get_entropy_pattern_caching():
    p20 = get_entropy_pattern(20)
    p20_again = get_entropy_pattern(20)
    assert p20 is p20_again

    p30 = get_entropy_pattern(30)
    assert p30 is not p20
    assert p20.pattern == r'[A-Za-z0-9_\-\+/=]{20,}'
    assert p30.pattern == r'[A-Za-z0-9_\-\+/=]{30,}'
