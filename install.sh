#!/usr/bin/env bash
# Install system and Python dependencies for Cairo/Pango text demo.
# Tested on macOS (Intel & Apple Silicon) with Homebrew.
set -euo pipefail

# Install Homebrew if missing
if ! command -v brew >/dev/null; then
  echo "Homebrew not found. Please install Homebrew (https://brew.sh) first." >&2
  exit 1
fi

# Homebrew packages
BREW_PKGS=(pygobject3 py3cairo gobject-introspection)

echo "==> Installing Homebrew packages: ${BREW_PKGS[*]}"
brew install "${BREW_PKGS[@]}"

echo "==> Installing Python packages from requirements.txt"
python3 -m pip install -U pip
python3 -m pip install -r "$(dirname "$0")/requirements.txt"

echo "All dependencies installed. Run pango_feature_demos.py to generate images."
