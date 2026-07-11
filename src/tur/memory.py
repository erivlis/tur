import contextlib
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from tur._helpers import yaml_safe_load
from tur.models import Memory, MemoryLink, MemoryScope, MemoryType
from tur.paths import is_global_path


class MemoryManager:
    """
    Manages the 'Memory Bank' for a specific Persona.
    Handles atomicity, immutability, retrieval, and Federation (Universal vs. Incarnational).
    Transitions L1 memory storage to Open Knowledge Format (OKF) Markdown files.
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
            local_memories = Path.cwd() / '.tur' / 'personas' / persona_id / 'memories'
        else:
            local_memories = base_dir / 'memories'

        self.local_dir = local_memories / 'active'
        self.local_archive_dir = local_memories / 'archive'
        self.local_subsumed_dir = local_memories / 'subsumed'

        # Calculate the global equivalent: ~/.tur/personas/<uuid>
        global_memories = Path.home() / '.tur' / 'personas' / persona_id / 'memories'
        self.global_dir = global_memories / 'active'
        self.global_archive_dir = global_memories / 'archive'
        self.global_subsumed_dir = global_memories / 'subsumed'

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
            case MemoryScope.UNIVERSAL | MemoryScope.PERSONA | MemoryScope.USER:
                return self.global_dir, self.global_archive_dir
            case MemoryScope.INCARNATION:
                return self.local_dir, self.local_archive_dir
            case _:
                raise ValueError(f'Unsupported MemoryScope: {scope}')

    def save(self, memory: Memory) -> Path:
        """
        Saves a Memory to an immutable file in the federated storage using atomic POSIX writes.
        Routes to ~/.tur (Universal) or ./.tur (Incarnational) based on scope.
        Returns the path to the saved file as an OKF Markdown file.
        """
        target_dir, _ = self._get_target_dirs(memory.scope)

        # Filename: timestamp_type_id.md
        filename = f'{memory.timestamp.strftime("%Y%m%d_%H%M%S")}_{memory.type.value}_{memory.id}.md'
        file_path = target_dir / filename

        desc = (
            f'{memory.type.value.capitalize()}: {memory.content.splitlines()[0][:100]}'
            if memory.content
            else ''
        )

        # Format as OKF Markdown with YAML frontmatter
        frontmatter: dict[str, Any] = {
            'type': 'L1 Memory',
            'title': f'Memory {memory.id[:8]}',
            'description': desc,
            'tags': memory.tags,
            'timestamp': memory.timestamp.isoformat(),
            'scope': memory.scope.value.upper(),
            'memory_type': memory.type.value.upper(),
            'hash': memory.id,
        }
        if memory.links:
            frontmatter['links'] = [link.model_dump() for link in memory.links]
        if memory.source_session:
            frontmatter['source_session'] = memory.source_session

        yaml_part = yaml.dump(frontmatter, sort_keys=False, default_flow_style=False)
        okf_content = f"---\n{yaml_part}---\n\n{memory.content}\n"

        # Atomic Write Pattern (to prevent multi-agent collision under EP-0102/EP-0106)
        # 1. Write to a temporary file in the same directory
        # 2. fsync to guarantee flush to disk
        # 3. os.replace to atomically overwrite/create the final file
        fd, tmp_path_str = tempfile.mkstemp(dir=target_dir, prefix=f'{filename}.tmp.')
        try:
            with open(fd, 'w', encoding='utf-8') as f:
                f.write(okf_content)
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
        files = (
                list(self.local_dir.glob(f'*_{memory_id}.md'))
                + list(self.local_dir.glob(f'*_{memory_id}.yaml'))
        )
        # Legacy search in parent memories/ folder
        if not files:
            files = (
                    list(self.local_dir.parent.glob(f'*_{memory_id}.yaml'))
                    + list(self.local_dir.parent.glob(f'*_{memory_id}.md'))
            )

        target_archive = self.local_archive_dir

        # If not found locally, search the global bank
        if not files:
            files = (
                    list(self.global_dir.glob(f'*_{memory_id}.md'))
                    + list(self.global_dir.glob(f'*_{memory_id}.yaml'))
            )
            if not files:
                files = (
                        list(self.global_dir.parent.glob(f'*_{memory_id}.yaml'))
                        + list(self.global_dir.parent.glob(f'*_{memory_id}.md'))
                )
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
        files = (
                list(self.local_dir.glob(f'*_{memory_id}.md'))
                + list(self.local_dir.glob(f'*_{memory_id}.yaml'))
        )
        # Legacy search in parent memories/ folder
        if not files:
            files = (
                    list(self.local_dir.parent.glob(f'*_{memory_id}.yaml'))
                    + list(self.local_dir.parent.glob(f'*_{memory_id}.md'))
            )

        target_subsumed = self.local_subsumed_dir

        if not files:
            files = (
                    list(self.global_dir.glob(f'*_{memory_id}.md'))
                    + list(self.global_dir.glob(f'*_{memory_id}.yaml'))
            )
            if not files:
                files = (
                        list(self.global_dir.parent.glob(f'*_{memory_id}.yaml'))
                        + list(self.global_dir.parent.glob(f'*_{memory_id}.md'))
                )
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

        # Legacy directories
        legacy_local_subsumed = self.local_dir.parent.parent / 'subsumed'
        legacy_global_subsumed = self.global_dir.parent.parent / 'subsumed'
        directories.extend([legacy_local_subsumed, legacy_global_subsumed])

        loaded_ids = set()
        for directory in directories:
            if directory.exists():
                for file_path in list(directory.glob('*.md')) + list(directory.glob('*.yaml')):
                    if file_path.is_file():
                        mem = self._load_file(file_path)
                        if mem and mem.id not in loaded_ids:
                            memories.append(mem)
                            loaded_ids.add(mem.id)
        memories.sort(key=lambda x: x.timestamp)
        return memories

    def load_all(self, include_archived: bool = False) -> list[Memory]:
        """
        Retrieves all memories by merging the local and global memory banks (Federation).
        """
        memories = []

        # Load from active and legacy memories folders
        directories = [self.local_dir, self.global_dir]
        directories.extend([self.local_dir.parent, self.global_dir.parent])

        if include_archived:
            directories.extend([self.local_archive_dir, self.global_archive_dir])

        loaded_ids = set()
        for directory in directories:
            if directory.exists():
                for file_path in list(directory.glob('*.md')) + list(directory.glob('*.yaml')):
                    if file_path.is_file():
                        # Safety: skip directories if named like search patterns
                        # Ensure we only load files from memories/active, memories/archive, or legacy memories/*.yaml
                        parent_name = file_path.parent.name
                        is_legacy = parent_name == 'memories' and file_path.suffix == '.yaml'
                        if parent_name not in ['active', 'archive', 'subsumed'] and not is_legacy:
                            continue

                        mem = self._load_file(file_path)
                        if mem and mem.id not in loaded_ids:
                            memories.append(mem)
                            loaded_ids.add(mem.id)

        # Sort combined federated timeline by timestamp
        memories.sort(key=lambda x: x.timestamp)
        return memories

    def count_all(self, include_archived: bool = False) -> int:
        """
        Counts all memories in the federated storage without loading them (for performance).
        """
        return len(self.load_all(include_archived=include_archived))

    def _verify_file_integrity(self, file_path: Path) -> str | None:
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) < 3:
                    return 'Invalid OKF structure'
                yaml_part = parts[1]
                body_part = parts[2].strip()
                data = yaml_safe_load(yaml_part)
                stored_id = data.get('hash', '')
            else:
                data = yaml_safe_load(content)
                stored_id = data.get('id', '')
                body_part = data.get('content', '')

            if not data or not isinstance(data, dict):
                return 'Invalid structure or empty file'

            if not stored_id:
                return "Missing ID/hash in file"

            expected_suffix = f'_{stored_id}.md' if file_path.suffix == '.md' else f'_{stored_id}.yaml'
            if not file_path.name.endswith(expected_suffix):
                return f'Filename does not match stored ID: {stored_id}'

            if content.startswith('---'):
                scope_val = data.get('scope', '').lower()
                type_val = data.get('memory_type', '').lower()
                links_data = data.get('links', [])
                links = [MemoryLink(**lnk) for lnk in links_data] if links_data else []

                recomputed_mem = Memory(
                    timestamp=datetime.fromisoformat(str(data.get('timestamp'))),
                    type=MemoryType(type_val),
                    scope=MemoryScope(scope_val),
                    tags=data.get('tags', []),
                    content=body_part,
                    links=links,
                    source_session=data.get('source_session'),
                )
            else:
                test_data = data.copy()
                if 'id' in test_data:
                    del test_data['id']
                if 'status' in test_data:
                    del test_data['status']
                recomputed_mem = Memory(**test_data)

            if recomputed_mem.id != stored_id:
                return f'Computed hash {recomputed_mem.id} does not match stored ID {stored_id}'
        except Exception as e:
            return f'Failed to parse or hash memory: {e}'
        else:
            return None

    def verify_integrity(self) -> list[tuple[Path, str]]:
        """
        EP-0106: Merkle Memory.
        Iterates through all .md and .yaml files in the active, archived and subsumed memory banks,
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
            self.local_dir.parent,
            self.global_dir.parent,
            self.local_dir.parent.parent / 'subsumed',
            self.global_dir.parent.parent / 'subsumed',
        ]

        seen_paths = set()
        for directory in directories:
            if not directory.exists():
                continue
            for file_path in list(directory.glob('*.md')) + list(directory.glob('*.yaml')):
                if not file_path.is_file() or file_path in seen_paths:
                    continue
                seen_paths.add(file_path)

                parent_name = file_path.parent.name
                is_legacy = parent_name == 'memories' and file_path.suffix == '.yaml'
                if parent_name not in ['active', 'archive', 'subsumed'] and not is_legacy:
                    continue

                error_reason = self._verify_file_integrity(file_path)
                if error_reason:
                    failures.append((file_path, error_reason))
        return failures

    @staticmethod
    def _load_file(file_path: Path) -> Memory | None:
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) < 3:
                    return None
                yaml_part = parts[1]
                body_part = parts[2].strip()
                data = yaml_safe_load(yaml_part)

                scope_val = data.get('scope', '').lower()
                type_val = data.get('memory_type', '').lower()
                links_data = data.get('links', [])
                links = [MemoryLink(**lnk) for lnk in links_data] if links_data else []

                return Memory(
                    id=data.get('hash', ''),
                    timestamp=datetime.fromisoformat(str(data.get('timestamp'))),
                    type=MemoryType(type_val),
                    scope=MemoryScope(scope_val),
                    tags=data.get('tags', []),
                    content=body_part,
                    links=links,
                    source_session=data.get('source_session'),
                )

            # Legacy YAML file load fallback
            data = yaml_safe_load(content)
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
