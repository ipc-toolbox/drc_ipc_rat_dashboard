#!/usr/bin/env python3
"""
Multi-partition KoboToolbox fetch + encrypt pipeline.

For each partition in partitions.json:
  1. Fetch data using that partition's own API token — Kobo's row-level
     permissions determine what each partition contains (server-enforced).
  2. Gzip-compress the CSV.
  3. Encrypt with AES-256-GCM using a passphrase-derived key.
  4. Write data/<name>.enc for publication in a (public) repo.

Output binary layout per .enc file — MUST match the app's Web Crypto decrypt:
    bytes 0..15   PBKDF2 salt (16 bytes)
    bytes 16..27  AES-GCM nonce/IV (12 bytes)
    bytes 28..    ciphertext (GCM auth tag appended)

Key derivation: PBKDF2-HMAC-SHA256, 200,000 iterations, 32-byte key.
(If you change iterations here, change them in the app's JS too.)
"""

import os
import sys
import json
import ssl
import gzip
import urllib.request
import urllib.error
from datetime import datetime, timezone

import pandas as pd
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── Configuration ────────────────────────────────────────────────────────
KOBO_URL          = os.environ.get("KOBO_URL", "https://kf.kobotoolbox.org")
KOBO_ASSET        = os.environ["KOBO_ASSET_UID"]
PAGE_SIZE         = 30000
PBKDF2_ITERATIONS = 200_000          # must match the app-side JS
PARTITIONS_FILE   = "partitions.json"
DATA_DIR          = "data"
META_PATH         = os.path.join(DATA_DIR, "kobo_meta.json")


# ── Kobo fetch (paginated) ───────────────────────────────────────────────
def fetch(token: str) -> list:
    url = (f"{KOBO_URL.rstrip('/')}/api/v2/assets/{KOBO_ASSET}"
           f"/data.json?format=json&limit={PAGE_SIZE}")
    headers = {"Authorization": f"Token {token}"}
    ctx, out = ssl.create_default_context(), []
    while url:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
                payload = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError({
                401: "authentication failed (bad token)",
                403: "permission denied (token lacks access)",
                404: "asset not found (check KOBO_ASSET_UID)",
            }.get(e.code, f"HTTP {e.code}"))
        out.extend(payload.get("results", []))
        url = payload.get("next")
        print(f"    …{len(out)} records")
    return out


# ── Encryption (format must match app-side Web Crypto) ──────────────────
def encrypt(data: bytes, passphrase: str) -> bytes:
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=salt, iterations=PBKDF2_ITERATIONS)
    key   = kdf.derive(passphrase.encode("utf-8"))
    nonce = os.urandom(12)
    ct    = AESGCM(key).encrypt(nonce, data, None)   # ct includes GCM tag
    return salt + nonce + ct


# ── Main ─────────────────────────────────────────────────────────────────
def main() -> int:
    os.makedirs(DATA_DIR, exist_ok=True)
    partitions = json.load(open(PARTITIONS_FILE, encoding="utf-8"))

    meta = {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "partitions": {},
    }
    n_ok = n_fail = 0

    for p in partitions:
        name  = p["name"]
        token = os.environ.get(p["token_env"], "").strip()
        pw    = os.environ.get(p["pass_env"], "").strip()

        if not token or not pw:
            print(f"::warning::Partition '{name}' skipped — "
                  f"missing secret {p['token_env']} or {p['pass_env']}.")
            meta["partitions"][name] = {"status": "skipped-missing-secrets"}
            n_fail += 1
            continue

        print(f"▶ Partition: {name}")
        try:
            records = fetch(token)
        except Exception as e:
            print(f"::warning::Partition '{name}' failed — {e}. "
                  f"Existing file (if any) is kept.")
            meta["partitions"][name] = {"status": f"failed: {e}"}
            n_fail += 1
            continue

        if not records:
            # Zero rows is more often a permissions mistake than reality —
            # keep the previous good file rather than clobbering it.
            print(f"::warning::Partition '{name}' returned 0 records — "
                  f"keeping existing file.")
            meta["partitions"][name] = {"status": "skipped-empty"}
            n_fail += 1
            continue

        df   = pd.json_normalize(records)
        csv  = df.to_csv(index=False).encode("utf-8")
        blob = encrypt(gzip.compress(csv, compresslevel=9), pw)

        out_path = os.path.join(DATA_DIR, f"{name}.enc")
        with open(out_path, "wb") as f:
            f.write(blob)

        meta["partitions"][name] = {
            "status":  "updated",
            "records": len(df),
            "size_kb": round(len(blob) / 1024, 1),
        }
        print(f"  ✅ {len(df)} records → {out_path} "
              f"({meta['partitions'][name]['size_kb']} KB)")
        n_ok += 1

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\nSummary: {n_ok} updated, {n_fail} skipped/failed "
          f"of {len(partitions)} partitions.")

    if n_ok == 0:
        print("::error::All partitions failed — nothing was updated.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())