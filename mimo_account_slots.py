"""Dynamic MiMo Pro account slot store (manifest + auth.json snapshots)."""
from __future__ import annotations

import json
import os
import secrets
import shutil
from datetime import datetime, timezone
from typing import Any

from colorama import Fore, Style

from mimo_paths import (
    get_mimo_accounts_dir,
    get_mimo_auth_path,
    get_mimo_manifest_path,
)

MANIFEST_VERSION = 1

EMOJI = {
    "SUCCESS": "✅",
    "ERROR": "❌",
    "INFO": "ℹ️",
    "WARNING": "⚠️",
}


def _msg(translator, key, fallback, **kwargs):
    if translator:
        try:
            return translator.get(key, **kwargs)
        except Exception:
            pass
    return fallback.format(**kwargs) if kwargs else fallback


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_slot_id() -> str:
    return f"slot-{secrets.token_hex(3)}"


def _slot_filename(slot_id: str) -> str:
    return f"{slot_id.replace('-', '_')}.json"


def _ensure_accounts_dir() -> str:
    path = get_mimo_accounts_dir()
    os.makedirs(path, exist_ok=True)
    return path


def _load_manifest_raw() -> dict[str, Any]:
    path = get_mimo_manifest_path()
    if not os.path.isfile(path):
        return {"version": MANIFEST_VERSION, "active_slot_id": None, "slots": []}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("version", MANIFEST_VERSION)
    data.setdefault("active_slot_id", None)
    data.setdefault("slots", [])
    return data


def _save_manifest(manifest: dict[str, Any]) -> str:
    _ensure_accounts_dir()
    path = get_mimo_manifest_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return path


def _read_auth_dict(auth_path: str | None = None) -> dict[str, Any]:
    path = auth_path or get_mimo_auth_path()
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def mask_key_prefix(key: str | None, visible: int = 8) -> str:
    if not key:
        return ""
    key = key.strip()
    if len(key) <= visible:
        return key[:2] + "…"
    return f"{key[:visible]}…"


def extract_xiaomi_meta(auth_dict: dict[str, Any]) -> dict[str, str]:
    """Return uid and masked key prefix from xiaomi block (never full key)."""
    block = auth_dict.get("xiaomi") or {}
    meta = block.get("metadata") or {}
    uid = str(meta.get("uid") or meta.get("user_id") or "")
    key = block.get("key") or ""
    return {
        "uid": uid,
        "key_prefix": mask_key_prefix(key),
        "type": str(block.get("type") or ""),
    }


def _slot_entry_for_list(entry: dict[str, Any], active_id: str | None) -> dict[str, Any]:
    meta = extract_xiaomi_meta(_read_auth_dict(os.path.join(get_mimo_accounts_dir(), entry.get("file", ""))))
    return {
        "id": entry["id"],
        "label": entry.get("label", ""),
        "chrome_profile": entry.get("chrome_profile", ""),
        "chrome_display_name": entry.get("chrome_display_name", ""),
        "xiaomi_uid": entry.get("xiaomi_uid") or meta["uid"],
        "key_prefix": meta["key_prefix"],
        "saved_at": entry.get("saved_at", ""),
        "file": entry.get("file", ""),
        "active": entry["id"] == active_id,
    }


def load_manifest() -> dict[str, Any]:
    """Return raw manifest dict (active_slot_id + slots entries)."""
    return _load_manifest_raw()


def list_slots() -> dict[str, Any]:
    manifest = _load_manifest_raw()
    active_id = manifest.get("active_slot_id")
    slots = [_slot_entry_for_list(s, active_id) for s in manifest.get("slots", [])]
    return {
        "version": manifest.get("version", MANIFEST_VERSION),
        "active_slot_id": active_id,
        "slots": slots,
        "count": len(slots),
    }


def list_slot_entries() -> list[dict[str, Any]]:
    """Return slot list with masked keys (for manage UI)."""
    return list_slots()["slots"]


def create_slot_from_auth(
    auth_path: str | None = None,
    *,
    label: str = "",
    chrome_profile: str = "",
    chrome_display_name: str = "",
    slot_id: str | None = None,
    activate: bool = False,
) -> dict[str, Any]:
    src = auth_path or get_mimo_auth_path()
    if not os.path.isfile(src):
        raise FileNotFoundError(f"auth snapshot source missing: {src}")

    auth_dict = _read_auth_dict(src)
    xiaomi = auth_dict.get("xiaomi")
    if not xiaomi or not xiaomi.get("key"):
        raise ValueError("auth.json has no xiaomi API key block")

    meta = extract_xiaomi_meta(auth_dict)
    slot_id = slot_id or _new_slot_id()
    filename = _slot_filename(slot_id)
    accounts_dir = _ensure_accounts_dir()
    dest = os.path.join(accounts_dir, filename)
    shutil.copy2(src, dest)

    manifest = _load_manifest_raw()
    entry = {
        "id": slot_id,
        "label": label or chrome_display_name or meta["uid"] or slot_id,
        "chrome_profile": chrome_profile,
        "chrome_display_name": chrome_display_name,
        "xiaomi_uid": meta["uid"],
        "saved_at": _utc_now_iso(),
        "file": filename,
    }
    manifest["slots"] = [s for s in manifest["slots"] if s["id"] != slot_id]
    manifest["slots"].append(entry)
    _save_manifest(manifest)

    if activate:
        activate_slot(slot_id)

    return {"slot_id": slot_id, "file": filename, "label": entry["label"], "xiaomi_uid": meta["uid"]}


