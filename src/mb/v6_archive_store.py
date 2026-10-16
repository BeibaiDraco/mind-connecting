"""External lossless container for immutable archives; no torch or GPU imports.

Original files are never edited/deleted. A failed pack/restore retains its new
directory without a completion manifest. ZIP storage boundaries improve sharing
without loading pickle or interpreting tensor values.
"""
from __future__ import annotations

from collections import OrderedDict
import hashlib
import json
import os
from pathlib import Path
import struct
import zipfile
import zlib

VERSION = "v6-lossless-container-1"
INDEX = struct.Struct("<32sQII B7x")
REF = struct.Struct("<I")
FILES = ("blocks.bin", "index.bin", "refs.bin")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _name(name: str) -> str:
    if (type(name) is not str or not name or Path(name).name != name
            or name in (".", "..", "restore_receipt.json")):
        raise ValueError("Archive names must be single safe path components")
    return name


def _cuts(path: Path, size: int) -> list[int]:
    """Keep every byte; only reset chunk alignment at stored ZIP tensor spans."""
    cuts = {0, size}
    if not zipfile.is_zipfile(path):
        return sorted(cuts)
    with zipfile.ZipFile(path) as z, path.open("rb") as raw:
        spans = []
        for info in z.infolist():
            if "/data/" not in info.filename:
                continue
            if info.compress_type != zipfile.ZIP_STORED or info.flag_bits & 1:
                raise ValueError("Only unencrypted stored tensor ZIP members supported")
            raw.seek(info.header_offset)
            header = raw.read(30)
            if len(header) != 30 or header[:4] != b"PK\x03\x04":
                raise ValueError("Invalid local ZIP header")
            filename, extra = struct.unpack_from("<HH", header, 26)
            start = info.header_offset + 30 + filename + extra
            end = start + info.file_size
            if not 0 <= start <= end <= size:
                raise ValueError("ZIP storage outside original file")
            spans.append((start, end)); cuts.update((start, end))
        spans.sort()
        if any(a[1] > b[0] for a, b in zip(spans, spans[1:])):
            raise ValueError("Overlapping ZIP storage spans")
    return sorted(cuts)


def _sync(f) -> None:
    f.flush(); os.fsync(f.fileno())


def pack(sources: list[dict], directory: Path, *, block_bytes: int = 1024,
         max_blocks: int = 2_000_000) -> dict:
    """Sources require original name/path/bytes/sha256; unique new output only."""
    if (type(block_bytes) is not int or not 256 <= block_bytes <= 1024 * 1024
            or type(max_blocks) is not int or not 1 <= max_blocks <= 2_000_000 or not sources):
        raise ValueError("Invalid bounded container layout")
    names = [_name(row["name"]) for row in sources]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate source names")
    for row in sources:
        path = Path(row["path"])
        if path.is_symlink() or not path.is_file() or path.stat().st_size != row["bytes"]:
            raise ValueError("Missing, linked or changed source")
    directory = Path(directory)
    directory.mkdir(exist_ok=False, parents=False)
    seen: dict[tuple[bytes, int], int] = {}
    records, ref_count, offset = [], 0, 0
    with (directory/FILES[0]).open("xb") as data, (directory/FILES[1]).open("xb") as index, (
            directory/FILES[2]).open("xb") as refs:
        for row in sources:
            path = Path(row["path"])
            stat = path.stat()
            boundaries = _cuts(path, row["bytes"])
            h, start_ref = hashlib.sha256(), ref_count
            with path.open("rb") as source:
                for start, end in zip(boundaries, boundaries[1:]):
                    remaining = end - start
                    while remaining:
                        block = source.read(min(block_bytes, remaining))
                        if not block:
                            raise ValueError("Source truncated during packing")
                        remaining -= len(block); h.update(block)
                        digest = hashlib.sha256(block).digest()
                        key = (digest, len(block))
                        if key not in seen:
                            if len(seen) >= max_blocks:
                                raise ValueError("Container metadata bound reached")
                            number = len(seen)
                            compressed = zlib.compress(block, 1)
                            codec = int(len(compressed) + 16 < len(block))
                            stored = compressed if codec else block
                            data.write(stored)
                            index.write(INDEX.pack(digest, offset, len(stored), len(block), codec))
                            offset += len(stored); seen[key] = number
                        refs.write(REF.pack(seen[key])); ref_count += 1
                if source.read(1):
                    raise ValueError("Source grew during packing")
            after = path.stat()
            if h.hexdigest() != row["sha256"] or any(getattr(after, k) != getattr(stat, k)
                    for k in ("st_dev", "st_ino", "st_size", "st_mtime_ns")):
                raise ValueError("Original source integrity changed")
            records.append({"name": row["name"], "bytes": row["bytes"],
                            "sha256": row["sha256"], "ref_start": start_ref,
                            "ref_count": ref_count-start_ref})
        for f in (data, index, refs):
            _sync(f)
    manifest = {"version": VERSION, "block_bytes": block_bytes, "blocks": len(seen),
        "references": ref_count, "files": records, "scientific_admission": False,
        "container": {name: {"bytes": (directory/name).stat().st_size,
                             "sha256": sha256(directory/name)} for name in FILES}}
    with (directory/"manifest.json").open("x") as f:
        json.dump(manifest, f, sort_keys=True, indent=2); _sync(f)
    return manifest


