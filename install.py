#!/usr/bin/env python3
"""
Dotfiles Zed — Install script

Detecte l'OS courant et deploie tous les fichiers de config Zed au bon endroit.

Les fichiers deployes sont versionnés dans macos/ et windows/ — copiables
directement sans passer par ce script.

Usage:
    uv run install.py                  # Auto-detecte l'OS et deploie
    uv run install.py --dry            # Montre ce qui serait fait sans ecrire
    uv run install.py --os windows     # Force un OS specifique (test depuis WSL)
    uv run install.py --build-keymaps  # Regenere macos/keymap.json et windows/keymap.json
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import sys
from pathlib import Path

try:
    import json5
except ImportError:
    print("  Missing dependency: json5")
    print("  Install it with: uv add json5")
    sys.exit(1)


# ─── Constants ────────────────────────────────────────────────────────────────

REPO_DIR = Path(__file__).resolve().parent

ZED_CONFIG_PATHS: dict[str, Path] = {
    "Darwin": Path.home() / ".config" / "zed",
    "Windows": Path(os.environ.get("APPDATA", "")) / "Zed",
}

# Quand on tourne depuis WSL, le vrai dossier Zed est sur /mnt/c/
WSL_ZED_PATH = Path("/mnt/c/Users")


# ─── Helpers ──────────────────────────────────────────────────────────────────


def detect_os(force_os: str | None = None) -> str:
    """Detecte l'OS courant. Retourne 'Darwin' ou 'Windows'.

    Sur WSL (Linux sous Windows), retourne 'Windows' car Zed tourne cote Windows.
    """
    if force_os:
        mapping = {"windows": "Windows", "macos": "Darwin", "darwin": "Darwin"}
        result = mapping.get(force_os.lower())
        if not result:
            print(f"  OS inconnu : {force_os}. Utiliser 'windows' ou 'macos'.")
            sys.exit(1)
        return result

    system = platform.system()

    if system == "Linux":
        try:
            with open("/proc/version", encoding="utf-8") as f:
                version_info = f.read().lower()
            if "microsoft" in version_info or "wsl" in version_info:
                return "Windows"
        except FileNotFoundError:
            pass

    if system not in ZED_CONFIG_PATHS:
        print(f"  OS non supporte : {system}")
        sys.exit(1)

    return system


def get_zed_config_dir(os_name: str) -> Path:
    """Retourne le dossier de config Zed pour l'OS detecte."""
    if os_name == "Windows":
        if platform.system() == "Linux":
            for user_dir in WSL_ZED_PATH.iterdir():
                candidate = user_dir / "AppData" / "Roaming" / "Zed"
                if candidate.exists():
                    return candidate
            print("  Dossier Zed introuvable sous /mnt/c/Users/*/AppData/Roaming/Zed")
            print("  Verifier le point de montage WSL.")
            sys.exit(1)
        return ZED_CONFIG_PATHS["Windows"]

    return ZED_CONFIG_PATHS[os_name]


def copy_file(src: Path, dst: Path, dry: bool = False) -> None:
    """Copie un fichier en creant les dossiers parents si necessaire."""
    if dry:
        print(f"  [DRY] {src.relative_to(REPO_DIR)} -> {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  {src.relative_to(REPO_DIR)} -> {dst}")


