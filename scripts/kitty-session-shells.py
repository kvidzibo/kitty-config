"""Remove executable launches and environment overrides from Kitty snapshots."""
import json
import shlex
import sys


def sanitize(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.split(maxsplit=1)[:1] == ["launch"]:
            tokens = shlex.split(line)
            kept = ["launch"]
            # Kitty emits its layout identity first, then options, then the command.
            # Stop at the command so command arguments cannot become launch options.
            for token in tokens[1:]:
                if token.startswith("kitty-unserialize-data="):
                    data = json.loads(token.partition("=")[2])
                    kept.append("kitty-unserialize-data=" + json.dumps({"id": data["id"]}))
                elif token.startswith("--cwd="):
                    kept.append(token)
                elif token.startswith("--type="):
                    if token.partition("=")[2] in ("overlay", "overlay-main"):
                        kept.append(token)
                elif not token.startswith("--"):
                    break
            line = shlex.join(kept)
        lines.append(line)
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.stdout.write(sanitize(sys.stdin.read()))
