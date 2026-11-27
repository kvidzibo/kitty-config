import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch


class BackgroundLinkTests(unittest.TestCase):
    def test_only_new_tabs_restore_source_focus(self):
        handler = ModuleType("kittens.tui.handler")
        handler.result_handler = lambda **kwargs: lambda callback: callback
        timers = ModuleType("kitty.fast_data_types")
        timers.add_timer = Mock()
        action = SimpleNamespace(func="launch", args=())
        actions = ModuleType("kitty.open_actions")
        actions.actions_for_url = Mock(return_value=[action])
        spec = importlib.util.spec_from_file_location(
            "background_link", Path(__file__).resolve().parents[1] / "scripts/kitty-background-link.py"
        )
        kitten = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {
            "kittens.tui.handler": handler, "kitty.fast_data_types": timers,
            "kitty.open_actions": actions,
        }):
            spec.loader.exec_module(kitten)

        for mode in ("overlay", "new-tab", "source-closed"):
            with self.subTest(mode=mode):
                tab = object()
                window = Mock()
                window.tabref.return_value = tab
                boss = Mock(window_id_map={7: window}, active_tab=tab)

                original = boss.open_url
                timers.add_timer.reset_mock()

                def open_url(*args):
                    if mode == "new-tab":
                        boss.active_tab = object()

                boss.dispatch_action.side_effect = lambda *args, **kwargs: open_url()
                window.mouse_handle_click.side_effect = lambda *_: boss.open_url("file:///tmp/image.png")
                kitten.handle_result([], None, 7, boss)
                window.mouse_handle_click.assert_called_once_with("link")
                self.assertIs(boss.open_url, original)
                original.assert_not_called()
                boss.dispatch_action.assert_not_called()
                self.assertEqual(timers.add_timer.call_count, 1)
                self.assertEqual(timers.add_timer.call_args.args[1:], (0, False))
                if mode == "source-closed":
                    boss.window_id_map.clear()
                if mode == "new-tab":
                    # Focus can move between the click and its queued callback.
                    boss.active_tab = object()
                timers.add_timer.call_args.args[0](0)
                original.assert_not_called()
                if mode == "source-closed":
                    boss.dispatch_action.assert_not_called()
                else:
                    boss.dispatch_action.assert_called_once_with(action, window_for_dispatch=window)
                if mode == "new-tab":
                    boss.set_active_window.assert_called_once_with(window, for_keep_focus=True)
                else:
                    boss.set_active_window.assert_not_called()


if __name__ == "__main__":
    unittest.main()
