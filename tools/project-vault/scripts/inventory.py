#!/usr/bin/env python3
"""Read-only source inventory; private cache/report and deliberate public export.

No content sanitization, extraction, upload, deletion, or secret detection.
Uses only the Python standard library. Successful hashes resume per file.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import struct
import sys
import tarfile
import uuid
import zipfile

SCHEMA = 1
ZIP_SUFFIXES = (".zip", ".docx", ".xlsx", ".pptx", ".docm", ".xlsm", ".pptm",
                ".odt", ".ods", ".odp", ".epub", ".jar", ".whl")
TAR_SUFFIXES = (".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz")
OTHER_SUFFIXES = (".7z", ".rar", ".gz", ".bz2", ".xz", ".zst", ".iso", ".dmg")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def archive_type(name, header=b""):
    if header.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x06\x06")):
        return "zip"
    name = name.lower()
    if name.endswith(ZIP_SUFFIXES):
        return "zip"
    if name.endswith(TAR_SUFFIXES):
        return "tar"
    if name.endswith(OTHER_SUFFIXES):
        return "unsupported"
    if header[257:262] == b"ustar":
        return "tar"
    if header.startswith((b"\x1f\x8b", b"BZh", b"\xfd7zXZ\x00", b"7z\xbc\xaf\x27\x1c",
                          b"Rar!\x1a\x07", b"\x28\xb5\x2f\xfd")):
        return "unsupported"
    return None


def signature(st):
    return [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_mode]


def open_dir_strict(path):
    """Open every absolute path component with O_NOFOLLOW, retaining final fd."""
    absolute = os.path.abspath(path)
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in Path(absolute).parts[1:]:
            new_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                             dir_fd=descriptor)
            os.close(descriptor)
            descriptor = new_fd
        return descriptor, absolute
    except BaseException:
        os.close(descriptor)
        raise


def outside_source(path, source):
    resolved = os.path.realpath(path)
    if os.path.commonpath([resolved, source]) == source:
        raise ValueError("State/report/output must be outside the source tree")


def private_parent(path):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, mode=0o700, exist_ok=True)
    # Refuse symlinked output paths rather than overwriting their targets.
    fd, _ = open_dir_strict(parent)
    os.close(fd)
    if os.path.lexists(path) and os.path.islink(path):
        raise ValueError("Output/state path is a symlink")


def write_json(path, value, private=True):
    private_parent(path)
    tmp = str(path) + ".tmp-" + uuid.uuid4().hex
    mode = 0o600 if private else 0o644
    descriptor = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, path)
        os.chmod(path, mode)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def unsafe_member(name):
    normalized = name.replace("\\", "/")
    return (normalized.startswith("/") or ".." in PurePosixPath(normalized).parts
            or bool(re.match(r"^[A-Za-z]:", normalized)) or "\x00" in normalized)


def zip_metadata_size(handle):
    """Bound stdlib ZipFile's in-memory directory; handle ordinary and ZIP64 EOCD."""
    handle.seek(0, os.SEEK_END)
    end = handle.tell()
    start = max(0, end - 65557)
    handle.seek(start)
    tail = handle.read(end - start)
    pos = tail.rfind(b"PK\x05\x06")
    while pos >= 0:
        if len(tail) - pos >= 22:
            fields = struct.unpack("<4s4H2LH", tail[pos:pos + 22])
            if pos + 22 + fields[7] == len(tail):
                break
        pos = tail.rfind(b"PK\x05\x06", 0, pos)
    if pos < 0:
        raise ValueError("ZIP end record unavailable")
    if fields[1] != 0 or fields[2] != 0:
        raise ValueError("Multi-volume ZIP is unsupported")
    if fields[5] != 0xffffffff and fields[6] != 0xffffffff and fields[4] != 0xffff:
        return fields[5]
    locator_pos = start + pos - 20
    if locator_pos < 0:
        raise ValueError("ZIP64 locator unavailable")
    handle.seek(locator_pos)
    locator = struct.unpack("<4sLQL", handle.read(20))
    if locator[0] != b"PK\x06\x07" or locator[1] != 0 or locator[3] != 1:
        raise ValueError("Invalid or multi-volume ZIP64 locator")
    handle.seek(locator[2])
    record = struct.unpack("<4sQ2H2L4Q", handle.read(56))
    if record[0] != b"PK\x06\x06" or record[4] != 0 or record[5] != 0:
        raise ValueError("Invalid ZIP64 directory")
    return record[8]