def restore(directory: Path, output: Path, *, expected_manifest_sha256: str,
            cache_bytes: int = 64*1024*1024) -> dict:
    """Reconstruct original files and original SHA256s; refuse existing output."""
    if type(cache_bytes) is not int or not 0 <= cache_bytes <= 256*1024*1024:
        raise ValueError("Invalid restore cache bound")
    directory, output = Path(directory), Path(output)
    manifest_bytes=(directory/"manifest.json").read_bytes()
    manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_sha256 != expected_manifest_sha256:
        raise ValueError("Externally bound manifest checksum mismatch")
    m = json.loads(manifest_bytes)
    if m.get("version") != VERSION or set(m["container"]) != set(FILES):
        raise ValueError("Unknown container")
    if (type(m["block_bytes"]) is not int or not 256 <= m["block_bytes"] <= 1024*1024
            or type(m["blocks"]) is not int or not 0 <= m["blocks"] <= 2_000_000
            or type(m["references"]) is not int or m["references"] < 0):
        raise ValueError("Invalid container bounds")
    names = [_name(row["name"]) for row in m["files"]]
    if not names or len(names) != len(set(names)):
        raise ValueError("Missing/duplicate restored files")
    for name, record in m["container"].items():
        path = directory/name
        if path.is_symlink() or path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
            raise ValueError("Container checksum mismatch")
    if (m["container"]["index.bin"]["bytes"] != m["blocks"]*INDEX.size
            or m["container"]["refs.bin"]["bytes"] != m["references"]*REF.size):
        raise ValueError("Container index/reference size mismatch")
    cursor = 0
    for row in m["files"]:
        if (any(type(row[k]) is not int or row[k] < 0 for k in ("bytes", "ref_start", "ref_count"))
                or row["ref_start"] != cursor):
            raise ValueError("Non-contiguous or invalid file reference table")
        cursor += row["ref_count"]
    if cursor != m["references"]:
        raise ValueError("Incomplete file reference table")
    output.mkdir(exist_ok=False, parents=False)
    cache, retained = OrderedDict(), 0
    recovered = []
    with (directory/"blocks.bin").open("rb") as data, (directory/"index.bin").open("rb") as index, (
            directory/"refs.bin").open("rb") as refs:
        for row in m["files"]:
            h, size = hashlib.sha256(), 0
            with (output/row["name"]).open("xb") as destination:
                for _ in range(row["ref_count"]):
                    number, = REF.unpack(refs.read(REF.size))
                    if number >= m["blocks"]:
                        raise ValueError("Reference outside block inventory")
                    if number in cache:
                        block = cache.pop(number); cache[number] = block
                    else:
                        index.seek(number*INDEX.size)
                        digest, start, stored_size, raw_size, codec = INDEX.unpack(index.read(INDEX.size))
                        if (not 0 < raw_size <= m["block_bytes"] or codec not in (0, 1)
                                or not 0 < stored_size <= m["block_bytes"]
                                or start+stored_size > m["container"]["blocks.bin"]["bytes"]):
                            raise ValueError("Invalid stored block")
                        data.seek(start); stored = data.read(stored_size)
                        if codec:
                            decoder = zlib.decompressobj()
                            block = decoder.decompress(stored, raw_size+1)
                            if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
                                raise ValueError("Invalid or excessive compressed block")
                        else:
                            block = stored
                        if len(block) != raw_size or hashlib.sha256(block).digest() != digest:
                            raise ValueError("Block checksum mismatch")
                        if len(block) <= cache_bytes:
                            while cache and retained+len(block) > cache_bytes:
                                _, old = cache.popitem(last=False); retained -= len(old)
                            cache[number] = block; retained += len(block)
                    size += len(block)
                    if size > row["bytes"]:
                        raise ValueError("Restored file exceeds declared size")
                    destination.write(block); h.update(block)
                _sync(destination)
            if size != row["bytes"] or h.hexdigest() != row["sha256"]:
                raise ValueError("Original file restoration checksum mismatch")
            recovered.append({"name": row["name"], "bytes": size, "sha256": h.hexdigest()})
    receipt = {"version": VERSION, "status": "restored_exact_bytes", "files": recovered,
               "container_manifest_sha256": manifest_sha256}
    with (output/"restore_receipt.json").open("x") as f:
        json.dump(receipt, f, sort_keys=True, indent=2); _sync(f)
    return receipt
