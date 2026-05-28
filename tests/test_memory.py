import os
from datetime import datetime
from pathlib import Path

import pytest

from tur.memory import MemoryManager
from tur.models import Memory, MemoryScope, MemoryType


@pytest.fixture
def temp_home_and_base(tmp_path, monkeypatch):
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()

    # Mock Path.home() to return fake_home
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    local_base = tmp_path / "local_base"
    local_base.mkdir()

    return fake_home, local_base


def test_memory_manager_init_and_dirs(temp_home_and_base):
    fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)

    assert manager.local_dir == local_base / "memories"
    assert manager.local_archive_dir == local_base / "memories" / "archive"
    assert manager.global_dir == fake_home / ".tur" / "personas" / local_base.name / "memories"
    assert manager.global_archive_dir == manager.global_dir / "archive"

    assert manager.local_dir.exists()
    assert manager.local_archive_dir.exists()
    assert manager.global_dir.exists()
    assert manager.global_archive_dir.exists()


def test_memory_manager_save_and_load_local(temp_home_and_base):
    _fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)

    mem = Memory(
        timestamp=datetime(2026, 5, 29, 12, 0, 0),
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        tags=["pytest", "local"],
        content="This is a local incarnation memory."
    )

    saved_path = manager.save(mem)
    assert saved_path.exists()
    assert str(local_base) in str(saved_path)

    # Verify file is read-only (Golem's Seal)
    # On Windows, chmod 0o444 sets the read-only attribute.
    # We can check if it loaded successfully.
    loaded_memories = manager.load_all()
    assert len(loaded_memories) == 1
    assert loaded_memories[0].id == mem.id
    assert loaded_memories[0].content == mem.content
    assert loaded_memories[0].type == MemoryType.FACT
    assert loaded_memories[0].scope == MemoryScope.INCARNATION


def test_memory_manager_save_and_load_global(temp_home_and_base):
    fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)

    mem = Memory(
        timestamp=datetime(2026, 5, 29, 12, 0, 0),
        type=MemoryType.FACT,
        scope=MemoryScope.UNIVERSAL,
        tags=["pytest", "global"],
        content="This is a universal global memory."
    )

    saved_path = manager.save(mem)
    assert saved_path.exists()
    assert str(fake_home) in str(saved_path)

    loaded_memories = manager.load_all()
    assert len(loaded_memories) == 1
    assert loaded_memories[0].id == mem.id
    assert loaded_memories[0].scope == MemoryScope.UNIVERSAL


def test_memory_manager_archive_local(temp_home_and_base):
    _fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)

    mem = Memory(
        type=MemoryType.INSIGHT,
        scope=MemoryScope.INCARNATION,
        tags=["temp"],
        content="Forgettable content."
    )

    manager.save(mem)
    assert len(manager.load_all(include_archived=False)) == 1

    # Archive the memory
    manager.archive(mem.id)

    # Verify it is no longer in the active list
    assert len(manager.load_all(include_archived=False)) == 0

    # Verify it is returned when including archived
    archived_list = manager.load_all(include_archived=True)
    assert len(archived_list) == 1
    assert archived_list[0].id == mem.id


def test_memory_manager_archive_global(temp_home_and_base):
    _fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)

    mem = Memory(
        type=MemoryType.INSIGHT,
        scope=MemoryScope.UNIVERSAL,
        tags=["temp"],
        content="Forgettable global content."
    )

    manager.save(mem)
    assert len(manager.load_all(include_archived=False)) == 1

    manager.archive(mem.id)
    assert len(manager.load_all(include_archived=False)) == 0

    archived_list = manager.load_all(include_archived=True)
    assert len(archived_list) == 1
    assert archived_list[0].id == mem.id


def test_memory_manager_archive_not_found(temp_home_and_base):
    _fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)

    with pytest.raises(FileNotFoundError):
        manager.archive("nonexistent-id")


def test_memory_manager_query(temp_home_and_base):
    _fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)

    mem1 = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        tags=["tag-a", "tag-common"],
        content="First memory"
    )
    mem2 = Memory(
        type=MemoryType.AXIOM,
        scope=MemoryScope.INCARNATION,
        tags=["tag-b", "tag-common"],
        content="Second memory"
    )

    manager.save(mem1)
    manager.save(mem2)

    # Query with no tags (should return all up to limit)
    assert len(manager.query(limit=1)) == 1
    assert len(manager.query()) == 2

    # Query with specific tag
    filtered_a = manager.query(tags=["tag-a"])
    assert len(filtered_a) == 1
    assert filtered_a[0].content == "First memory"

    filtered_common = manager.query(tags=["tag-common"])
    assert len(filtered_common) == 2


def test_load_corrupted_file(temp_home_and_base):
    _fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)

    corrupt_file = manager.local_dir / "20260529_000000_insight_badhash.yaml"
    with open(corrupt_file, "w", encoding="utf-8") as f:
        f.write("corrupted: yaml: content: {")

    # Should handle error and return None in _load_file
    assert manager._load_file(corrupt_file) is None

    # load_all should skip the corrupted file gracefully
    assert len(manager.load_all()) == 0


def test_save_exception_cleanup(temp_home_and_base, monkeypatch):
    _fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)

    mem = Memory(
        type=MemoryType.FACT,
        scope=MemoryScope.INCARNATION,
        tags=["pytest"],
        content="Will fail."
    )

    # Mock os.replace to raise an exception
    def mock_replace(src, dst):
        raise RuntimeError("Atomic replace failed")
    monkeypatch.setattr(os, "replace", mock_replace)

    # Save should raise and cleanup temp file
    with pytest.raises(RuntimeError):
        manager.save(mem)

    # Check that no temporary files remain in target directory
    temp_files = list(manager.local_dir.glob("*.tmp.*"))
    assert len(temp_files) == 0


def test_load_legacy_with_status(temp_home_and_base):
    _fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)

    # Create a legacy yaml file containing a 'status' attribute
    legacy_content = (
        "id: legacy-id-123\n"
        "timestamp: 2026-05-29T12:00:00\n"
        "type: fact\n"
        "scope: incarnation\n"
        "tags: [legacy]\n"
        "content: This has status.\n"
        "status: active\n"
    )

    legacy_file = manager.local_dir / "20260529_120000_fact_legacy-id-123.yaml"
    with open(legacy_file, "w", encoding="utf-8") as f:
        f.write(legacy_content)

    mem = manager._load_file(legacy_file)
    assert mem is not None
    assert mem.id == "legacy-id-123"
    assert mem.content == "This has status."
    # status key should be successfully removed before validating
    assert not hasattr(mem, "status")


def test_load_all_skips_directories(temp_home_and_base):
    _fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)

    # Create a subdirectory inside local_dir ending in .yaml to trigger the loop but fail is_file()
    nested_dir = manager.local_dir / "not_a_file.yaml"
    nested_dir.mkdir()

    mems = manager.load_all()
    # It should skip the directory gracefully
    assert len(mems) == 0


def test_load_all_with_non_existent_directory(temp_home_and_base):
    _fake_home, local_base = temp_home_and_base
    manager = MemoryManager(base_dir=local_base)
    # Remove one of the directories to trigger directory.exists() == False
    if manager.global_archive_dir.exists():
        manager.global_archive_dir.rmdir()
    if manager.global_dir.exists():
        manager.global_dir.rmdir()

    mems = manager.load_all(include_archived=True)
    assert len(mems) == 0


