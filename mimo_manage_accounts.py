"""Manage MiMo Pro account slots (list, activate, rename, delete)."""
from __future__ import annotations

from colorama import Fore, Style, init

from chrome_profile import EMOJI
from mimo_account_slots import (
    activate_slot,
    delete_slot,
    list_slot_entries,
    load_manifest,
    rename_slot,
)

init()


def _msg(translator, key, fallback, **kwargs):
    if translator:
        try:
            return translator.get(key, **kwargs)
        except Exception:
            pass
    return fallback.format(**kwargs) if kwargs else fallback


def _print_slots(translator=None) -> None:
    slots = list_slot_entries()
    active = load_manifest().get("active_slot_id")
    if not slots:
        print(f"{Fore.YELLOW}{EMOJI['INFO']} {_msg(translator, 'mimo_slots.empty', 'No saved MiMo accounts')}{Style.RESET_ALL}")
        return
    print(f"\n{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}")
    for i, slot in enumerate(slots, 1):
        mark = f"{Fore.GREEN}*{Style.RESET_ALL}" if slot.get("id") == active else " "
        print(
            f"{mark} {i}. {slot.get('label')} | uid={slot.get('xiaomi_uid')} | "
            f"profile={slot.get('chrome_profile')} | key={slot.get('key_prefix')} | id={slot.get('id')}"
        )
    print(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}")


def manage_mimo_accounts(translator=None) -> None:
    while True:
        print(f"\n{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{EMOJI['INFO']} {_msg(translator, 'mimo_slots.title', 'Manage MiMo Accounts')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}1. List{Style.RESET_ALL}")
        print(f"{Fore.CYAN}2. Activate{Style.RESET_ALL}")
        print(f"{Fore.CYAN}3. Rename{Style.RESET_ALL}")
        print(f"{Fore.CYAN}4. Delete{Style.RESET_ALL}")
        print(f"{Fore.CYAN}0. Back{Style.RESET_ALL}")

        choice = input(f"\n{Fore.CYAN}{_msg(translator, 'menu.input_choice', 'Choice ({choices})', choices='0-4')}: {Style.RESET_ALL}").strip()
        if choice == "0":
            return
        if choice == "1":
            _print_slots(translator)
            continue

        slots = list_slot_entries()
        if not slots:
            print(f"{Fore.YELLOW}{EMOJI['INFO']} {_msg(translator, 'mimo_slots.empty', 'No saved MiMo accounts')}{Style.RESET_ALL}")
            continue

        _print_slots(translator)
        idx_raw = input(f"{Fore.CYAN}Slot number: {Style.RESET_ALL}").strip()
        try:
            idx = int(idx_raw) - 1
            slot = slots[idx]
        except (ValueError, IndexError):
            print(f"{Fore.RED}{EMOJI['ERROR']} Invalid slot{Style.RESET_ALL}")
            continue

        slot_id = slot["id"]
        try:
            if choice == "2":
                activate_slot(slot_id)
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Activated {slot.get('label')}{Style.RESET_ALL}")
            elif choice == "3":
                label = input(f"{Fore.CYAN}New label: {Style.RESET_ALL}").strip()
                if label:
                    rename_slot(slot_id, label)
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Renamed{Style.RESET_ALL}")
            elif choice == "4":
                confirm = input(f"{Fore.YELLOW}Delete {slot.get('label')}? (y/N): {Style.RESET_ALL}").lower()
                if confirm == "y":
                    delete_slot(slot_id)
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Deleted{Style.RESET_ALL}")
        except Exception as exc:
            print(f"{Fore.RED}{EMOJI['ERROR']} {exc}{Style.RESET_ALL}")


def run(translator=None):
    manage_mimo_accounts(translator)
    input(f"{EMOJI['INFO']} {_msg(translator, 'reset.press_enter', 'Press Enter to continue...')}")


if __name__ == "__main__":
    run()