def list_archive(handle, kind, limit, metadata_limit):
    result = {"format": kind, "status": "listed_top_level_only",
              "content_reviewed": False, "nested_archives_expanded": False, "entries": []}
    if kind == "unsupported":
        result["status"] = "unsupported_uninspected"
        return result
    try:
        if kind == "zip":
            if zip_metadata_size(handle) > metadata_limit:
                result["status"] = "metadata_limit_uninspected"
                return result
            handle.seek(0)
            with zipfile.ZipFile(handle) as container:
                for index, entry in enumerate(container.infolist()):
                    if index >= limit:
                        result["status"] = "entry_limit_partial"
                        break
                    entry_kind = "directory" if entry.is_dir() else "file"
                    if stat.S_ISLNK(entry.external_attr >> 16):
                        entry_kind = "symlink_unfollowed"
                    item = {"path": entry.filename, "kind": entry_kind, "size": entry.file_size,
                            "packed_size": entry.compress_size, "unsafe_path": unsafe_member(entry.filename),
                            "encrypted": bool(entry.flag_bits & 1)}
                    if archive_type(entry.filename):
                        item["nested_status"] = "uninspected"
                    result["entries"].append(item)
        else:
            handle.seek(0)
            with tarfile.open(fileobj=handle, mode="r|*") as container:
                for index, entry in enumerate(container):
                    if index >= limit:
                        result["status"] = "entry_limit_partial"
                        break
                    entry_kind = ("file" if entry.isfile() else "directory" if entry.isdir()
                                  else "link_unfollowed" if entry.issym() or entry.islnk() else "special")
                    item = {"path": entry.name, "kind": entry_kind, "size": entry.size,
                            "unsafe_path": unsafe_member(entry.name)}
                    if entry.issym() or entry.islnk():
                        item["link_target"] = entry.linkname
                    if archive_type(entry.name):
                        item["nested_status"] = "uninspected"
                    result["entries"].append(item)
    except (OSError, ValueError, EOFError, struct.error, zipfile.BadZipFile, tarfile.TarError) as error:
        result["status"] = "error_uninspected"
        result["error_type"] = type(error).__name__
    return result


def connect_state(path):
    private_parent(path)
    if not os.path.exists(path):
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        os.close(fd)
    descriptor = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError("State must be a regular file with exactly one hard link")
        os.fchmod(descriptor, 0o600)
    finally:
        os.close(descriptor)
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("CREATE TABLE IF NOT EXISTS entries (path TEXT PRIMARY KEY, value TEXT NOT NULL, scan TEXT NOT NULL)")
    return connection


def set_meta(connection, key, value):
    connection.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)", (key, json.dumps(value)))
    connection.commit()


def get_meta(connection, key):
    row = connection.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return json.loads(row[0]) if row else None


def read_entries(connection):
    return [json.loads(row[0]) for row in connection.execute("SELECT value FROM entries ORDER BY path")]


def inventory_id(entries):
    public_keys = ("path", "kind", "size", "sha256", "signature", "target", "error_type")
    canonical = [{key: entry[key] for key in public_keys if key in entry} for entry in entries]
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=True, sort_keys=True).encode()).hexdigest()


def assert_tree_unchanged(source, entries):
    """Fresh no-follow enumeration catches added/removed objects, not just edits."""
    expected = {entry["path"]: entry for entry in entries}
    seen = set()
    root_fd, _ = open_dir_strict(source)
    try:
        def visit(directory_fd, prefix=""):
            for name in sorted(os.listdir(directory_fd)):
                path = prefix + name
                current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                previous = expected.get(path)
                if previous is None or previous.get("signature") != signature(current):
                    raise ValueError("Source tree changed after scan; scan and review again")
                seen.add(path)
                if stat.S_ISLNK(current.st_mode):
                    if previous.get("target") != os.readlink(name, dir_fd=directory_fd):
                        raise ValueError("Source links changed after scan; scan and review again")
                elif stat.S_ISDIR(current.st_mode):
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                    dir_fd=directory_fd)
                    try:
                        if signature(os.fstat(child)) != signature(current):
                            raise ValueError("Source directory changed during recheck")
                        visit(child, path + "/")
                    finally:
                        os.close(child)
        visit(root_fd)
        if seen != set(expected):
            raise ValueError("Source entries disappeared after scan; scan and review again")
    finally:
        os.close(root_fd)


