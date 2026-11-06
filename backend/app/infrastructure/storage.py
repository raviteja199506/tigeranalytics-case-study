import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO, Protocol
from uuid import uuid4

from app.core.errors import PayloadTooLargeError

_MEBIBYTE = 1024 * 1024
_CHUNK_SIZE = _MEBIBYTE


@dataclass(frozen=True, slots=True)
class StoredFile:
    key: str
    checksum: str
    size_bytes: int


class FileStorage(Protocol):
    def save(self, source: BinaryIO, max_bytes: int) -> StoredFile: ...

    def open(self, key: str) -> BinaryIO: ...

    def delete(self, key: str) -> None: ...


class LocalFileStorage:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, source: BinaryIO, max_bytes: int) -> StoredFile:
        key = f"{datetime.now(UTC):%Y/%m/%d}/{uuid4().hex}.csv"
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        digest = hashlib.sha256()
        size = 0
        try:
            with path.open("wb") as target:
                while chunk := source.read(_CHUNK_SIZE):
                    size += len(chunk)
                    if size > max_bytes:
                        raise PayloadTooLargeError(
                            f"File exceeds the maximum upload size of {max_bytes // _MEBIBYTE} MB"
                        )
                    digest.update(chunk)
                    target.write(chunk)
        except BaseException:
            path.unlink(missing_ok=True)
            raise

        return StoredFile(key=key, checksum=digest.hexdigest(), size_bytes=size)

    def open(self, key: str) -> BinaryIO:
        return self._path(key).open("rb")

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if not path.is_relative_to(self._root):
            raise ValueError(f"Invalid storage key: {key}")
        return path
