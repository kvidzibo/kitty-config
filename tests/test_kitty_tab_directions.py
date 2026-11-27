import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
LEFT, TOP = 1, 2


class KittyTabDirectionTests(unittest.TestCase):
    def load(self, name, edge):
        handler = ModuleType("kittens.tui.handler")
        handler.result_handler = lambda **kwargs: lambda fn: fn
        boss = ModuleType("kitty.boss")
        boss.Boss = object
        native = ModuleType("kitty.fast_data_types")
        native.get_options = lambda: SimpleNamespace(tab_bar_edge=edge)
        tab_bar = ModuleType("kitty.tab_bar")
        tab_bar.is_vertical_edge = lambda value: value == LEFT
        spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
        kitten = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {
            "kittens.tui.handler": handler, "kitty.boss": boss,
            "kitty.fast_data_types": native, "kitty.tab_bar": tab_bar,
        }):
            spec.loader.exec_module(kitten)
        return kitten

    def run_kitten(self, name, edge, direction):
        tab = Mock()
        tab.neighboring_group_id.return_value = None
        boss = Mock(active_tab=tab, active_tab_manager=SimpleNamespace(tabs=[1, 2]))
        self.load(name, edge).handle_result([name, direction], "", 0, boss)
        return boss

    def test_edge_wrap_follows_tab_bar_axis(self):
        cases = [
            ("focus_or_tab", "previous_tab", "next_tab"),
            ("move_or_tab", "move_tab_backward", "move_tab_forward"),
        ]
        for name, previous, following in cases:
            for edge, back, forward, ignored in [
                (TOP, "left", "right", "bottom"),
                (LEFT, "top", "bottom", "right"),
            ]:
                with self.subTest(name=name, edge=edge):
                    getattr(self.run_kitten(name, edge, back), previous).assert_called_once_with()
                    getattr(self.run_kitten(name, edge, forward), following).assert_called_once_with()
                    boss = self.run_kitten(name, edge, ignored)
                    getattr(boss, previous).assert_not_called()
                    getattr(boss, following).assert_not_called()


if __name__ == "__main__":
    unittest.main()
