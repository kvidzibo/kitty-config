import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, Mock, patch


class ImageWindowTests(unittest.TestCase):
    def test_reuses_only_marked_image_only_windows(self):
        handler = ModuleType("kittens.tui.handler")
        handler.result_handler = lambda **kwargs: lambda callback: callback
        launcher = ModuleType("kitty.launch")
        launcher.launch = Mock()
        launcher.parse_launch_args = Mock()
        timers = ModuleType("kitty.fast_data_types")
        timers.add_timer = Mock()
        actions = ModuleType("kitty.open_actions")
        actions.actions_for_url = Mock(return_value=[SimpleNamespace(func="launch", args=())])
        path = Path(__file__).resolve().parents[1] / "scripts/kitty-image-window.py"
        namespace = {"__name__": "kitten"}
        with patch.dict(sys.modules, {
            "kittens.tui.handler": handler, "kitty.launch": launcher, "kitty.open_actions": actions,
            "kitty.fast_data_types": timers,
        }):
            # Kitty's no-UI loader executes kittens without defining __file__.
            exec(compile(path.read_text(), str(path), "exec"), namespace)
        kitten = SimpleNamespace(**namespace)
        args = [str(path)]

        for mode in ("new", "reuse", "mixed", "ordinary", "markdown", "diff", "other-link", "source-closed", "error"):
            with self.subTest(mode=mode):
                source = Mock()
                original = Mock()
                boss = Mock(window_id_map={7: source}, open_url=original, os_window_map={})
                target = [SimpleNamespace(user_vars={"kitty_image_preview": "1"})]
                if mode == "mixed":
                    target.append(SimpleNamespace(user_vars={}))
                manager = MagicMock(wm_class="kitty" if mode == "ordinary" else kitten.IMAGE_CLASS)
                manager.active_tab = target
                manager.__iter__.side_effect = lambda: iter([target])
                if mode != "new":
                    boss.os_window_map[1] = manager
                opts = SimpleNamespace(type="tab", var=[])
                command = ["kitty-image-overlay.sh", "/tmp/an image.png"]
                if mode == "markdown":
                    command = ["kitty-text-preview.sh", "--markdown", "/tmp/a note.md"]
                if mode == "diff":
                    command = ["kitty-text-preview.sh", "/tmp/review.diff.ansi"]
                if mode == "other-link":
                    command = ["less", "note.txt"]
                launcher.parse_launch_args.return_value = (opts, command)
                launcher.launch.reset_mock()
                timers.add_timer.reset_mock()
                launcher.launch.side_effect = RuntimeError("failed") if mode == "error" else None
                source.mouse_handle_click.side_effect = lambda *_: boss.open_url("file:///tmp/a%20note.md" if mode == "markdown" else "file:///tmp/an%20image.png")
                kitten.handle_result(args, None, 7, boss)
                self.assertIs(boss.open_url, original)
                launcher.launch.assert_not_called()
                original.assert_not_called()
                boss.dispatch_action.assert_not_called()
                self.assertEqual(timers.add_timer.call_count, 1)
                self.assertEqual(timers.add_timer.call_args.args[1:], (0, False))
                callback = timers.add_timer.call_args.args[0]
                boss.active_tab = object()  # Focus moved after the click.
                if mode == "error":
                    with self.assertRaises(RuntimeError):
                        callback(0)
                elif mode == "source-closed":
                    boss.window_id_map.clear()
                    callback(0)
                    launcher.launch.assert_not_called()
                    original.assert_not_called()
                else:
                    callback(0)
                    if mode == "other-link":
                        launcher.launch.assert_not_called()
                        original.assert_not_called()
                        boss.dispatch_action.assert_called_once_with(
                            actions.actions_for_url.return_value[0], window_for_dispatch=source,
                        )
                    else:
                        reuse = mode in ("reuse", "markdown", "diff")
                        self.assertEqual(opts.type, "tab" if reuse else "os-window")
                        launcher.launch.assert_called_once_with(
                            boss, opts, command, target_tab=target if reuse else None,
                        )
                        self.assertEqual(opts.var, ["kitty_image_preview=1"])
                        self.assertEqual(opts.source_window, "id:7")
                        boss.set_active_window.assert_called_once_with(
                            launcher.launch.return_value, switch_os_window_if_needed=True,
                        )
                self.assertIs(boss.open_url, original)


if __name__ == "__main__":
    unittest.main()
