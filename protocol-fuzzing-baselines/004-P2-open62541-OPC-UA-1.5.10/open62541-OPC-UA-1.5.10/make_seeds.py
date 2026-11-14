#!/usr/bin/env python3
"""Extract upstream OPC UA TCP seeds and add a valid HEL with memory trailer."""

import hashlib
import re
import shutil
import struct
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parent
source_archive = root / "source/open62541-v1.5.10-with-submodules.tar.gz"
seed_root = root / "seeds"
corpus = seed_root / "upstream-corpus"
formal_corpus = seed_root / "formal-corpus"
if corpus.exists():
    shutil.rmtree(corpus)
if formal_corpus.exists():
    shutil.rmtree(formal_corpus)
corpus.mkdir(parents=True, exist_ok=True)
formal_corpus.mkdir(parents=True, exist_ok=True)

prefix = "tests/fuzz/fuzz_binary_message_corpus/generated/"
with tarfile.open(source_archive, "r:gz") as archive:
    for member in archive.getmembers():
        normalized = member.name.removeprefix("./")
        if not normalized.startswith(prefix) or not member.isfile():
            continue
        name = normalized[len(prefix):]
        if "/" in name or not name.endswith(".bin"):
            continue
        source = archive.extractfile(member)
        if source is not None:
            (corpus / name).write_bytes(source.read())

url = b"opc.tcp://localhost:4840"
hello_body = struct.pack("<IIIII", 0, 65536, 65536, 0, 0) + struct.pack("<I", len(url)) + url
hello_packet = b"HELF" + struct.pack("<I", 8 + len(hello_body)) + hello_body
(seed_root / "opcua-hello.bin").write_bytes(hello_packet + struct.pack("<I", 0xFFFFFFFF))

# The upstream directory is made from many complete client/server exchanges,
# but fuzz_tcp_message starts a new server and sends exactly one message per
# iteration. Keep every upstream file, and use one deterministic seed per
# standalone message/service kind for the time-bounded formal campaign.
category_pattern = re.compile(r"^.*?_\d+_(.+)\.bin$")
by_category = {}
for path in sorted(corpus.glob("*.bin")):
    match = category_pattern.match(path.name)
    if match:
        by_category.setdefault(match.group(1), []).append(path)

selection = []
seen_hashes = set()
for category in sorted(by_category):
    source = by_category[category][0]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest not in seen_hashes:
        destination = formal_corpus / f"{category}.bin"
        shutil.copyfile(source, destination)
        seen_hashes.add(digest)
        selected = destination.name
    else:
        selected = next(
            item.name for item in formal_corpus.glob("*.bin")
            if hashlib.sha256(item.read_bytes()).hexdigest() == digest
        )
    selection.append(f"{category}\t{source.name}\t{selected}\t{digest}\n")

hello_digest = hashlib.sha256((seed_root / "opcua-hello.bin").read_bytes()).hexdigest()
if hello_digest not in seen_hashes:
    shutil.copyfile(seed_root / "opcua-hello.bin", formal_corpus / "valid-hello.bin")
    selection.append(f"custom-valid-hello\topcua-hello.bin\tvalid-hello.bin\t{hello_digest}\n")
else:
    selected = next(
        item.name for item in formal_corpus.glob("*.bin")
        if hashlib.sha256(item.read_bytes()).hexdigest() == hello_digest
    )
    selection.append(f"custom-valid-hello\topcua-hello.bin\t{selected}\t{hello_digest}\n")
(seed_root / "FORMAL_CORPUS_SELECTION.tsv").write_text(
    "category\tselected_upstream_file\tformal_file\tsha256\n" + "".join(selection),
    encoding="utf-8",
)

dict_member = "tests/fuzz/fuzz_binary_message_header.dict"
with tarfile.open(source_archive, "r:gz") as archive:
    member = next(m for m in archive.getmembers() if m.name.removeprefix("./") == dict_member)
    source = archive.extractfile(member)
    assert source is not None
    with (seed_root / "fuzz_binary_message_header.dict").open("wb") as output:
        shutil.copyfileobj(source, output)

entries = sorted(p for p in seed_root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")
manifest = "".join(
    f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}\n"
    for p in entries
)
(seed_root / "SHA256SUMS.txt").write_text(manifest, encoding="utf-8")
print(
    f"upstream_seeds={len(list(corpus.glob('*.bin')))} "
    f"categories={len(by_category)} formal_seeds={len(list(formal_corpus.glob('*.bin')))} "
    f"total_seed_files={len(entries)}"
)
