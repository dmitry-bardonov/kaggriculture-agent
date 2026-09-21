#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import tarfile
from pathlib import Path


def load_agent(source: Path):
    spec = importlib.util.spec_from_file_location("submission_contract_check", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    agent = getattr(module, "agent", None)
    if not callable(agent):
        raise RuntimeError(f"{source} does not export callable agent(obs)")
    return agent


def package(source: Path, output: Path) -> str:
    source = source.resolve()
    load_agent(source)
    raw = source.read_bytes()
    compile(raw, str(source), "exec")

    output.parent.mkdir(parents=True, exist_ok=True)
    info = tarfile.TarInfo("main.py")
    info.size = len(raw)
    info.mode = 0o644
    info.mtime = 0
    with tarfile.open(output, "w:gz") as archive:
        archive.addfile(info, io.BytesIO(raw))

    with tarfile.open(output, "r:gz") as archive:
        names = archive.getnames()
        if names != ["main.py"]:
            raise RuntimeError(f"Unexpected archive members: {names}")
        packaged = archive.extractfile("main.py")
        if packaged is None or packaged.read() != raw:
            raise RuntimeError("Packaged main.py differs from source")

    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    digest = package(args.source, args.output)
    print(f"created={args.output} sha256={digest}")


if __name__ == "__main__":
    main()

