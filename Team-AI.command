#!/bin/bash
# Team launcher for Mac: double-click to open the team folder.
# Installs what is needed the first time, then prepares this computer.
cd "$(dirname "$0")" || exit 1
echo "Opening your team folder..."

finish() { echo; read -r -p "Press Enter to close this window." _; exit "$1"; }

# Git: comes with Apple's developer tools.
if ! git --version >/dev/null 2>&1; then
  echo "Your computer needs Apple's developer tools (they include git, used to keep the team folder in sync)."
  read -r -p "Install them now? [y/n] " answer
  if [[ "$answer" =~ ^[yYsS] ]]; then
    xcode-select --install
    echo "Follow the installation window. When it finishes, open this file again."
  fi
  finish 1
fi

# uv: installs and runs the right Python. Installed automatically the first time.
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing the tools your team folder needs (one time only)..."
  if ! curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; then
    echo "The installation failed. Check your internet connection and try again, or ask your AI Champion."
    finish 1
  fi
fi
uv python install 3.12 --quiet >/dev/null 2>&1

uv run --quiet --no-project --python 3.12 .agents/core/facade/setup.py
finish $?
