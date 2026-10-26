#!/usr/bin/env python3
"""Local encrypted project lookup. No networking, keychain access or publication.

Requires cryptography. Records and find queries arrive as JSON on stdin, never
as command-line arguments. Only find deliberately prints private records.
"""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import unicodedata
from urllib.parse import urlsplit

HEADER = b"PROJECT-VAULT-CATALOG\x01"
AAD = HEADER
KEY_FILE = "catalog.key"
DATA_FILE = "catalog.enc"
LOCK_FILE = ".catalog.lock"
MAX_BYTES = 16 * 1024 * 1024
DEFAULT_DIRECTORY = Path.home() / ".codex" / "project-vault" / "private"


class CatalogError(Exception):
    pass


def aesgcm(key):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        raise CatalogError("cryptography is required; use the bundled Python or install it in a user environment") from None
    return AESGCM(key)


def file_stat(directory, name):
    try:
        info = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
        raise CatalogError("Refusing a symlink, hardlink, special file or foreign-owned private file")
    if stat.S_IMODE(info.st_mode) != 0o600:
        raise CatalogError("Existing private files must have permission 0600")
    return info


def identity(info):
    return None if info is None else (info.st_dev, info.st_ino, info.st_size,
                                     info.st_mtime_ns, info.st_ctime_ns, info.st_mode)


def private_directory(path, create):
    """Use directory descriptors and reject symlinks in every path component."""
    absolute = Path(os.path.abspath(os.path.expanduser(path)))
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in absolute.parts[1:]:
            if create:
                try:
                    os.mkdir(component, mode=0o700, dir_fd=directory)
                except FileExistsError:
                    pass
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        info = os.fstat(directory)
        if info.st_uid != os.getuid():
            raise CatalogError("Private directory must belong to the current user")
        if create:
            os.fchmod(directory, 0o700)
        elif stat.S_IMODE(info.st_mode) != 0o700:
            raise CatalogError("Private directory must have permission 0700")
        return directory
    except BaseException:
        os.close(directory)
        raise


