#!/bin/sh
# Install the local pre-push spoiler scan.
# Usage: PYTHON=~/venvs/pbw-romance/bin/python scripts/install_hooks.sh /path/to/private/spoiler_terms.txt
set -e
terms=$(realpath "$1")
py=${PYTHON:-$(command -v python3)}
hook="$(git rev-parse --git-path hooks)/pre-push"
cat > "$hook" <<HOOK
#!/bin/sh
exec "$py" -m pbw_romance spoilers --terms "$terms" --repo "\$(git rev-parse --show-toplevel)"
HOOK
chmod +x "$hook"
echo "installed $hook"
