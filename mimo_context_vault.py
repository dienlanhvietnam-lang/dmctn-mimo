"""Local MiMo context vault: snapshot / restore memory + DB outside mimocode wipe."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mimo_context_paths import (
    MANIFEST_VERSION,
    get_context_bundle_paths,
    get_context_bundles_dir,
    get_context_manifest_path,
    get_context_vault_dir,
)
import mimo_paths


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_slot_id() -> str:
    return f"ctx-{secrets.token_hex(3)}"


def _ensure_vault() -> None:
    os.makedirs(get_context_bundles_dir(), exist_ok=True)


def _load_manifest() -> dict[str, Any]:
    path = get_context_manifest_path()
    if not os.path.isfile(path):
        return {"version": MANIFEST_VERSION, "active_context_id": None, "slots": []}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("version", MANIFEST_VERSION)
    data.setdefault("active_context_id", None)
    data.setdefault("slots", [])
    return data


def _save_manifest(manifest: dict[str, Any]) -> str:
    _ensure_vault()
    path = get_context_manifest_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return path


def _client_hash() -> str:
    client_path = mimo_paths.get_mimo_identity_files().get("mimo-free-client", "")
    if not client_path or not os.path.isfile(client_path):
        return ""
    with open(client_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def _cli_version() -> str:
    try:
        root = Path(__file__).resolve().parent
        pkg = root / "mimo" / "package.json"
        if pkg.is_file():
            with open(pkg, encoding="utf-8") as f:
                return str(json.load(f).get("version", ""))
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return ""


def _arcname_for(path: str, data_dir: str) -> str:
    return os.path.relpath(path, data_dir).replace("\\", "/")


def create_context_snapshot(label: str = "", *, activate: bool = True) -> dict[str, Any]:
    """Tar existing context paths into vault; register in manifest."""
    _ensure_vault()
    data_dir = mimo_paths.get_mimo_data_dir()
    slot_id = _new_slot_id()
    bundle_name = f"{slot_id.replace('-', '_')}.tar.gz"
    bundle_path = os.path.join(get_context_bundles_dir(), bundle_name)

    existing = [p for p in get_context_bundle_paths() if os.path.exists(p)]
    if not existing:
        raise FileNotFoundError("No local context paths found to snapshot (memory/DB empty)")

    with tarfile.open(bundle_path, "w:gz") as tar:
        for path in existing:
            tar.add(path, arcname=_arcname_for(path, data_dir))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    entry = {
        "id": slot_id,
        "label": (label or f"context-{ts}").strip(),
        "saved_at": _utc_now_iso(),
        "bundle": bundle_name,
        "client_hash": _client_hash(),
        "cli_version": _cli_version(),
        "paths": [os.path.basename(p) for p in existing],
    }

    manifest = _load_manifest()
    manifest["slots"] = [s for s in manifest["slots"] if s["id"] != slot_id]
    manifest["slots"].append(entry)
    if activate:
        manifest["active_context_id"] = slot_id
    _save_manifest(manifest)

    return {
        "slot_id": slot_id,
        "label": entry["label"],
        "bundle": bundle_path,
        "client_hash": entry["client_hash"],
    }


def restore_context_snapshot(slot_id: str | None = None) -> str:
    """Extract a context bundle into mimocode data dir. Returns slot_id restored."""
    manifest = _load_manifest()
    slot_id = slot_id or manifest.get("active_context_id")
    if not slot_id:
        raise KeyError("No active context slot to restore")

    entry = next((s for s in manifest["slots"] if s["id"] == slot_id), None)
    if not entry:
        raise KeyError(f"context slot not found: {slot_id}")

    bundle_path = os.path.join(get_context_bundles_dir(), entry["bundle"])
    if not os.path.isfile(bundle_path):
        raise FileNotFoundError(f"context bundle missing: {bundle_path}")

    data_dir = mimo_paths.get_mimo_data_dir()
    os.makedirs(data_dir, exist_ok=True)

    # Remove existing context targets so restore is clean
    for path in get_context_bundle_paths():
        if not os.path.exists(path):
            continue
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                os.remove(path)
            except OSError:
                pass

    with tarfile.open(bundle_path, "r:gz") as tar:
        tar.extractall(path=data_dir)

    manifest["active_context_id"] = slot_id
    _save_manifest(manifest)
    return slot_id


def list_context_slots() -> dict[str, Any]:
    manifest = _load_manifest()
    active = manifest.get("active_context_id")
    slots = []
    for s in manifest.get("slots", []):
        slots.append(
            {
                "id": s["id"],
                "label": s.get("label", ""),
                "saved_at": s.get("saved_at", ""),
                "bundle": s.get("bundle", ""),
                "client_hash": s.get("client_hash", ""),
                "cli_version": s.get("cli_version", ""),
                "paths": s.get("paths", []),
                "active": s["id"] == active,
            }
        )
    return {
        "version": manifest.get("version", MANIFEST_VERSION),
        "active_context_id": active,
        "slots": slots,
        "count": len(slots),
    }


def get_active_context_id() -> str | None:
    return _load_manifest().get("active_context_id")


def activate_context_slot(slot_id: str) -> str:
    """Restore slot into mimocode and mark active."""
    return restore_context_snapshot(slot_id)


def delete_context_slot(slot_id: str) -> bool:
    manifest = _load_manifest()
    entry = next((s for s in manifest["slots"] if s["id"] == slot_id), None)
    if not entry:
        raise KeyError(f"context slot not found: {slot_id}")

    bundle_path = os.path.join(get_context_bundles_dir(), entry.get("bundle", ""))
    if os.path.isfile(bundle_path):
        os.remove(bundle_path)

    manifest["slots"] = [s for s in manifest["slots"] if s["id"] != slot_id]
    if manifest.get("active_context_id") == slot_id:
        manifest["active_context_id"] = manifest["slots"][-1]["id"] if manifest["slots"] else None
    _save_manifest(manifest)
    return True


def rename_context_slot(slot_id: str, label: str) -> dict[str, Any]:
    manifest = _load_manifest()
    entry = next((s for s in manifest["slots"] if s["id"] == slot_id), None)
    if not entry:
        raise KeyError(f"context slot not found: {slot_id}")
    entry["label"] = label.strip() or entry["label"]
    _save_manifest(manifest)
    return entry


def wipe_context_vault() -> int:
    """Delete all context slots and bundles. Returns number of slots removed."""
    manifest = _load_manifest()
    count = len(manifest.get("slots", []))
    vault = get_context_vault_dir()
    if os.path.isdir(vault):
        shutil.rmtree(vault, ignore_errors=True)
    return count


def has_local_context() -> bool:
    """True if any snapshottable context path exists on disk."""
    return any(os.path.exists(p) for p in get_context_bundle_paths())
