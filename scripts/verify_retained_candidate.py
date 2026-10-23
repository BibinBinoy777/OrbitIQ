"""Retain verified, non-sensitive CI images/evidence; never load, run or deploy them.

Docker save is local and read-only. Offline verification hashes configurations and
uncompressed layers to establish the recorded image IDs, without extracting files.
Records are unsigned trusted-CI evidence, not production or scientific approval.
"""

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

import verify_release_evidence as release

MAX_UNPACKED = 2 * 1024**3
MAX_COMPRESSED = 512 * 1024**2
MAX_MEMBERS = 2048


def safe_name(name):
    parts = PurePosixPath(name)
    if not name or parts.is_absolute() or ".." in parts.parts or "\\" in name:
        raise ValueError("Unsafe retained artifact path")
    return name


def image_archive(path, images, source):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Image archive must be a regular file")
    expected = {spec["id"] for spec in images.values()}
    if len(expected) != 2 or any(
        not re.fullmatch(r"sha256:[a-f0-9]{64}", value) for value in expected
    ):
        raise ValueError("Exactly two image identities are required")
    hashes, payloads, total, seen = {}, {}, 0, set()
    with tarfile.open(path, "r|*") as archive:
        for member in archive:
            name = safe_name(member.name)
            if name in seen or len(seen) >= MAX_MEMBERS:
                raise ValueError("Duplicate or excessive archive members")
            seen.add(name)
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError("Archive links and special files are refused")
            total += member.size
            if total > MAX_UNPACKED:
                raise ValueError("Image archive exceeds verification limit")
            needed = name == "manifest.json" or any(
                name in (value[7:] + ".json", "blobs/sha256/" + value[7:])
                for value in expected
            )
            if needed and member.size > 2 * 1024**2:
                raise ValueError("Oversized image metadata")
            digest, chunks = hashlib.sha256(), []
            with archive.extractfile(member) as file:
                while chunk := file.read(1024 * 1024):
                    digest.update(chunk)
                    if needed:
                        chunks.append(chunk)
            hashes[name] = digest.hexdigest()
            if needed:
                payloads[name] = b"".join(chunks)
    manifests = json.loads(payloads["manifest.json"])
    if not isinstance(manifests, list) or len(manifests) != 2:
        raise ValueError("Image manifest must contain precisely the tested images")
    found, layers = set(), set()
    for item in manifests:
        config = safe_name(item["Config"])
        image_id = "sha256:" + hashes[config]
        if image_id not in expected or image_id in found:
            raise ValueError("Saved image configuration differs from tested identity")
        found.add(image_id)
        spec = json.loads(payloads[config])
        labels = spec.get("config", {}).get("Labels", {}) or {}
        if (
            labels.get("org.opencontainers.image.revision") != source["revision"]
            or labels.get("io.orbitiq.source-tree") != source["tree"]
        ):
            raise ValueError("Archived image has the wrong source labels")
        rootfs = spec["rootfs"]
        paths = [safe_name(p) for p in item["Layers"]]
        if (
            rootfs["type"] != "layers"
            or not paths
            or len(paths) != len(rootfs["diff_ids"])
            or ["sha256:" + hashes[p] for p in paths] != rootfs["diff_ids"]
        ):
            raise ValueError("Saved filesystem layers differ from tested image")
        layers.update(paths)
    if found != expected:
        raise ValueError("An expected image is missing")
    return {"images": sorted(found), "distinct_layers": len(layers)}


