import contextlib
import hashlib
import os
import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

import yaml

from tur._helpers import yaml_safe_load
from tur.models import Memory, MemoryLink, MemoryScope, MemoryType
from tur.paths import get_global_tur_dir, is_global_path, resolve_workspace_dir


class MemoryManager:
    """
    Manages the 'Memory Bank' for a specific Persona.
    Handles atomicity, immutability, retrieval, and Federation (Universal vs. Incarnational).
    Transitions L1 memory storage to Open Knowledge Format (OKF) Markdown files.
    """

    _CACHE: ClassVar[dict[tuple[str, bool], tuple[str, list[Memory]]]] = {}

    def __init__(self, base_dir: Path, local_base_dir: Path | None = None):
        """
        Initializes the federated memory system.

        Args:
            base_dir: The persona directory to anchor memory storage to. May be either
                      the global identity directory (~/.tur/personas/<uuid>) or a local
                      project directory (.tur/personas/<uuid>).
            local_base_dir: Optional explicit project-local base directory. If omitted,
                            resolves via resolve_workspace_dir().
        """
        self.persona_id = base_dir.name
        persona_id = self.persona_id

        if local_base_dir is not None:
            local_memories = local_base_dir / 'memories' if local_base_dir.name != 'memories' else local_base_dir
        elif is_global_path(base_dir):
            ws = resolve_workspace_dir()
            local_memories = ws / '.tur' / 'personas' / persona_id / 'memories' if ws is not None else None
        else:
            local_memories = base_dir / 'memories'

        if local_memories is not None:
            self.local_dir: Path | None = local_memories / 'active'
            self.local_archive_dir: Path | None = local_memories / 'archive'
            self.local_subsumed_dir: Path | None = local_memories / 'subsumed'
        else:
            self.local_dir = None
            self.local_archive_dir = None
            self.local_subsumed_dir = None

        # Calculate the global equivalent: ~/.tur/personas/<uuid> (or TUR_HOME)
        global_memories = get_global_tur_dir() / 'personas' / persona_id / 'memories'
        self.global_dir = global_memories / 'active'
        self.global_archive_dir = global_memories / 'archive'
        self.global_subsumed_dir = global_memories / 'subsumed'

        self._ensure_dirs()

    def _ensure_dirs(self):
        """Creates directory structures for global memory banks (local is created if local_dir is explicit)."""
        self.global_dir.mkdir(parents=True, exist_ok=True)
        self.global_archive_dir.mkdir(parents=True, exist_ok=True)
        self.global_subsumed_dir.mkdir(parents=True, exist_ok=True)
        if self.local_dir is not None and not is_global_path(self.local_dir):
            self.local_dir.mkdir(parents=True, exist_ok=True)
            if self.local_archive_dir is not None:
                self.local_archive_dir.mkdir(parents=True, exist_ok=True)
            if self.local_subsumed_dir is not None:
                self.local_subsumed_dir.mkdir(parents=True, exist_ok=True)

    def _get_target_dirs(self, scope: MemoryScope) -> tuple[Path, Path]:
        """
        Determines the correct filesystem path based on the MemoryScope (Federation).
        Creates local directories strictly on-demand when saving an incarnation memory.
        """
        match scope:
            case MemoryScope.UNIVERSAL | MemoryScope.PERSONA | MemoryScope.USER:
                self.global_dir.mkdir(parents=True, exist_ok=True)
                self.global_archive_dir.mkdir(parents=True, exist_ok=True)
                return self.global_dir, self.global_archive_dir
            case MemoryScope.INCARNATION:
                if self.local_dir is None or self.local_archive_dir is None:
                    ws = resolve_workspace_dir() or Path.cwd()
                    local_memories = ws / '.tur' / 'personas' / self.persona_id / 'memories'
                    self.local_dir = local_memories / 'active'
                    self.local_archive_dir = local_memories / 'archive'
                    self.local_subsumed_dir = local_memories / 'subsumed'
                assert self.local_dir is not None
                assert self.local_archive_dir is not None
                self.local_dir.mkdir(parents=True, exist_ok=True)
                self.local_archive_dir.mkdir(parents=True, exist_ok=True)
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

        desc = f'{memory.type.value.capitalize()}: {memory.content.splitlines()[0][:100]}' if memory.content else ''

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

        # Core Memory fields
        if memory.core_type:
            frontmatter['core_type'] = memory.core_type
        if memory.derived_principle:
            frontmatter['derived_principle'] = memory.derived_principle
        if memory.ethical_covenant:
            frontmatter['ethical_covenant'] = memory.ethical_covenant
        if memory.status:
            frontmatter['status'] = memory.status

        # Merkle Tombstone & Redaction fields (EP-0143)
        if memory.redacted:
            frontmatter['redacted'] = True
            if memory.redacted_at:
                frontmatter['redacted_at'] = (
                    memory.redacted_at.isoformat()
                    if isinstance(memory.redacted_at, datetime)
                    else str(memory.redacted_at)
                )
            if memory.redaction_reason:
                frontmatter['redaction_reason'] = memory.redaction_reason

        yaml_part = yaml.dump(frontmatter, sort_keys=False, default_flow_style=False)
        okf_content = f'---\n{yaml_part}---\n\n{memory.content}\n'

        # Atomic Write Pattern (to prevent multi-agent collisions)
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
            if file_path.exists():
                with contextlib.suppress(Exception):
                    os.chmod(file_path, 0o666)
            os.replace(tmp_path_str, file_path)
        except Exception:
            # Clean up the temp file if the atomic rename fails
            with contextlib.suppress(OSError):
                os.remove(tmp_path_str)
            raise

        # Lock the file (The Golem's Seal)
        with contextlib.suppress(Exception):
            os.chmod(file_path, 0o444)  # Read-only

        self._invalidate_cache()
        return file_path

    def _find_memory_file(self, memory_id: str) -> Path:
        """Finds a memory file by ID across local and global memory stores."""
        search_dirs: list[Path] = []
        if self.local_dir is not None and self.local_dir.exists():
            search_dirs.extend([self.local_dir, self.local_dir.parent])
        search_dirs.extend([self.global_dir, self.global_dir.parent])

        for directory in search_dirs:
            if directory.exists():
                for pattern in (f'*_{memory_id}.md', f'*_{memory_id}.yaml'):
                    matches = list(directory.glob(pattern))
                    if matches:
                        return matches[0]

        raise FileNotFoundError(f'No memory found across federated banks with ID: {memory_id}')

    def _move_memory(self, memory_id: str, local_dest: Path | None, global_dest: Path) -> None:
        """Atomically moves a memory file to its target destination directory (archive or subsumed)."""
        source_path = self._find_memory_file(memory_id)
        is_local = self.local_dir is not None and (
            source_path.parent == self.local_dir or source_path.parent == self.local_dir.parent
        )
        target_dir = local_dest if is_local and local_dest is not None else global_dest
        target_dir.mkdir(parents=True, exist_ok=True)
        os.replace(source_path, target_dir / source_path.name)
        self._invalidate_cache()

    def archive(self, memory_id: str) -> None:
        """'Forgets' a memory by atomically moving it to the archive directory.

        Searches both the local and global federated banks.
        """
        self._move_memory(memory_id, self.local_archive_dir, self.global_archive_dir)

    def subsume(self, memory_id: str) -> None:
        """Moves a memory to the subsumed directory (compacted but still recoverable).

        Searches both the local and global federated banks.
        """
        self._move_memory(memory_id, self.local_subsumed_dir, self.global_subsumed_dir)

    def approve_core_memory(self, memory_id: str) -> tuple[Memory, bool]:
        """Approve and activate a pending Core memory matching ID prefix.

        Returns (matching_memory, was_already_active).
        Raises FileNotFoundError if no matching Core memory exists.
        """
        all_mems = self.load_all()
        matching_mem = next(
            (m for m in all_mems if m.id.startswith(memory_id) and m.type == MemoryType.CORE),
            None,
        )
        if not matching_mem:
            raise FileNotFoundError(f"No Core memory found matching ID '{memory_id}'")

        if getattr(matching_mem, 'status', None) == 'active':
            return matching_mem, True

        matching_mem.status = 'active'
        self.save(matching_mem)
        return matching_mem, False

    def redact(self, memory_id: str, reason: str) -> Path:
        """
        Merkle Tombstone Redaction (EP-0143).
        Replaces the body of a memory with a tombstone marker while preserving
        frontmatter hash and original file path to prevent breaking inbound L2 graph links.
        """
        file_path = self._find_memory_file(memory_id)
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        if not content.startswith('---'):
            raise ValueError(f"Memory file '{file_path.name}' is not in OKF format and cannot be tombstoned.")

        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid OKF structure in '{file_path.name}'.")

        yaml_part = parts[1]
        data: dict[str, Any] = yaml_safe_load(yaml_part) or {}

        now_iso = datetime.now().astimezone().isoformat()
        data['redacted'] = True
        data['redacted_at'] = now_iso
        data['redaction_reason'] = reason
        data['description'] = f'[REDACTED: {reason}]'

        tombstone_body = f'[TOMBSTONE: REDACTED DUE TO SECURITY POLICY - {reason}]'

        yaml_out = yaml.dump(data, sort_keys=False, default_flow_style=False)
        new_content = f'---\n{yaml_out}---\n\n{tombstone_body}\n'

        with contextlib.suppress(Exception):
            os.chmod(file_path, 0o666)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            f.flush()
            os.fsync(f.fileno())

        with contextlib.suppress(Exception):
            os.chmod(file_path, 0o444)

        self._invalidate_cache()
        return file_path

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory directory digest cache across all personas."""
        cls._CACHE.clear()

    def _invalidate_cache(self) -> None:
        """Invalidates the in-memory cache for this persona."""
        self._CACHE.pop((self.persona_id, False), None)
        self._CACHE.pop((self.persona_id, True), None)

    def _get_load_directories(self, include_archived: bool = False) -> list[Path | None]:
        """Returns the list of directories to search when loading memories."""
        dirs: list[Path | None] = [self.global_dir, self.global_dir.parent]
        if include_archived:
            dirs.append(self.global_archive_dir)

        if self.local_dir is not None and self.local_dir.exists():
            dirs.append(self.local_dir)
            if self.local_dir.parent.exists():
                dirs.append(self.local_dir.parent)
            if include_archived and self.local_archive_dir is not None and self.local_archive_dir.exists():
                dirs.append(self.local_archive_dir)
        return dirs

    @staticmethod
    def _iter_memory_files(directories: list[Path | None]) -> Iterator[Path]:
        """Yields unique, valid memory files across the provided directory list."""
        seen: set[Path] = set()
        for directory in directories:
            if directory is None or not directory.exists():
                continue
            for file_path in list(directory.glob('*.md')) + list(directory.glob('*.yaml')):
                if not file_path.is_file() or file_path in seen:
                    continue
                seen.add(file_path)

                parent_name = file_path.parent.name
                is_legacy = parent_name == 'memories' and file_path.suffix == '.yaml'
                if parent_name not in ('active', 'archive', 'subsumed') and not is_legacy:
                    continue

                yield file_path

    def _compute_directory_digest(self, include_archived: bool = False) -> str:
        """Fast state digest computed in < 1ms using high-resolution mtime and file size.

        Follows the mathematical model in EP-0140:
        H_digest = SHA256( (name_f || mtime_f || size_f) for f in Memories )
        """
        stat_digests: list[str] = []
        for file_path in self._iter_memory_files(self._get_load_directories(include_archived)):
            try:
                st = file_path.stat()
                stat_digests.append(f'{file_path.name}:{st.st_mtime_ns}:{st.st_size}')
            except OSError:
                pass

        raw = '|'.join(sorted(stat_digests))
        return hashlib.sha256(raw.encode()).hexdigest()

    def load_subsumed(self) -> list[Memory]:
        """Loads all subsumed memories from both local and global subsumed directories."""
        directories: list[Path | None] = [
            self.global_subsumed_dir,
            self.global_dir.parent.parent / 'subsumed',
        ]
        if self.local_subsumed_dir is not None:
            directories.append(self.local_subsumed_dir)
        if self.local_dir is not None:
            directories.append(self.local_dir.parent.parent / 'subsumed')

        memories = []
        loaded_ids: set[str] = set()
        for file_path in self._iter_memory_files(directories):
            mem = self._load_file(file_path)
            if mem and mem.id not in loaded_ids:
                memories.append(mem)
                loaded_ids.add(mem.id)
        memories.sort(key=lambda x: x.timestamp)
        return memories

    def _load_from_disk(self, include_archived: bool = False) -> list[Memory]:
        memories = []
        loaded_ids: set[str] = set()
        for file_path in self._iter_memory_files(self._get_load_directories(include_archived)):
            mem = self._load_file(file_path)
            if mem and mem.id not in loaded_ids:
                memories.append(mem)
                loaded_ids.add(mem.id)

        memories.sort(key=lambda x: x.timestamp)
        return memories

    def load_all(self, include_archived: bool = False) -> list[Memory]:
        """Retrieves all memories by merging the local and global memory banks (Federation).

        Uses Merkle directory digest invalidation caching for O(1) retrieval.
        """
        cache_key = (self.persona_id, include_archived)
        current_digest = self._compute_directory_digest(include_archived=include_archived)
        cached = self._CACHE.get(cache_key)

        if cached is not None and cached[0] == current_digest:
            return list(cached[1])

        memories = self._load_from_disk(include_archived=include_archived)
        self._CACHE[cache_key] = (current_digest, memories)
        return list(memories)

    def count_all(self, include_archived: bool = False) -> int:
        """
        Counts all memories in the federated storage without loading them (for performance).
        """
        return len(self.load_all(include_archived=include_archived))

    def get_stats(self) -> dict[str, Any]:
        """
        Returns a structured breakdown of memories across federated storage.
        """
        all_active = self.load_all(include_archived=False)
        all_with_archived = self.load_all(include_archived=True)
        subsumed = self.load_subsumed()

        by_scope: dict[str, int] = {}
        by_type: dict[str, int] = {}

        for mem in all_active:
            s_val = mem.scope.value if hasattr(mem.scope, 'value') else str(mem.scope).lower()
            t_val = mem.type.value if hasattr(mem.type, 'value') else str(mem.type).lower()
            by_scope[s_val] = by_scope.get(s_val, 0) + 1
            by_type[t_val] = by_type.get(t_val, 0) + 1

        archived_count = max(0, len(all_with_archived) - len(all_active))
        subsumed_count = len(subsumed)

        return {
            'total': len(all_active),
            'active': len(all_active),
            'archived': archived_count,
            'subsumed': subsumed_count,
            'by_scope': by_scope,
            'by_type': by_type,
        }

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
                return 'Missing ID/hash in file'

            expected_suffix = f'_{stored_id}.md' if file_path.suffix == '.md' else f'_{stored_id}.yaml'
            if not file_path.name.endswith(expected_suffix):
                return f'Filename does not match stored ID: {stored_id}'

            # Merkle Tombstone Redaction (EP-0143): Content was purged/redacted post-facto.
            # Hash in filename and frontmatter is preserved for relational graph continuity.
            if data.get('redacted'):
                return None

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
                    core_type=data.get('core_type'),
                    derived_principle=data.get('derived_principle'),
                    ethical_covenant=data.get('ethical_covenant'),
                    status=data.get('status', 'active'),
                )
            else:
                test_data = data.copy()
                if 'id' in test_data:
                    del test_data['id']
                recomputed_mem = Memory(**test_data)

            if recomputed_mem.id != stored_id:
                return f'Computed hash {recomputed_mem.id} does not match stored ID {stored_id}'
        except Exception as e:
            return f'Failed to parse or hash memory: {e}'
        else:
            return None

    def verify_integrity(self) -> list[tuple[Path, str]]:
        """
        Merkle Memory verification.
        Iterates through all .md and .yaml files in the active, archived and subsumed memory banks,
        recomputes the SHA-256 hashes of their contents, and asserts they match their filenames.
        Returns a list of tuples containing (file_path, error_reason) for any failures.
        """
        failures = []
        directories: list[Path | None] = [
            self.global_dir,
            self.global_archive_dir,
            self.global_subsumed_dir,
            self.global_dir.parent,
            self.global_dir.parent.parent / 'subsumed',
        ]

        if self.local_dir is not None:
            directories.extend(
                [
                    self.local_dir,
                    self.local_archive_dir,
                    self.local_subsumed_dir,
                    self.local_dir.parent,
                    self.local_dir.parent.parent / 'subsumed',
                ]
            )

        failures = []
        for file_path in self._iter_memory_files(directories):
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

                redacted_val = bool(data.get('redacted', False))
                redacted_at_raw = data.get('redacted_at')
                redacted_at_val = datetime.fromisoformat(str(redacted_at_raw)) if redacted_at_raw else None
                redaction_reason_val = data.get('redaction_reason')

                return Memory(
                    id=data.get('hash', ''),
                    timestamp=datetime.fromisoformat(str(data.get('timestamp'))),
                    type=MemoryType(type_val),
                    scope=MemoryScope(scope_val),
                    tags=data.get('tags', []),
                    content=body_part,
                    links=links,
                    source_session=data.get('source_session'),
                    core_type=data.get('core_type'),
                    derived_principle=data.get('derived_principle'),
                    ethical_covenant=data.get('ethical_covenant'),
                    status=data.get('status', 'active'),
                    redacted=redacted_val,
                    redacted_at=redacted_at_val,
                    redaction_reason=redaction_reason_val,
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
