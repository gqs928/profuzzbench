#!/usr/bin/env python3
"""Create small PostgreSQL v3.0, read-only session seeds."""
import argparse, hashlib, json, struct
from pathlib import Path

def startup(user, database):
    params = b"user\0" + user.encode() + b"\0database\0" + database.encode() + b"\0client_encoding\0UTF8\0application_name\0aflnet-pgwire\0\0"
    body = struct.pack("!I", 196608) + params
    return struct.pack("!I", len(body) + 4) + body

def message(kind, payload):
    return kind + struct.pack("!I", len(payload) + 4) + payload

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="root")
    ap.add_argument("--database", default="defaultdb")
    ap.add_argument("--password", default="", help="Include one PostgreSQL PasswordMessage after StartupMessage")
    ap.add_argument("--out", default="seeds")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    queries = {
        "01-select-one": "SELECT 1", "02-server-version": "SELECT version()",
        "03-current-database": "SELECT current_database()", "04-multi-statement": "SELECT 1; SELECT 2",
        "05-transaction-read-only": "BEGIN READ ONLY; SELECT 1; ROLLBACK",
        "06-syntax-error": "SELECT * FROM aflnet_missing_table", "07-show-databases": "SHOW DATABASES",
        "08-empty-query": "",
    }
    prefix = startup(args.user, args.database)
    if args.password: prefix += message(b"p", args.password.encode() + b"\0")
    records = []
    for name, sql in queries.items():
        data = prefix + message(b"Q", sql.encode() + b"\0") + message(b"X", b"")
        path = out / f"{name}.pg"; path.write_bytes(data)
        records.append({"file": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "sql": sql})
    (out / "manifest.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"generated={len(records)} user={args.user} database={args.database} password_message={bool(args.password)}")

if __name__ == "__main__": main()
