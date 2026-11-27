import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HELPER = Path(__file__).resolve().parents[1] / "scripts/thunar-kitty-tab.sh"


class ThunarKittyTabTests(unittest.TestCase):
    def test_folder_arguments_and_default_screen_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Folder's & $(touch INJECTED)"
            folder.mkdir()
            log = root / "commands.jsonl"
            kitty = root / "kitty"
            kitty.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\n"
                "with open(os.environ['COMMAND_LOG'], 'a') as log:\n"
                "    log.write(json.dumps([os.getcwd(), sys.argv[1:]]) + '\\n')\n"
                "if 'launch' in sys.argv:\n"
                "    print('42')\n"
            )
            kitty.chmod(0o755)
            # Simulate Kitty's :812 versus Thunar's launch-context :812.0.
            process = subprocess.Popen(["sleep", "10"], env=dict(os.environ, DISPLAY=":812"))
            try:
                pgrep = root / "pgrep"
                pgrep.write_text(f"#!/bin/sh\nprintf '%s\\n' '{process.pid}'\n")
                pgrep.chmod(0o755)
                env = dict(
                    os.environ,
                    PATH=f"{root}:{os.environ['PATH']}",
                    DISPLAY=":812.0",
                    COMMAND_LOG=str(log),
                )
                env.pop("KITTY_LISTEN_ON", None)
                subprocess.run([str(HELPER), str(folder)], env=env, check=True)
            finally:
                process.terminate()
                process.wait()

            commands = [json.loads(line) for line in log.read_text().splitlines()]
            prefix = ["@", "--to", f"unix:@mykitty-{process.pid}"]
            self.assertEqual(commands, [
                [str(folder), prefix + ["launch", "--type=tab", f"--cwd={folder}"]],
                [str(folder), prefix + [
                    "set-tab-title", "--match=window_id:42", "--", folder.name,
                ]],
                [str(folder), prefix + ["focus-window", "--match=id:42"]],
            ])
            self.assertFalse((folder / "INJECTED").exists())


if __name__ == "__main__":
    unittest.main()
