import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class KittyTabScrollTests(unittest.TestCase):
    def test_scroll_only_inside_the_visible_target_tab_bar(self):
        handler = ModuleType("kittens.tui.handler")
        handler.result_handler = lambda **kwargs: lambda fn: fn
        native = ModuleType("kitty.fast_data_types")
        native.is_tab_bar_visible = Mock(return_value=True)
        bounds = SimpleNamespace(left=0, top=10, right=800, bottom=30)
        native.viewport_for_window = lambda _id: (None, bounds)
        utils = ModuleType("kitty.utils")
        utils.platform_window_id = lambda id: id + 100
        spec = importlib.util.spec_from_file_location(
            "scroll_tabs", Path(__file__).resolve().parents[1] / "kitty/scroll-tabs.py",
        )
        kitten = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {
            "kittens.tui.handler": handler,
            "kitty.fast_data_types": native,
            "kitty.utils": utils,
        }):
            spec.loader.exec_module(kitten)

        other, target = Mock(os_window_id=1), Mock(os_window_id=2)
        boss = SimpleNamespace(os_window_map={1: other, 2: target})
        for xid, x, y, visible, delta, expected in [
            (102, 0, 10, True, -1, -1),
            (102, 799, 29, True, 1, 1),
            (102, 100, 9, True, 1, None),
            (102, 100, 30, True, 1, None),
            (102, 800, 20, True, 1, None),
            (102, 100, 20, False, 1, None),
            (999, 100, 20, True, 1, None),
        ]:
            with self.subTest(xid=xid, x=x, y=y, visible=visible, delta=delta):
                target.next_tab.reset_mock()
                native.is_tab_bar_visible.return_value = visible
                kitten.handle_result(
                    ["scroll-tabs.py", *map(str, (xid, x, y, delta))], "", 0, boss,
                )
                if expected is None:
                    target.next_tab.assert_not_called()
                else:
                    target.next_tab.assert_called_once_with(expected)
                other.next_tab.assert_not_called()


if __name__ == "__main__":
    unittest.main()
