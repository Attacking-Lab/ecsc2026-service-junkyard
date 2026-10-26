import os
import fcntl
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import NewType, Annotated

from fastapi.params import Query
from redis.asyncio import Redis

Username = NewType("Username", Annotated[str, Query(min_length=3, max_length=64)])
Password = NewType("Password", Annotated[str, Query(min_length=5, max_length=64)])
PathComponent = NewType("PathComponent", Annotated[str, Query(min_length=1, max_length=80, pattern=r"^[\w-]+$")])

BASE_STORAGE = Path(__file__).absolute().parent / "data"
if "BASE_DIR" in os.environ:
    BASE_STORAGE = Path(os.environ["BASE_DIR"])
SECRET_STORAGE = BASE_STORAGE / "secrets"
FILE_STORAGE = BASE_STORAGE / "files"


def init_storage() -> None:
    BASE_STORAGE.mkdir(exist_ok=True)
    SECRET_STORAGE.mkdir(exist_ok=True, mode=0o700)
    FILE_STORAGE.mkdir(exist_ok=True, mode=0o755)


def get_redis() -> Redis:
    return Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, db=0)


SECRET_LENGTH = 32


def _read_secret(path: Path) -> bytes:
    secret = path.read_bytes()
    if len(secret) != SECRET_LENGTH:
        raise RuntimeError(f"Secret {path} is corrupt (expected {SECRET_LENGTH} bytes, got {len(secret)})")
    return secret


@lru_cache()
def get_secret(what: str) -> bytes:
    secret_path = SECRET_STORAGE / what
    try:
        return _read_secret(secret_path)
    except FileNotFoundError:
        pass

    SECRET_STORAGE.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(SECRET_STORAGE / f".{what}.lock", "a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            return _read_secret(secret_path)
        except FileNotFoundError:
            pass
        fd, tmp_path = tempfile.mkstemp(dir=SECRET_STORAGE, prefix=f".{what}.")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(os.urandom(SECRET_LENGTH))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, secret_path)
        except BaseException:
            os.unlink(tmp_path)
            raise
        return _read_secret(secret_path)
