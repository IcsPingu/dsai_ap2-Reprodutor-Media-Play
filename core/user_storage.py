"""Authenticated filesystem namespaces; mount MEDIA_PLAY_DATA on durable storage."""

from contextvars import ContextVar
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading
import json
import tempfile

_user = ContextVar("media_user", default=None)
_locks = {}
_guard = threading.Lock()


def data_root():
    return Path(os.environ.get("MEDIA_PLAY_DATA", "storage/private")).resolve()


@contextmanager
def database():
    data_root().mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(data_root() / "accounts.sqlite", timeout=15)
    connection.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY, salt TEXT NOT NULL, password TEXT NOT NULL)")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def account_name(name):
    name = name.strip().lower()
    if not re.fullmatch(r"[a-z0-9_-]{3,40}", name):
        raise ValueError("Use de 3 a 40 letras sem acento, números, _ ou - no usuário.")
    return name


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000).hex()


def register(name, password):
    name = account_name(name)
    if len(password) < 12:
        raise ValueError("A senha deve ter pelo menos 12 caracteres.")
    salt = secrets.token_hex(32)
    try:
        with database() as connection:
            connection.execute("INSERT INTO accounts VALUES (?, ?, ?)", (name, salt, password_hash(password, salt)))
    except sqlite3.IntegrityError as error:
        raise ValueError("Não foi possível cadastrar esse usuário.") from error
    return name


def authenticate(name, password):
    try:
        name = account_name(name)
    except ValueError:
        return None
    with database() as connection:
        row = connection.execute("SELECT salt, password FROM accounts WHERE name = ?", (name,)).fetchone()
    salt, expected = row if row else ("00" * 32, "00" * 32)
    actual = password_hash(password, salt)
    return name if hmac.compare_digest(actual, expected) and row else None


def select_user(name):
    """Call only with an identity established by server-side authentication."""
    return _user.set(account_name(name) if name is not None else None)


def reset_user(token):
    _user.reset(token)


def user_directory():
    name = _user.get()
    if name is None:
        return None
    key = hashlib.sha256(name.encode()).hexdigest()
    return data_root() / "users" / key


def scoped_path(legacy_path, relative):
    directory = user_directory()
    return str(directory / relative) if directory else legacy_path


def accessible_path(path):
    directory = user_directory()
    if directory is None:
        return True
    return Path(path).resolve().is_relative_to(directory)


def atomic_json(path, value):
    """Replace complete documents, so readers never observe a partial JSON file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def serialized(function):
    """Serialize read-modify-write operations within this single app process."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        key = str(user_directory() or "legacy")
        with _guard:
            lock = _locks.setdefault(key, threading.RLock())
        with lock:
            return function(*args, **kwargs)
    return wrapped
