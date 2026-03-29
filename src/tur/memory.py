import contextlib
import os
from pathlib import Path

import yaml

from tur.models import Memory


class MemoryManager:
    """
    Manages the 'Memory Bank' for a specific Persona.
    Handles atomicity, immutability, and retrieval.
    """

    def __init__(self, base_dir: Path = Path(".tur")):
        # base_dir is now expected to be the specific persona directory
        # e.g., Path(".tur/personas/f47ac10b-58cc-4372-a567-0e02b2c3d479")
        self.memory_dir = base_dir / "memories"
        self.archive_dir = self.memory_dir / "archive"
        self._ensure_dir()

    def _ensure_dir(self):
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def save(self, memory: Memory) -> Path:
        """
        Saves a Memory to an immutable file.
        Returns the path to the saved file.
        """
        # Filename: timestamp_type_id.yaml
        filename = f"{memory.timestamp.strftime('%Y%m%d_%H%M%S')}_{memory.type.value}_{memory.id}.yaml"
        file_path = self.memory_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            # We dump the raw model to ensure full fidelity
            # Pydantic's json-serializable dict is safe for YAML
            yaml.dump(memory.model_dump(mode='json'), f, sort_keys=False)

        # Lock the file (The Golem's Seal)
        with contextlib.suppress(Exception):
            os.chmod(file_path, 0o444)  # Read-only

        return file_path

    def archive(self, memory_id: str):
        """
        'Forgets' a memory by moving it to the archive directory.
        """
        # Search for the file with the matching UUID
        files = list(self.memory_dir.glob(f"*_{memory_id}.yaml"))
        if not files:
            raise FileNotFoundError(f"No memory found with ID: {memory_id}")

        source_path = files[0]
        target_path = self.archive_dir / source_path.name

        # Move the file
        # We might need to change permissions to move it on some systems,
        # but usually rename/move works if the directory is writable.
        os.rename(source_path, target_path)

    def load_all(self, include_archived: bool = False) -> list[Memory]:
        """
        Retrieves all memories from the bank.
        """
        memories = []

        if self.memory_dir.exists():
            for file_path in self.memory_dir.glob("*.yaml"):
                if file_path.is_file():
                    memories.append(self._load_file(file_path))

        if include_archived and self.archive_dir.exists():
            for file_path in self.archive_dir.glob("*.yaml"):
                if file_path.is_file():
                    mem = self._load_file(file_path)
                    if mem:
                        mem.status = "archived"  # Ensure status reflects location
                        memories.append(mem)

        # Sort by timestamp
        memories = [m for m in memories if m is not None]
        memories.sort(key=lambda x: x.timestamp)
        return memories

    def _load_file(self, file_path: Path) -> Memory | None:
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return Memory(**data)
        except Exception:
            return None

    def query(self, tags: list[str] | None = None, limit: int = 100) -> list[Memory]:
        """
        Simple in-memory filter.
        """
        all_memories = self.load_all()
        if not tags:
            return all_memories[-limit:]  # Return most recent if no filter

        filtered = [
            m for m in all_memories
            if any(tag in m.tags for tag in tags)
        ]
        return filtered[-limit:]
