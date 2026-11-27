#!/usr/bin/env bash
set -euo pipefail

# Forward filenames unchanged to the native Kitty preview.
mock_bin=$(mktemp -d)
trap 'rm -rf "$mock_bin"' EXIT
cat > "$mock_bin/kitty" <<'MOCK'
#!/usr/bin/env bash
[[ $# == 5 && $1 == +runpy && $3 == */scripts/kitty-image-preview.py &&
   $4 == '/tmp/an image.png' && $5 == '-another.png' ]]
MOCK
chmod +x "$mock_bin/kitty"
PATH="$mock_bin:$PATH" bash "$(dirname "${BASH_SOURCE[0]}")/../scripts/kitty-image-overlay.sh" \
    '/tmp/an image.png' '-another.png'
printf 'PASS: image preview forwards filename arguments unchanged\n'