def scan(args):
    root_fd, source = open_dir_strict(args.root)
    try:
        for path in (args.state, args.report):
            outside_source(path, source)
        connection = connect_state(args.state)
        try:
            prior_source = get_meta(connection, "source")
            if prior_source and prior_source != source:
                raise ValueError("State belongs to a different source root")
            set_meta(connection, "source", source)
            set_meta(connection, "status", "running")
            scan_id = uuid.uuid4().hex
            started = now()
            errors = []
            reused = 0
            hashed = 0

            def save(entry):
                connection.execute("INSERT OR REPLACE INTO entries VALUES (?, ?, ?)",
                                   (entry["path"], json.dumps(entry, ensure_ascii=True), scan_id))
                connection.commit()

            def walk(directory_fd, prefix=""):
                nonlocal reused, hashed
                try:
                    names = sorted(os.listdir(directory_fd))
                except OSError as error:
                    errors.append({"path": prefix, "error_type": type(error).__name__})
                    return
                for name in names:
                    path = prefix + name
                    entry = {"path": path}
                    try:
                        before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                        entry["signature"] = signature(before)
                        if stat.S_ISLNK(before.st_mode):
                            entry.update(kind="symlink_unfollowed", target=os.readlink(name, dir_fd=directory_fd))
                        elif stat.S_ISDIR(before.st_mode):
                            entry["kind"] = "directory"
                            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                            dir_fd=directory_fd)
                            try:
                                if signature(os.fstat(child)) != signature(before):
                                    raise OSError("Directory changed during open")
                                save(entry)
                                walk(child, path + "/")
                            finally:
                                os.close(child)
                            continue
                        elif stat.S_ISREG(before.st_mode):
                            entry.update(kind="file", size=before.st_size)
                            cached_row = connection.execute("SELECT value FROM entries WHERE path = ?", (path,)).fetchone()
                            cached = json.loads(cached_row[0]) if cached_row else {}
                            file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                              dir_fd=directory_fd)
                            with os.fdopen(file_fd, "rb") as handle:
                                if signature(os.fstat(handle.fileno())) != signature(before):
                                    raise OSError("File changed during open")
                                if cached.get("signature") == entry["signature"] and cached.get("sha256"):
                                    entry["sha256"] = cached["sha256"]
                                    entry["hash_source"] = "cache"
                                    reused += 1
                                else:
                                    digest = hashlib.sha256()
                                    while True:
                                        chunk = handle.read(1024 * 1024)
                                        if not chunk:
                                            break
                                        digest.update(chunk)
                                    entry["sha256"] = digest.hexdigest()
                                    entry["hash_source"] = "read"
                                    hashed += 1
                                handle.seek(0)
                                kind = archive_type(name, handle.read(600))
                                if kind:
                                    entry["archive"] = list_archive(handle, kind, args.max_archive_entries,
                                                                    args.max_zip_metadata_mib * 1024 * 1024)
                                if signature(os.fstat(handle.fileno())) != signature(before):
                                    entry.pop("sha256", None)
                                    raise OSError("File changed during reading")
                        else:
                            entry["kind"] = "special_unread"
                    except OSError as error:
                        entry.pop("sha256", None)
                        entry["error_type"] = type(error).__name__
                        errors.append({"path": path, "error_type": type(error).__name__})
                    save(entry)

            walk(root_fd)
            connection.execute("DELETE FROM entries WHERE scan != ?", (scan_id,))
            connection.commit()
            entries = read_entries(connection)
            fingerprint = inventory_id(entries)
            status = "complete_with_errors" if errors else "complete"
            report = {"schema": SCHEMA, "visibility": "PRIVATE_DO_NOT_PUBLISH", "source_root": source,
                      "scan_started": started, "scan_finished": now(), "status": status,
                      "inventory_id": fingerprint, "hidden_files": "included", "symlinks": "never_followed",
                      "archive_coverage": "top_level_names_only; nested/content/metadata require separate review",
                      "archive_detection": "top-level extension and common magic; nested extension only; not exhaustive",
                      "hashing": "SHA-256; resumable per completed file; not an atomic snapshot",
                      "totals": {"entries": len(entries), "regular_files": sum(e.get("kind") == "file" for e in entries),
                                 "bytes": sum(e.get("size", 0) for e in entries if e.get("kind") == "file"),
                                 "hashes_read": hashed, "hashes_reused": reused},
                      "errors": errors, "entries": entries}
            set_meta(connection, "inventory_id", fingerprint)
            set_meta(connection, "status", status)
            set_meta(connection, "errors", errors)
            write_json(args.report, report)
            print(json.dumps({"status": status, "inventory_id": fingerprint, **report["totals"]}))
            return 2 if errors else 0
        finally:
            connection.close()
    finally:
        os.close(root_fd)


