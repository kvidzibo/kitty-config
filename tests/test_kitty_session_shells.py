import importlib.util
import json
import shlex
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "kitty-session-shells.py"
_spec = importlib.util.spec_from_file_location("kitty_session_shells", MODULE_PATH)
kitty_session_shells = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kitty_session_shells)


class KittySessionShellsTests(unittest.TestCase):
    def test_sanitize_removes_launch_shell_details(self):
        session = "\n".join(
            [
                "new_tab",
                "cd /tmp",
                "set_layout_state \"{}\"",
                "launch "
                + shlex.join(
                    [
                        'kitty-unserialize-data={"id": 2,"cmd_at_shell_startup":"pi"}',
                        "--cwd=/tmp/a b",
                        "--env=SECRET=value",
                        "--hold",
                        "node",
                        "pi",
                        "--session",
                        "path",
                    ]
                ),
                "launch " + shlex.join(["--cwd=/tmp/plain", "bash"]),
            ]
        )

        sanitized = kitty_session_shells.sanitize(session)
        lines = sanitized.splitlines()

        self.assertEqual(lines[:3], ["new_tab", "cd /tmp", 'set_layout_state "{}"'])
        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[4], "launch --cwd=/tmp/plain")

        tokens = shlex.split(lines[3])
        self.assertEqual(tokens[0], "launch")
        self.assertEqual(tokens[2], "--cwd=/tmp/a b")
        self.assertEqual(len(tokens), 3)
        metadata_key, metadata_value = tokens[1].split("=", 1)
        self.assertEqual(metadata_key, "kitty-unserialize-data")
        metadata = json.loads(metadata_value)
        self.assertEqual(metadata["id"], 2)
        self.assertNotIn("cmd_at_shell_startup", metadata)


if __name__ == "__main__":
    unittest.main()