@contextmanager
def locked_directory(path, create=False):
    directory = private_directory(path, create)
    lock = None
    try:
        prior = file_stat(directory, LOCK_FILE)
        flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
        if prior is None:
            flags |= os.O_CREAT | os.O_EXCL
        lock = os.open(LOCK_FILE, flags, 0o600, dir_fd=directory)
        current = os.fstat(lock)
        if not stat.S_ISREG(current.st_mode) or current.st_nlink != 1 or current.st_uid != os.getuid():
            raise CatalogError("Unsafe catalog lock")
        if prior is not None and identity(prior) != identity(current):
            raise CatalogError("Catalog lock changed during open")
        if prior is None:
            os.fchmod(lock, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        # Recheck the lock path after waiting; do not lock an unlinked old file.
        if os.stat(LOCK_FILE, dir_fd=directory, follow_symlinks=False).st_ino != current.st_ino:
            raise CatalogError("Catalog lock was replaced")
        yield directory
    finally:
        if lock is not None:
            os.close(lock)
        os.close(directory)


def read_private(directory, name):
    before = file_stat(directory, name)
    if before is None:
        raise CatalogError("Catalog is not initialized or a required private file is missing")
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(descriptor, "rb") as handle:
        if identity(os.fstat(handle.fileno())) != identity(before):
            raise CatalogError("Private file changed during open")
        data = handle.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES or identity(os.fstat(handle.fileno())) != identity(before):
            raise CatalogError("Private file is too large or changed during read")
    return data


def atomic_write(directory, name, data):
    before = file_stat(directory, name)
    temporary = ".catalog-" + secrets.token_hex(12) + ".tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if identity(file_stat(directory, name)) != identity(before):
            raise CatalogError("Private destination changed during write")
        os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass


def read_key(directory):
    key = read_private(directory, KEY_FILE)
    if len(key) != 32:
        raise CatalogError("Invalid catalog key")
    return key


def encrypt(key, catalog):
    plaintext = json.dumps(catalog, ensure_ascii=False, sort_keys=True).encode("utf-8")
    if len(plaintext) + len(HEADER) + 28 > MAX_BYTES:
        raise CatalogError("Catalog size limit reached")
    nonce = secrets.token_bytes(12)
    return HEADER + nonce + aesgcm(key).encrypt(nonce, plaintext, AAD)


def read_catalog(directory, key):
    data = read_private(directory, DATA_FILE)
    if not data.startswith(HEADER) or len(data) < len(HEADER) + 28:
        raise CatalogError("Unsupported or damaged catalog format")
    nonce = data[len(HEADER):len(HEADER) + 12]
    ciphertext = data[len(HEADER) + 12:]
    try:
        from cryptography.exceptions import InvalidTag
        plaintext = aesgcm(key).decrypt(nonce, ciphertext, AAD)
    except ImportError:
        raise CatalogError("cryptography is required; use the bundled Python or install it in a user environment") from None
    except InvalidTag:
        raise CatalogError("Catalog authentication failed: wrong key or changed ciphertext") from None
    try:
        catalog = json.loads(plaintext)
        if not isinstance(catalog, dict) or catalog.get("schema") != 1 or not isinstance(catalog.get("records"), list):
            raise ValueError
        records = [validate_record(record) for record in catalog["records"]]
        if len({record["id"] for record in records}) != len(records):
            raise ValueError
    except (ValueError, TypeError, UnicodeError, CatalogError):
        raise CatalogError("Invalid encrypted catalog records") from None
    return {"schema": 1, "records": records}


def normalized(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def validate_record(record):
    required = {"aliases", "id", "repo", "telegram_url", "status"}
    if not isinstance(record, dict) or set(record) != required:
        raise CatalogError("Record needs exactly aliases, id, repo, telegram_url and status")
    identifier = record["id"]
    if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", identifier):
        raise CatalogError("A neutral lowercase project id is required")
    aliases = record["aliases"]
    if (not isinstance(aliases, list) or not 1 <= len(aliases) <= 100
            or any(not isinstance(alias, str) or not normalized(alias) or len(alias) > 256 for alias in aliases)):
        raise CatalogError("aliases must be a nonempty list of short search strings")
    for field in ("repo", "telegram_url"):
        value = record[field]
        if not isinstance(value, str) or len(value) > 2048:
            raise CatalogError("Repository and Telegram links must be short strings")
        if value:
            parts = urlsplit(value)
            if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
                raise CatalogError("Links must be HTTPS URLs without embedded credentials")
    if not isinstance(record["status"], str) or not record["status"].strip() or len(record["status"]) > 160:
        raise CatalogError("A short status string is required")
    return {"id": identifier, "aliases": list(dict.fromkeys(alias.strip() for alias in aliases)),
            "repo": record["repo"], "telegram_url": record["telegram_url"], "status": record["status"].strip()}


def stdin_json():
    raw = sys.stdin.buffer.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise CatalogError("JSON input is too large")
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError):
        raise CatalogError("Expected one valid JSON value on stdin") from None


def run(args):
    if args.command == "init":
        with locked_directory(args.directory, create=True) as directory:
            key_exists = file_stat(directory, KEY_FILE) is not None
            data_exists = file_stat(directory, DATA_FILE) is not None
            if data_exists and not key_exists:
                raise CatalogError("Existing catalog has no key; restore its original key instead of reinitializing")
            if not key_exists:
                atomic_write(directory, KEY_FILE, secrets.token_bytes(32))
            key = read_key(directory)
            if not data_exists:
                atomic_write(directory, DATA_FILE, encrypt(key, {"schema": 1, "records": []}))
            catalog = read_catalog(directory, key)
            return {"status": "catalog_ready", "records": len(catalog["records"])}
    payload = stdin_json()
    if args.command == "put":
        payload = validate_record(payload)
    elif (not isinstance(payload, dict) or set(payload) != {"query"}
          or not isinstance(payload["query"], str) or not normalized(payload["query"]) or len(payload["query"]) > 256):
        raise CatalogError("Find needs one nonempty query string on stdin")
    with locked_directory(args.directory) as directory:
        key = read_key(directory)
        catalog = read_catalog(directory, key)
        if args.command == "put":
            records = {record["id"]: record for record in catalog["records"]}
            records[payload["id"]] = payload
            catalog["records"] = sorted(records.values(), key=lambda record: record["id"])
            atomic_write(directory, DATA_FILE, encrypt(key, catalog))
            return {"status": "record_saved", "id": payload["id"], "records": len(records)}
        query = normalized(payload["query"])
        matches = [record for record in catalog["records"]
                   if query == record["id"] or any(query in normalized(alias) for alias in record["aliases"])]
        return {"status": "private_search_result", "count": len(matches), "records": matches}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default=str(DEFAULT_DIRECTORY), help="Private directory outside projects")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="Initialize or verify a catalog")
    subparsers.add_parser("put", help="Save one JSON record from stdin")
    subparsers.add_parser("find", help="Read a JSON query from stdin; stdout contains private matching records")
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=True, sort_keys=True))
        return 0
    except CatalogError as error:
        print("Error: " + str(error), file=sys.stderr)
    except (OSError, ValueError):
        # OS and URL-parser messages may contain private filenames or input data.
        print("Error: private catalog operation failed; no private values were printed", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