def copy_file(source, destination):
    # Reject symlink parents as well as symbolic files; never extract an archive.
    if any(p.is_symlink() for p in [source, *source.parents]):
        raise ValueError("Symbolic artifact inputs are refused")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def pack(record, directory, frontend, output):
    if output.exists() or output.is_symlink():
        raise ValueError("Candidate output must not exist")
    value = release.load(record)
    if (
        value.get("release_candidate") is not True
        or value["source"]["kind"] != "committed"
    ):
        raise ValueError("Only a verified committed candidate may be retained")
    release.verify_files(record, directory, frontend)
    if release.source() != value["source"]:
        raise ValueError("Current source differs from verified candidate")
    tag = value["images"]["api"]["reference"].split(":", 1)[1]
    if release.images(tag, value["source"]) != value["images"]:
        raise ValueError("Current image tags differ from verified candidate")
    output.mkdir(mode=0o700)  # A partial directory is never a success receipt.
    evidence = output / "evidence"
    names = [*value["evidence_sha256"], value["capture_name"], record.name]
    if record.parent.resolve() != directory.resolve():
        raise ValueError("Record must belong to the evidence directory")
    for name in names:
        safe_name(name)
        copy_file(directory / name, evidence / name)
    for name in value["frontend_files_sha256"]:
        safe_name(name)
        copy_file(frontend / name, output / "frontend" / name)
    env = os.environ.copy()
    for key in (
        "DOCKER_HOST",
        "DOCKER_CONTEXT",
        "DOCKER_TLS",
        "DOCKER_TLS_VERIFY",
        "DOCKER_CERT_PATH",
    ):
        env.pop(key, None)
    with tempfile.TemporaryDirectory(
        prefix="orbitiq-image-save-", dir=output.parent
    ) as temporary:
        raw = Path(temporary) / "images.tar"
        subprocess.run(
            [
                *release.DOCKER,
                "image",
                "save",
                "--output",
                str(raw),
                *[value["images"][role]["id"] for role in ("api", "web")],
            ],
            env=env,
            check=True,
            capture_output=True,
            timeout=180,
        )
        image_archive(raw, value["images"], value["source"])
        with (
            raw.open("rb") as incoming,
            (output / "images.tar.gz").open("xb") as outgoing,
        ):
            with gzip.GzipFile(
                filename="", fileobj=outgoing, mode="wb", mtime=0
            ) as compressed:
                shutil.copyfileobj(incoming, compressed)
    if (output / "images.tar.gz").stat().st_size > MAX_COMPRESSED:
        raise ValueError("Compressed image archive exceeds retention transfer limit")
    if (
        release.source() != value["source"]
        or release.images(tag, value["source"]) != value["images"]
    ):
        raise ValueError("Source or image tags changed while retaining candidate")
    manifest = {
        "schema_version": 1,
        "kind": "orbitiq_retained_candidate",
        "production_approved": False,
        "source": value["source"],
        "images": value["images"],
        "record_name": record.name,
        "files_sha256": release.inventory(output),
        "retention_days": 90,
    }
    release.write_new(output / "candidate.json", manifest)
    return verify(output)


def verify(directory, revision=None):
    manifest = release.load(directory / "candidate.json")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("kind") != "orbitiq_retained_candidate"
        or manifest.get("production_approved") is not False
        or manifest["source"]["kind"] != "committed"
        or (revision is not None and manifest["source"]["revision"] != revision)
    ):
        raise ValueError("Unsupported candidate or unexpected source revision")
    if (directory / "images.tar.gz").stat().st_size > MAX_COMPRESSED:
        raise ValueError("Compressed image archive exceeds retention transfer limit")
    actual = release.inventory(directory)
    del actual["candidate.json"]
    if actual != manifest["files_sha256"]:
        raise ValueError("Retained candidate files were changed, added or removed")
    name = safe_name(manifest["record_name"])
    if "/" in name:
        raise ValueError("Invalid retained record name")
    record = directory / "evidence" / name
    release.verify_files(record, directory / "evidence", directory / "frontend")
    value = release.load(record)
    if any(value[key] != manifest[key] for key in ("source", "images")):
        raise ValueError("Candidate identity differs from sealed verification")
    result = image_archive(
        directory / "images.tar.gz", manifest["images"], manifest["source"]
    )
    return {
        "status": "PASS",
        "revision": manifest["source"]["revision"],
        **result,
        "scope": "retained image/evidence integrity; not deployment approval",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    p = commands.add_parser("pack")
    p.add_argument("--record", type=Path, required=True)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--frontend", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = commands.add_parser("verify")
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--revision")
    args = parser.parse_args()
    try:
        result = (
            pack(args.record, args.directory, args.frontend, args.output)
            if args.operation == "pack"
            else verify(args.directory, args.revision)
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        tarfile.TarError,
        subprocess.SubprocessError,
    ):
        parser.exit(
            1, "Candidate retention refused; inspect inputs and trusted CI evidence.\n"
        )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
