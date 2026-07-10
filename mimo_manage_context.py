"""Manage MiMo local context vault (list, create, activate/restore, rename, delete)."""
from __future__ import annotations

from colorama import Fore, Style, init

from chrome_profile import EMOJI
from mimo_context_vault import (
    activate_context_slot,
    create_context_snapshot,
    delete_context_slot,
    has_local_context,
    list_context_slots,
    rename_context_slot,
)

init()


def _msg(translator, key, fallback, **kwargs):
    if translator:
        try:
            return translator.get(key, **kwargs)
        except Exception:
            pass
    return fallback.format(**kwargs) if kwargs else fallback


def _print_slots(translator=None) -> list:
    data = list_context_slots()
    slots = data["slots"]
    if not slots:
        print(f"{Fore.YELLOW}{EMOJI['INFO']} {_msg(translator, 'mimo_context.empty', 'No context snapshots yet')}{Style.RESET_ALL}")
        return []
    print(f"\n{Fore.CYAN}{_msg(translator, 'mimo_context.list_header', 'Saved snapshots ({count}):', count=len(slots))}{Style.RESET_ALL}")
    for i, s in enumerate(slots, 1):
        active = f" {Fore.GREEN}*{_msg(translator, 'mimo_context.active', 'active')}{Style.RESET_ALL}" if s.get("active") else ""
        print(
            f"  {Fore.GREEN}{i}{Style.RESET_ALL}. {s['label']} "
            f"| {s.get('saved_at', '')} | hash={s.get('client_hash') or '—'}{active}"
        )
    return slots


def manage_context(translator=None) -> None:
    while True:
        print(f"\n{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_context.title', 'Manage Context Vault')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}1. List{Style.RESET_ALL}")
        print(f"{Fore.CYAN}2. {_msg(translator, 'mimo_context.create', 'Create snapshot now')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}3. Activate / Restore{Style.RESET_ALL}")
        print(f"{Fore.CYAN}4. Rename{Style.RESET_ALL}")
        print(f"{Fore.CYAN}5. Delete{Style.RESET_ALL}")
        print(f"{Fore.CYAN}0. Back{Style.RESET_ALL}")

        choice = input(f"\n{Fore.CYAN}{_msg(translator, 'menu.input_choice', 'Choice ({choices})', choices='0-5')}: {Style.RESET_ALL}").strip()
        if choice == "0":
            return
        if choice == "1":
            _print_slots(translator)
            continue
        if choice == "2":
            try:
                if not has_local_context():
                    print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_context.nothing_to_snapshot', 'No local context to snapshot')}{Style.RESET_ALL}")
                    continue
                label = input(f"{Fore.CYAN}{_msg(translator, 'mimo_context.new_label', 'New label')}: {Style.RESET_ALL}").strip()
                result = create_context_snapshot(label=label or "")
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_context.snapshot_ok', 'Context snapshot: {id}', id=result['slot_id'])}{Style.RESET_ALL}")
            except Exception as exc:
                print(f"{Fore.RED}{EMOJI['ERROR']} {exc}{Style.RESET_ALL}")
            continue

        slots = _print_slots(translator)
        if not slots:
            continue
        idx_raw = input(f"{Fore.CYAN}{_msg(translator, 'mimo_context.pick', 'Snapshot number')}: {Style.RESET_ALL}").strip()
        try:
            idx = int(idx_raw) - 1
            slot = slots[idx]
        except (ValueError, IndexError):
            print(f"{Fore.RED}{EMOJI['ERROR']} {_msg(translator, 'mimo_context.invalid', 'Invalid snapshot number')}{Style.RESET_ALL}")
            continue

        slot_id = slot["id"]
        try:
            if choice == "3":
                activate_context_slot(slot_id)
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_context.activated', 'Activated / restored → {id}', id=slot_id)}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}{EMOJI['WARNING']} {_msg(translator, 'mimo_context.local_only_disclaimer', 'Local context only')}{Style.RESET_ALL}")
            elif choice == "4":
                label = input(f"{Fore.CYAN}{_msg(translator, 'mimo_context.new_label', 'New label')}: {Style.RESET_ALL}").strip()
                if label:
                    rename_context_slot(slot_id, label)
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_context.renamed', 'Label updated')}{Style.RESET_ALL}")
            elif choice == "5":
                confirm = input(f"{Fore.YELLOW}{_msg(translator, 'mimo_context.delete_confirm', 'Delete {label}? (y/N)', label=slot.get('label'))} {Style.RESET_ALL}").lower()
                if confirm == "y":
                    delete_context_slot(slot_id)
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {_msg(translator, 'mimo_context.deleted', 'Snapshot deleted')}{Style.RESET_ALL}")
        except Exception as exc:
            print(f"{Fore.RED}{EMOJI['ERROR']} {exc}{Style.RESET_ALL}")


def run(translator=None):
    manage_context(translator)
    input(f"{EMOJI['INFO']} {_msg(translator, 'reset.press_enter', 'Press Enter to continue...')}")


if __name__ == "__main__":
    run()
