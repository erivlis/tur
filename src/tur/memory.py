import contextlib
import os
import tempfile
from pathlib import Path

import yaml

from tur.models import Memory, MemoryScope
from tur.paths import is_global_path


class MemoryManager:
    """
    Manages the 'Memory Bank' for a specific Persona.
    Handles atomicity, immutability, retrieval, and Federation (Universal vs. Incarnational).
    """

    def __init__(self, base_dir: Path):
        """
        Initializes the federated memory system.

        Args:
            base_dir: The persona directory to anchor memory storage to.  May be either
                      the global identity directory (~/.tur/personas/<uuid>) or a local
                      project directory (.tur/personas/<uuid>).  The manager self-corrects:
                      universal/persona-scoped memories always go to the global store;
                      incarnation-scoped memories always go to the local store.
        """
        persona_id = base_dir.name

        if is_global_path(base_dir):
            self.local_dir = Path.cwd() / '.tur' / 'personas' / persona_id / 'memories'
        else:
            self.local_dir = base_dir / 'memories'
        self.local_archive_dir = self.local_dir / 'archive'
        self.local_subsumed_dir = self.local_dir.parent / 'subsumed'

        # Calculate the global equivalent: ~/.tur/personas/<uuid>
        self.global_dir = Path.home() / '.tur' / 'personas' / persona_id / 'memories'
        self.global_archive_dir = self.global_dir / 'archive'
        self.global_subsumed_dir = self.global_dir.parent / 'subsumed'

        self._ensure_dirs()

    def _ensure_dirs(self):
        """Creates the necessary directory structures for both local and global memory banks."""
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self.local_archive_dir.mkdir(parents=True, exist_ok=True)
        self.local_subsumed_dir.mkdir(parents=True, exist_ok=True)
        self.global_dir.mkdir(parents=True, exist_ok=True)
        self.global_archive_dir.mkdir(parents=True, exist_ok=True)
        self.global_subsumed_dir.mkdir(parents=True, exist_ok=True)

    def _get_target_dirs(self, scope: MemoryScope) -> tuple[Path, Path]:
        """
        Determines the correct filesystem path based on the MemoryScope (Federation).
        """
        match scope:
            case MemoryScope.UNIVERSAL | MemoryScope.PERSONA:
                return self.global_dir, self.global_archive_dir
            case MemoryScope.INCARNATION | MemoryScope.USER:
                return self.local_dir, self.local_archive_dir
            case _:
                raise ValueError(f'Unsupported MemoryScope: {scope}')

    def save(self, memory: Memory) -> Path:
        """
        Saves a Memory to an immutable file in the federated storage using atomic POSIX writes.
        Routes to ~/.tur (Universal) or ./.tur (Incarnational) based on scope.
        Returns the path to the saved file.
        """
        target_dir, _ = self._get_target_dirs(memory.scope)

        # Filename: timestamp_type_id.yaml
        filename = f'{memory.timestamp.strftime("%Y%m%d_%H%M%S")}_{memory.type.value}_{memory.id}.yaml'
        file_path = target_dir / filename

        # We dump the raw model to ensure full fidelity
        yaml_content = yaml.dump(memory.model_dump(mode='json'), sort_keys=False)

        # Atomic Write Pattern (to prevent multi-agent collision under EP-0102/EP-0106)
        # 1. Write to a temporary file in the same directory
        # 2. fsync to guarantee flush to disk
        # 3. os.replace to atomically overwrite/create the final file
        fd, tmp_path_str = tempfile.mkstemp(dir=target_dir, prefix=f'{filename}.tmp.')
        try:
            with open(fd, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
                f.flush()
                os.fsync(f.fileno())  # Guarantee disk flush

            # Atomic replace (POSIX)
            os.replace(tmp_path_str, file_path)
        except Exception:
            # Clean up the temp file if the atomic rename fails
            with contextlib.suppress(OSError):
                os.remove(tmp_path_str)
            raise

        # Lock the file (The Golem's Seal)
        with contextlib.suppress(Exception):
            os.chmod(file_path, 0o444)  # Read-only

        return file_path

    def archive(self, memory_id: str):
        """
        'Forgets' a memory by atomically moving it to the archive directory.
        Searches both the local and global federated banks.
        """
        # Search for the file in the local bank first
        files = list(self.local_dir.glob(f'*_{memory_id}.yaml'))
        target_archive = self.local_archive_dir

        # If not found locally, search the global bank
        if not files:
            files = list(self.global_dir.glob(f'*_{memory_id}.yaml'))
            target_archive = self.global_archive_dir

        if not files:
            raise FileNotFoundError(f'No memory found across federated banks with ID: {memory_id}')

        source_path = files[0]
        target_path = target_archive / source_path.name

        # os.replace is atomic across the same filesystem
        os.replace(source_path, target_path)

    def subsume(self, memory_id: str):
        """
        Moves a memory to the subsumed directory (compacted but still recoverable).
        Searches both the local and global federated banks.
        """
        files = list(self.local_dir.glob(f'*_{memory_id}.yaml'))
        target_subsumed = self.local_subsumed_dir

        if not files:
            files = list(self.global_dir.glob(f'*_{memory_id}.yaml'))
            target_subsumed = self.global_subsumed_dir

        if not files:
            raise FileNotFoundError(f'No memory found across federated banks with ID: {memory_id}')

        source_path = files[0]
        target_path = target_subsumed / source_path.name
        os.replace(source_path, target_path)

    def load_subsumed(self) -> list[Memory]:
        """
        Loads all subsumed memories from both local and global subsumed directories.
        """
        memories = []
        directories = [self.local_subsumed_dir, self.global_subsumed_dir]
        for directory in directories:
            if directory.exists():
                for file_path in directory.glob('*.yaml'):
                    if file_path.is_file():
                        mem = self._load_file(file_path)
                        if mem:
                            memories.append(mem)
        memories.sort(key=lambda x: x.timestamp)
        return memories

    def load_all(self, include_archived: bool = False) -> list[Memory]:
        """
        Retrieves all memories by merging the local and global memory banks (Federation).
        """
        memories = []

        # Load from both tiers
        directories = [self.local_dir, self.global_dir]
        if include_archived:
            directories.extend([self.local_archive_dir, self.global_archive_dir])

        for directory in directories:
            if directory.exists():
                for file_path in directory.glob('*.yaml'):
                    if file_path.is_file():
                        mem = self._load_file(file_path)
                        if mem:
                            # Note (EP-0106): The `status` field was removed from the Memory model.
                            # Status is now implicitly defined by which directory this file was found in.
                            memories.append(mem)

        # Sort combined federated timeline by timestamp
        memories.sort(key=lambda x: x.timestamp)
        return memories

    def verify_integrity(self) -> list[tuple[Path, str]]:
        """
        EP-0106: Merkle Memory.
        Iterates through all .yaml files in the active, archived and subsumed memory banks,
        recomputes the SHA-256 hashes of their contents, and asserts they match their filenames.
        Returns a list of tuples containing (file_path, error_reason) for any failures.
        """
        failures = []
        directories = [
            self.local_dir,
            self.global_dir,
            self.local_archive_dir,
            self.global_archive_dir,
            self.local_subsumed_dir,
            self.global_subsumed_dir,
        ]
        for directory in directories:
            if not directory.exists():
                continue
            for file_path in directory.glob('*.yaml'):
                if not file_path.is_file():
                    continue
                try:
                    with open(file_path, encoding='utf-8') as f:
                        data = yaml.safe_load(f)

                    if not data or not isinstance(data, dict):
                        failures.append((file_path, 'Invalid YAML structure or empty file'))
                        continue

                    stored_id = data.get('id', '')
                    if not stored_id:
                        failures.append((file_path, "Missing 'id' field in YAML"))
                        continue

                    expected_suffix = f'_{stored_id}.yaml'
                    if not file_path.name.endswith(expected_suffix):
                        failures.append((file_path, f'Filename does not match stored ID: {stored_id}'))
                        continue

                    test_data = data.copy()
                    if 'id' in test_data:
                        del test_data['id']
                    if 'status' in test_data:
                        del test_data['status']

                    recomputed_mem = Memory(**test_data)
                    if recomputed_mem.id != stored_id:
                        failures.append((file_path, f'Computed hash {recomputed_mem.id} does not match stored ID {stored_id}'))
                except Exception as e:
                    failures.append((file_path, f'Failed to parse or hash memory: {e}'))
        return failures

    @staticmethod
    def _load_file(file_path: Path) -> Memory | None:
        try:
            with open(file_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)
                # If the legacy file has 'status', ignore it so Pydantic doesn't throw a ValidationError
                if 'status' in data:
                    del data['status']
                return Memory(**data)
        except Exception:
            return None

    def query(self, tags: list[str] | None = None, limit: int = 100) -> list[Memory]:
        """
        Simple in-memory filter across the merged federated banks.
        """
        all_memories = self.load_all()
        if not tags:
            return all_memories[-limit:]

        filtered = [m for m in all_memories if any(tag in m.tags for tag in tags)]
        return filtered[-limit:]
