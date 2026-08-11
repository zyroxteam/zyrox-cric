#!/usr/bin/env bash
# ZYROX CRICBUZZ — installer (Termux / Linux / macOS)
set -e
echo "==> Installing zyrox-cric..."
python3 -c "import sys; assert sys.version_info >= (3,8), 'Python 3.8+ chahiye'" 2>/dev/null || { echo "Python 3.8+ install karo:  pkg install python  (Termux)"; exit 1; }
mkdir -p "$HOME/.local/bin"
cp zyrox-cric.py "$HOME/.local/bin/zyrox-cric"
chmod +x "$HOME/.local/bin/zyrox-cric"
if command -v zyrox-cric >/dev/null 2>&1; then
    echo "==> Installed! Command:  zyrox-cric live"
else
    echo "==> Installed at ~/.local/bin/zyrox-cric"
    echo "    PATH me add karo:  export PATH=\$PATH:\$HOME/.local/bin"
    echo "    (ya Termux:  ln -s ~/.local/bin/zyrox-cric \$PREFIX/bin/zyrox-cric)"
fi
