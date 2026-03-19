# dotfiles-zed

Configuration Zed harmonisee entre **Windows (WSL)** et **macOS**.

## Structure

```
base/
  keymap.jsonc               Keybindings multi-OS avec commentaires ← source de verite
  keymap.json                Keymap multi-OS JSON pur (genere + versionne)
  snippets/                  Python + TSX snippets (identiques partout)
macos/
  settings.json              Settings macOS complets, copiable directement
  keymap.json                Keymap standalone macOS (genere + versionne)
windows/
  settings.json              Settings Windows complets, copiable directement
  keymap.json                Keymap standalone Windows (genere + versionne)
tmux/.tmux.conf              Config tmux portable
install.py                   Script de deploiement
```

## Prerequis

- **uv** ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **JetBrainsMono Nerd Font** installee sur la machine

### Installer la police

**macOS :**
```bash
brew install --cask font-jetbrains-mono-nerd-font
```

**Windows :**
Telecharger depuis https://www.nerdfonts.com/font-downloads (JetBrainsMono) et installer via le panneau de configuration des polices.

### Installer tmux (si besoin)

**macOS :**
```bash
brew install tmux
```

**Windows (WSL/Ubuntu) :**
```bash
sudo apt install tmux
```

## Usage

### Deployer la config

```bash
# Auto-detecte l'OS et deploie tout
uv run install.py

# Dry run (voir ce qui serait fait sans ecrire)
uv run install.py --dry

# Forcer un OS specifique (utile depuis WSL)
uv run install.py --os windows
uv run install.py --os macos

# Regenerer uniquement les keymaps (apres modif de base/keymap.jsonc)
uv run install.py --build-keymaps
```

Le script :
1. Detecte l'OS (gere le cas WSL automatiquement)
2. Copie `macos/settings.json` ou `windows/settings.json` vers le dossier Zed
3. Copie `macos/keymap.json` ou `windows/keymap.json` vers le dossier Zed
4. Copie les snippets vers le dossier Zed
5. Symlink `.tmux.conf` vers `~/.tmux.conf`

### Apres un changement de settings

**Toujours editer depuis le repo**, jamais depuis Zed directement — les fichiers deployes seront ecrases au prochain `install.py`.

1. Modifier `macos/settings.json` ou `windows/settings.json`
2. `uv run install.py`
3. Redemarrer Zed

### Apres un changement de keybindings

1. Modifier `base/keymap.jsonc`
2. `uv run install.py --build-keymaps` (regenere les keymaps dans `base/`, `macos/`, `windows/`)
3. `uv run install.py`
4. Redemarrer Zed

### Ajouter un nouveau snippet

Ajouter le fichier `.json` dans `base/snippets/`, puis relancer `install.py`.

## Keybindings

| Action                  | Windows              | macOS              |
|-------------------------|----------------------|--------------------|
| Focus terminal          | `Ctrl+Alt+T`        | `Cmd+Alt+T`       |
| Rename symbol           | `Ctrl+Shift+R`      | `Cmd+Shift+R`     |
| Go to bracket           | `Ctrl+Shift+>`      | `Cmd+Shift+>`     |
| Find all references     | `Shift+F12`         | `Shift+F12`       |
| Go to implementation    | `Ctrl+F12`          | `Ctrl+F12`        |
| Go to type definition   | `Ctrl+Shift+F12`    | `Ctrl+Shift+F12`  |
| Go to declaration       | `Alt+Ctrl+F12`      | `Alt+Ctrl+F12`    |
| Focus pane left/right   | `Ctrl+Alt+←/→`      | `Cmd+Alt+←/→`     |

Les keymaps standalone (copiables sans script) sont dans `macos/keymap.json` et `windows/keymap.json`.

## Notes

- `base/keymap.jsonc` est la source de verite pour les keybindings — contient les commentaires et les conditions `os == macos` / `os == windows`
- `base/keymap.json`, `macos/keymap.json`, `windows/keymap.json` sont **generes par `--build-keymaps`** — ne pas les editer directement
- Les snippets utilisent le prefixe `z` (ex: `zmain`, `zdc`) pour eviter les collisions avec l'autocompletion
- `macos/settings.json` et `windows/settings.json` sont des fichiers complets copiables directement — Zed accepte les commentaires dans `settings.json`
