import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import sys
import unittest
from unittest.mock import patch


class KittySessionWatcherTests(unittest.TestCase):
    def test_saves_settled_layout_but_preserves_snapshot_during_quit(self):
        timers = []
        errors = []
        with TemporaryDirectory() as directory:
            modules = {name: ModuleType(name) for name in (
                "kitty", "kitty.config", "kitty.constants", "kitty.fast_data_types", "kitty.utils"
            )}
            modules["kitty.config"].atomic_save = lambda data, path: Path(path).write_bytes(data)
            modules["kitty.constants"].config_dir = directory
            modules["kitty.fast_data_types"].add_timer = lambda fn, *args: timers.append(fn)
            modules["kitty.utils"].log_error = errors.append
            path = Path(__file__).resolve().parents[1] / "kitty/session_watcher.py"
            spec = importlib.util.spec_from_file_location("session_watcher", path)
            watcher = importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules, modules):
                spec.loader.exec_module(watcher)

            layout = ["new_tab project", "cd /tmp", "launch bash", "launch bash"]
            boss = SimpleNamespace(shutting_down=False, serialize_state_as_session=lambda path: layout)
            snapshot = Path(directory) / "main.session"
            watcher.on_close(boss, None, {})
            watcher.on_tab_bar_dirty(boss, None, {})
            self.assertEqual(len(timers), 1)
            layout.pop()  # Removal completes after the close callback.
            timers.pop()(None)
            self.assertEqual(snapshot.read_text(), "new_tab project\ncd /tmp\nlaunch\n")

            # A closed final pane must not erase the last usable layout.
            watcher.on_close(boss, None, {})
            layout.clear()
            timers.pop()(None)
            self.assertIn("launch", snapshot.read_text())

            layout[:] = ["new_tab final", "cd /tmp", "launch --env=SECRET=value bash"]
            watcher.on_resize(boss, None, {})
            watcher.on_quit(boss, None, {"confirmed": False})
            self.assertIn("project", snapshot.read_text())
            watcher.on_quit(boss, None, {"confirmed": True})
            saved = snapshot.read_text()
            self.assertEqual(saved, "new_tab final\ncd /tmp\nlaunch\n")
            layout[:] = ["new_tab teardown", "launch bash"]
            watcher.on_close(boss, None, {})
            timers.pop()(None)
            self.assertEqual(snapshot.read_text(), saved)
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
