"""Atomic corpus snapshots and an offline question-answering CLI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from common import norm, require

import domain

DEFAULT = Path(__file__).parent / "data" / "source.json"


def read(path, limit=8_000_000):
    with Path(path).open("rb") as handle:
        data = handle.read(limit + 1)
    require(len(data) <= limit, "file exceeds size limit")
    return json.loads(data.decode("utf-8-sig"))


def validate(rows):
    require(isinstance(rows, list), "expected an array of records")
    seen = set()
    for row in rows:
        require(isinstance(row, dict), "invalid record")
        for field in ("id", "source", *domain.FIELDS):
            require(isinstance(row.get(field), str) and row[field].strip(),
                    f"missing or invalid {field}")
        require(row["id"] not in seen, "duplicate citation ID")
        seen.add(row["id"])
    domain.validate(rows)
    return rows


def digest(rows):
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def build(source, snapshot):
    rows = validate(read(source))
    document = {"schema": domain.NAME + "/1", "digest": digest(rows), "rows": rows}
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=Path(snapshot).parent,
                                         delete=False, encoding="utf8") as handle:
            tmp = handle.name
            json.dump(document, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, snapshot)
    finally:
        if tmp:
            Path(tmp).unlink(missing_ok=True)


def load(snapshot):
    doc = read(snapshot, limit=64_000_000)
    require(isinstance(doc, dict) and doc.get("schema") == domain.NAME + "/1",
            "incompatible snapshot")
    rows = validate(doc.get("rows"))
    require(digest(rows) == doc.get("digest"), "snapshot checksum mismatch")
    return rows


def answer(rows, question):
    require(isinstance(question, str) and 0 < len(question.strip()) <= 1000,
            "question must contain 1–1000 characters")
    result = domain.solve(rows, norm(question))
    if result is None:
        return {"status": "insufficient_evidence", "answer": None, "citations": []}
    value, evidence, method = result
    return {"status": "answered", "answer": value, "method": method,
            "citations": [{"id": r["id"], "source": r["source"]} for r in evidence]}


def main():
    cli = argparse.ArgumentParser(description=domain.NAME)
    commands = cli.add_subparsers(dest="action", required=True)
    build_cmd = commands.add_parser("build")
    build_cmd.add_argument("source")
    build_cmd.add_argument("snapshot")
    ask = commands.add_parser("ask")
    ask.add_argument("question")
    ask.add_argument("--snapshot")
    args = cli.parse_args()
    try:
        if args.action == "build":
            if Path(args.source).resolve() == Path(args.snapshot).resolve():
                raise ValueError("choose a distinct snapshot path")
            build(args.source, args.snapshot)
        else:
            rows = load(args.snapshot) if args.snapshot else validate(read(DEFAULT))
            print(json.dumps(answer(rows, args.question), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