def public_manifest(args):
    # Read-only SQLite access: an absent/unfinished state must not create a new DB.
    state = Path(args.state).resolve(strict=True)
    connection = sqlite3.connect(state.as_uri() + "?mode=ro", uri=True)
    try:
        if get_meta(connection, "status") != "complete":
            raise ValueError("Inventory is unfinished or has filesystem errors")
        source = get_meta(connection, "source")
        outside_source(args.output, source)
        entries = read_entries(connection)
        assert_tree_unchanged(source, entries)
        fingerprint = inventory_id(entries)
        with open(args.review, encoding="utf-8") as handle:
            review = json.load(handle)
        if not isinstance(review, dict):
            raise ValueError("Review must be an object")
        if review.get("inventory_id") != fingerprint or fingerprint != get_meta(connection, "inventory_id"):
            raise ValueError("Review does not match the current inventory")
        project_id = review.get("project_id", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", project_id):
            raise ValueError("A neutral lowercase project_id is required")
        for flag in ("public_paths_reviewed", "content_and_metadata_reviewed", "secrets_reviewed", "rights_reviewed"):
            if review.get(flag) is not True:
                raise ValueError("Missing public-release review: " + flag)
        decisions = review.get("entries", {})
        if not isinstance(decisions, dict) or any(not isinstance(value, dict) for value in decisions.values()):
            raise ValueError("Entry decisions must be objects keyed by relative path")
        expected = {e["path"] for e in entries if e.get("kind") != "directory"}
        if set(decisions) != expected:
            raise ValueError("Every non-directory entry needs exactly one explicit decision")
        included = []
        excluded = 0
        for entry in entries:
            if entry.get("kind") == "directory":
                continue
            decision = decisions[entry["path"]]
            if decision.get("decision") == "exclude":
                if not isinstance(decision.get("reason"), str) or not decision["reason"].strip():
                    raise ValueError("Every exclusion needs an internal reason")
                excluded += 1
                continue
            if decision.get("decision") != "include":
                raise ValueError("Unknown entry decision")
            if entry.get("kind") != "file" or not entry.get("sha256") or unsafe_member(entry["path"]):
                raise ValueError("Only safely named, successfully hashed regular files can be exported")
            if entry.get("archive") and decision.get("archive_reviewed") is not True:
                raise ValueError("Included containers need separate content review")
            included.append({key: entry[key] for key in ("path", "size", "sha256")})
        # Check the cached inventory still describes the final local files. This is
        # a freshness guard, not a substitute for hashes of the uploaded bytes.
        root_fd, _ = open_dir_strict(source)
        try:
            by_path = {entry["path"]: entry for entry in entries}
            for item in included:
                directory_fd = os.dup(root_fd)
                try:
                    components = PurePosixPath(item["path"]).parts
                    for component in components[:-1]:
                        child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                        dir_fd=directory_fd)
                        os.close(directory_fd)
                        directory_fd = child
                    file_fd = os.open(components[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                      dir_fd=directory_fd)
                    try:
                        if signature(os.fstat(file_fd)) != by_path[item["path"]]["signature"]:
                            raise ValueError("Final files changed after scan; scan and review again")
                    finally:
                        os.close(file_fd)
                finally:
                    os.close(directory_fd)
        finally:
            os.close(root_fd)
        public_exclusions = review.get("public_exclusions", [])
        if not isinstance(public_exclusions, list) or any(not isinstance(x, str) for x in public_exclusions):
            raise ValueError("public_exclusions must be reviewed public strings")
        manifest = {"schema": SCHEMA, "project_id": project_id, "generated_at": now(),
                    "algorithm": "sha256", "files": included,
                    "totals": {"files": len(included), "bytes": sum(e["size"] for e in included),
                               "excluded_entries": excluded}, "public_exclusions": public_exclusions}
        write_json(args.output, manifest, private=False)
        print(json.dumps({"status": "public_manifest_written", **manifest["totals"]}))
        return 0
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    scan_parser = sub.add_parser("scan", help="Create a private, read-only source inventory")
    scan_parser.add_argument("root")
    scan_parser.add_argument("--state", required=True)
    scan_parser.add_argument("--report", required=True)
    scan_parser.add_argument("--max-archive-entries", type=int, default=100000)
    scan_parser.add_argument("--max-zip-metadata-mib", type=int, default=32)
    scan_parser.set_defaults(run=scan)
    public_parser = sub.add_parser("public-manifest", help="Export reviewed final paths and hashes only")
    public_parser.add_argument("--state", required=True)
    public_parser.add_argument("--review", required=True)
    public_parser.add_argument("--output", required=True)
    public_parser.set_defaults(run=public_manifest)
    args = parser.parse_args()
    if args.command == "scan" and (args.max_archive_entries < 1 or args.max_zip_metadata_mib < 1):
        parser.error("Archive bounds must be positive")
    try:
        return args.run(args)
    except (OSError, ValueError, sqlite3.Error, json.JSONDecodeError) as error:
        # Do not print potentially sensitive path strings from operating-system errors.
        print("Error (" + type(error).__name__ + "): " +
              (str(error) if isinstance(error, ValueError) else "operation failed; inspect private paths/state"),
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