def symlink_or_copy(src: Path, dst: Path, dry: bool = False) -> None:
    """Cree un symlink, ou copie si les symlinks ne sont pas supportes."""
    if dry:
        print(f"  [DRY] symlink {dst} -> {src}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    try:
        dst.symlink_to(src)
        print(f"  symlink {dst} -> {src}")
    except OSError:
        shutil.copy2(src, dst)
        print(f"  copie (symlink echoue) {src.name} -> {dst}")


# ─── Keymap build ─────────────────────────────────────────────────────────────


def build_keymaps(dry: bool = False) -> None:
    """Regenere les fichiers keymap a partir de base/keymap.jsonc.

    Produit trois fichiers versionnés :
    - base/keymap.json      : multi-OS, JSON pur sans commentaires
    - macos/keymap.json     : standalone macOS, sans conditions os ==
    - windows/keymap.json   : standalone Windows, sans conditions os ==
    """
    template = REPO_DIR / "base" / "keymap.jsonc"
    raw: list[dict] = json5.loads(template.read_text(encoding="utf-8"))

    # base/keymap.json — multi-OS, JSON pur
    base_dst = REPO_DIR / "base" / "keymap.json"
    content = json.dumps(raw, indent=2, ensure_ascii=False) + "\n"
    if dry:
        print(f"  [DRY] base/keymap.jsonc -> base/keymap.json")
    else:
        base_dst.write_text(content, encoding="utf-8")
        print(f"  base/keymap.jsonc -> base/keymap.json")

    # macos/keymap.json et windows/keymap.json — standalone par OS
    os_map = {
        "macos": REPO_DIR / "macos" / "keymap.json",
        "windows": REPO_DIR / "windows" / "keymap.json",
    }

    for os_key, dst in os_map.items():
        result: list[dict] = []
        other_os = "windows" if os_key == "macos" else "macos"

        for entry in raw:
            ctx: str = entry.get("context", "")

            # Ignorer les entrees qui ciblent explicitement l'autre OS
            if f"os == {other_os}" in ctx:
                continue

            # Retirer la condition os == {os_key} du contexte
            clean_ctx = re.sub(rf"\s*&&\s*os == {os_key}\b", "", ctx)
            clean_ctx = re.sub(rf"\bos == {os_key}\s*&&\s*", "", clean_ctx)
            clean_ctx = re.sub(rf"\bos == {os_key}\b", "", clean_ctx)
            clean_ctx = clean_ctx.strip()

            new_entry = dict(entry)
            if clean_ctx:
                new_entry["context"] = clean_ctx
            else:
                new_entry.pop("context", None)
            result.append(new_entry)

        os_content = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if dry:
            print(f"  [DRY] base/keymap.jsonc -> {os_key}/keymap.json")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(os_content, encoding="utf-8")
            print(f"  base/keymap.jsonc -> {os_key}/keymap.json")


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    args = sys.argv[1:]
    dry = "--dry" in args
    force_os = None

    if "--os" in args:
        idx = args.index("--os")
        if idx + 1 < len(args):
            force_os = args[idx + 1]
        else:
            print("  --os requiert un argument (windows ou macos)")
            sys.exit(1)

    # ─── --build-keymaps : regenere les keymaps et quitte ────────────────────
    if "--build-keymaps" in args:
        print("=" * 60)
        print("  Dotfiles Zed — Build keymaps")
        print("=" * 60)
        build_keymaps(dry=dry)
        print(f"{'=' * 60}")
        return

    print("=" * 60)
    print("  Dotfiles Zed — Installer")
    print("=" * 60)

    # 1. Detect OS
    os_name = detect_os(force_os)
    os_label = "macOS" if os_name == "Darwin" else "Windows"
    os_dir = REPO_DIR / ("macos" if os_name == "Darwin" else "windows")
    print(f"\n  Plateforme : {os_label}")

    # 2. Find Zed config directory
    zed_dir = get_zed_config_dir(os_name)
    print(f"  Config Zed : {zed_dir}")

    if not zed_dir.exists() and not dry:
        zed_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Cree {zed_dir}")

    # 3. Regenere les keymaps (base/keymap.json + macos/ + windows/)
    print("\n--- Keymap ---")
    build_keymaps(dry=dry)

    # 4. Deploie settings.json et keymap.json depuis le dossier OS
    print("\n--- Deploy ---")
    copy_file(os_dir / "settings.json", zed_dir / "settings.json", dry=dry)
    copy_file(os_dir / "keymap.json", zed_dir / "keymap.json", dry=dry)

    # 5. Deploy snippets
    print("\n--- Snippets ---")
    snippets_src = REPO_DIR / "base" / "snippets"
    snippets_dst = zed_dir / "snippets"
    for snippet_file in sorted(snippets_src.glob("*.json")):
        copy_file(snippet_file, snippets_dst / snippet_file.name, dry=dry)

    # 6. Deploy tmux config
    print("\n--- tmux ---")
    tmux_src = REPO_DIR / "tmux" / ".tmux.conf"
    tmux_dst = Path.home() / ".tmux.conf"
    symlink_or_copy(tmux_src, tmux_dst, dry=dry)

    # 7. Summary
    print(f"\n{'=' * 60}")
    print(f"  Termine ! Deploy pour {os_label}.")
    if dry:
        print("  (Dry run — aucun fichier ecrit)")
    else:
        print("  Redemarrer Zed pour appliquer les changements.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()