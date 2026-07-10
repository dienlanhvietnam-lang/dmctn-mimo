"""Paths for MiMo local context vault (memory / DB / storage snapshots)."""
from __future__ import annotations

import os

import mimo_paths
import utils

MANIFEST_VERSION = 1
CONTEXT_DIR_NAME = "context"
MANIFEST_NAME = "context_manifest.json"
BUNDLES_DIR_NAME = "bundles"

# Directory names under mimocode data dir that hold conversation / session context
CONTEXT_DIR_NAMES = ("memory", "storage", "snapshot")


def get_context_vault_dir() -> str:
    """Vault root under Documents/.dmctn-mimo/context/ (outside mimocode wipe targets)."""
    return os.path.join(utils.get_app_config_dir(), CONTEXT_DIR_NAME)


def get_context_manifest_path() -> str:
    return os.path.join(get_context_vault_dir(), MANIFEST_NAME)


def get_context_bundles_dir() -> str:
    return os.path.join(get_context_vault_dir(), BUNDLES_DIR_NAME)


def get_context_bundle_paths() -> list[str]:
    """Absolute paths to snapshot for local context (dirs + DB files)."""
    data_dir = mimo_paths.get_mimo_data_dir()
    paths: list[str] = []
    for name in CONTEXT_DIR_NAMES:
        paths.append(os.path.join(data_dir, name))
    paths.extend(mimo_paths.get_mimo_database_files())
    return paths


def get_dmctn_protected_paths() -> list[str]:
    """Paths owned by DMCTN that must never appear in MiMo wipe lists."""
    return [get_context_vault_dir()]