def activate_slot(slot_id: str) -> str:
    manifest = _load_manifest_raw()
    entry = next((s for s in manifest["slots"] if s["id"] == slot_id), None)
    if not entry:
        raise KeyError(f"slot not found: {slot_id}")

    src = os.path.join(get_mimo_accounts_dir(), entry["file"])
    if not os.path.isfile(src):
        raise FileNotFoundError(f"slot file missing: {src}")

    auth_path = get_mimo_auth_path()
    os.makedirs(os.path.dirname(auth_path), exist_ok=True)
    shutil.copy2(src, auth_path)
    manifest["active_slot_id"] = slot_id
    _save_manifest(manifest)
    return auth_path


def delete_slot(slot_id: str) -> bool:
    manifest = _load_manifest_raw()
    entry = next((s for s in manifest["slots"] if s["id"] == slot_id), None)
    if not entry:
        raise KeyError(f"slot not found: {slot_id}")

    slot_file = os.path.join(get_mimo_accounts_dir(), entry["file"])
    if os.path.isfile(slot_file):
        os.remove(slot_file)

    manifest["slots"] = [s for s in manifest["slots"] if s["id"] != slot_id]
    if manifest.get("active_slot_id") == slot_id:
        manifest["active_slot_id"] = manifest["slots"][-1]["id"] if manifest["slots"] else None
    _save_manifest(manifest)
    return True


def rename_slot(slot_id: str, label: str) -> dict[str, Any]:
    manifest = _load_manifest_raw()
    entry = next((s for s in manifest["slots"] if s["id"] == slot_id), None)
    if not entry:
        raise KeyError(f"slot not found: {slot_id}")
    entry["label"] = label.strip() or entry["label"]
    _save_manifest(manifest)
    return entry


def backup_active_auth_to_slot(label: str | None = None) -> dict[str, Any] | None:
    """Snapshot active auth.json into a new slot before reset."""
    auth_path = get_mimo_auth_path()
    if not os.path.isfile(auth_path):
        return None
    auth_dict = _read_auth_dict(auth_path)
    if not auth_dict.get("xiaomi", {}).get("key"):
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    auto_label = label or f"auto-backup-before-reset-{ts}"
    return create_slot_from_auth(auth_path, label=auto_label, activate=False)


def has_xiaomi_auth(auth_path: str | None = None) -> bool:
    auth_dict = _read_auth_dict(auth_path)
    return bool(auth_dict.get("xiaomi", {}).get("key"))


def run_manage_accounts(translator=None) -> None:
    """Interactive menu: list / activate / delete / rename slots."""
    print(f"\n{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_slots.title', 'Manage MiMo Account Slots')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")

    while True:
        data = list_slots()
        slots = data["slots"]
        if not slots:
            print(f"{Fore.YELLOW}{EMOJI['INFO']} {_msg(translator, 'mimo_slots.empty', 'No saved slots yet. Use menu 6 to login.')}{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{_msg(translator, 'mimo_slots.list_header', 'Saved accounts ({count}):', count=len(slots))}{Style.RESET_ALL}")
        for i, s in enumerate(slots, 1):
            active = f" {Fore.GREEN}*{_msg(translator, 'mimo_slots.active', 'active')}{Style.RESET_ALL}" if s["active"] else ""
            print(
                f"  {Fore.GREEN}{i}{Style.RESET_ALL}. {s['label']} "
                f"({s['chrome_profile'] or '—'}) uid={s['xiaomi_uid'] or '—'} key={s['key_prefix']}{active}"
            )

        print(f"\n{Fore.CYAN}a{_msg(translator, 'mimo_slots.activate', '. Activate')}  "
              f"d{_msg(translator, 'mimo_slots.delete', '. Delete')}  "
              f"r{_msg(translator, 'mimo_slots.rename', '. Rename')}  "
              f"0{_msg(translator, 'mimo_slots.back', '. Back')}{Style.RESET_ALL}")
        choice = input(f"{EMOJI['INFO']} {_msg(translator, 'menu.input_choice', 'Please enter your choice ({choices})', choices='0/a/d/r')}: ").strip().lower()
        if choice == "0":
            return
        if choice not in ("a", "d", "r"):
            print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'menu.invalid_choice', 'Invalid selection. Please enter a number from {choices}', choices='0/a/d/r')}{Style.RESET_ALL}")
            continue

        try:
            idx = int(input(f"{EMOJI['INFO']} {_msg(translator, 'mimo_slots.pick', 'Slot number')}: ").strip())
        except ValueError:
            print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'mimo_slots.invalid', 'Invalid slot number')}{Style.RESET_ALL}")
            continue
        if idx < 1 or idx > len(slots):
            print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'mimo_slots.invalid', 'Invalid slot number')}{Style.RESET_ALL}")
            continue

        slot = slots[idx - 1]
        try:
            if choice == "a":
                path = activate_slot(slot["id"])
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_slots.activated', 'Activated → {path}', path=path)}{Style.RESET_ALL}")
            elif choice == "d":
                confirm = input(f"{Fore.YELLOW}{_msg(translator, 'mimo_slots.delete_confirm', 'Delete {label}? (y/N)', label=slot['label'])} {Style.RESET_ALL}").lower()
                if confirm == "y":
                    delete_slot(slot["id"])
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_slots.deleted', 'Slot deleted')}{Style.RESET_ALL}")
            elif choice == "r":
                new_label = input(f"{EMOJI['INFO']} {_msg(translator, 'mimo_slots.new_label', 'New label')}: ").strip()
                if new_label:
                    rename_slot(slot["id"], new_label)
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_slots.renamed', 'Label updated')}{Style.RESET_ALL}")
        except Exception as exc:
            print(f"{Fore.RED}{EMOJI['ERROR']} {exc}{Style.RESET_ALL}")
