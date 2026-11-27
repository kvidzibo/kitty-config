import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch


class TabManager:
    def __init__(self):
        self.tabs = [SimpleNamespace(id=1)]

    def handle_tab_bar_mouse(self, x, y, button, modifiers, action):
        if action == "double-click-empty":
            self.tabs.append(Mock(id=2, active_window=Mock(id=20)))


class KittyNewTabTitleWatcherTests(unittest.TestCase):
    def test_prompts_only_for_tabs_opened_from_tab_bar(self):
        tabs_module = ModuleType("kitty.tabs")
        tabs_module.TabManager = TabManager
        path = Path(__file__).resolve().parents[1] / "kitty/new_tab_title_watcher.py"
        spec = importlib.util.spec_from_file_location("new_tab_title_watcher", path)
        watcher = importlib.util.module_from_spec(spec)
        original = TabManager.handle_tab_bar_mouse
        self.addCleanup(setattr, TabManager, "handle_tab_bar_mouse", original)
        with patch.dict(sys.modules, {"kitty": ModuleType("kitty"), "kitty.tabs": tabs_module}):
            spec.loader.exec_module(watcher)

        boss = Mock()
        watcher.on_load(boss, {})
        watcher.on_load(boss, {})  # Reloading must not wrap twice.
        manager = TabManager()
        manager.handle_tab_bar_mouse(0, 0, 0, 0, "click-tab")
        boss.get_line.assert_not_called()

        manager.handle_tab_bar_mouse(0, 0, 0, 0, "double-click-empty")
        new_tab = manager.tabs[-1]
        boss.get_line.assert_called_once()
        prompt = boss.get_line.call_args
        self.assertIs(prompt.kwargs["window"], new_tab.active_window)
        self.assertEqual(prompt.kwargs["prompt"], "Tab name: ")

        boss.tab_for_id.return_value = new_tab
        prompt.args[1]("  project  ")
        boss.tab_for_id.assert_called_once_with(2)
        new_tab.set_title.assert_called_once_with("project")


if __name__ == "__main__":
    unittest.main()
