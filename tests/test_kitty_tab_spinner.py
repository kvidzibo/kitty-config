import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


class Tab(list):
    __hash__ = object.__hash__


class IndicatorTest(unittest.TestCase):
    def test_working_unread_focus_and_active_expiry(self):
        window = SimpleNamespace(progress=SimpleNamespace(state=None), title="shell", user_vars={})
        tab = Tab([window])
        manager = SimpleNamespace(active_tab=None)
        tab.tab_manager_ref = lambda: manager
        dirty = []
        tab.mark_tab_bar_dirty = lambda: dirty.append(True)
        boss = SimpleNamespace(tab_for_id=lambda _: tab)
        timers = []
        native = ModuleType("kitty.fast_data_types")
        native.get_boss = lambda: boss
        native.add_timer = lambda *args: timers.append(args)
        progress = ModuleType("kitty.progress")
        progress.ProgressState = SimpleNamespace(indeterminate=object())
        with patch.dict(sys.modules, {"kitty": ModuleType("kitty"),
                                     "kitty.fast_data_types": native,
                                     "kitty.progress": progress}):
            spec = importlib.util.spec_from_file_location(
                "indicator", Path(__file__).resolve().parents[1] / "kitty_tab_spinner.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        fg = SimpleNamespace(_704400="", _e5c07b="", _234d20="", _98c379="", _e06c75="", _c678dd="", _5c6370="", tab="")
        data = {"tab_id": 1, "fmt": SimpleNamespace(fg=fg)}
        with patch.object(module, "monotonic", return_value=10) as clock:
            self.assertEqual(module.draw_title(data), "  ")
            window.progress.state = progress.ProgressState.indeterminate
            # Eight pie frames a second, in order, each followed by one space.
            for step in range(8):
                clock.return_value = 10 + step / 8
                self.assertEqual(module.draw_title(data), chr(0xF0A9E + step) + " ")
            window.progress.state = None
            self.assertEqual(module.draw_title(data), "\U000f0e1e ")
            clock.return_value = 100
            self.assertEqual(module.draw_title(data), "\U000f0e1e ")
            manager.active_tab = tab
            self.assertEqual(module.draw_title(data), "  ")
            window.progress.state = progress.ProgressState.indeterminate
            module.draw_title(data)
            window.progress.state = None
            self.assertEqual(module.draw_title(data), "\U000f0e1e ")
            clock.return_value = 103
            timers[-1][0](1)
            self.assertEqual(dirty, [True])
            self.assertEqual(module.draw_title(data), "  ")
            # A new run must not be cleared by a previous completion timer.
            window.progress.state = progress.ProgressState.indeterminate
            self.assertIn(module.draw_title(data)[0], module.FRAMES)
            timers[-1][0](1)
            self.assertIn(module.draw_title(data)[0], module.FRAMES)
            # Codex's native title drives the same indicator without progress OSCs.
            window.progress.state = None
            manager.active_tab = None
            for frame in "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏":
                window.title = f"codex {frame} Working | project"
                self.assertIn(module.draw_title(data)[0], module.FRAMES)
            window.title = "codex | Ready | project"
            self.assertEqual(module.draw_title(data), "\U000f0e1e ")
            manager.active_tab = tab
            self.assertEqual(module.draw_title(data), "  ")
            window.title = "other app ⠋ Working | project"
            self.assertEqual(module.draw_title(data), "  ")
            # Pinote PR status fills the idle slot; work wins, and PR status outranks unread completion.
            window.title = "shell"
            other = SimpleNamespace(progress=SimpleNamespace(state=None), title="shell",
                                    user_vars={"pinote_pr": "passing"})
            tab.append(other)
            fg._e06c75, fg._c678dd = "<red>", "<purple>"
            self.assertEqual(module.draw_title(data), "\U000f02a2 ")
            window.user_vars["pinote_pr"] = "failing"
            self.assertEqual(module.draw_title(data), "<red>\U000f02a2 ")
            window.user_vars["pinote_pr"] = "bogus"
            other.user_vars["pinote_pr"] = "merged"
            self.assertEqual(module.draw_title(data), "<purple>\U000f02a2 ")
            window.progress.state = progress.ProgressState.indeterminate
            self.assertIn(module.draw_title(data)[0], module.FRAMES)
            window.progress.state = None
            manager.active_tab = None
            self.assertEqual(module.draw_title(data), "<purple>\U000f02a2 ")
            # The hidden unread check reappears once the PR status is gone, until the tab is visited.
            saved = dict(other.user_vars)
            other.user_vars.clear()
            self.assertEqual(module.draw_title(data), "\U000f0e1e ")
            other.user_vars.update(saved)
            manager.active_tab = tab
            self.assertEqual(module.draw_title(data), "<purple>\U000f02a2 ")
            other.user_vars.clear()
            self.assertEqual(module.draw_title(data), "  ")
            other.user_vars.update(saved)
            # As a global watcher, only PR status changes redraw the tab bar.
            dirty.clear()
            window.tabref = lambda: tab
            module.on_set_user_var(boss, window, {"key": "pinote_task", "value": "7"})
            module.on_set_user_var(boss, window, {"key": "pinote_pr", "value": None})
            self.assertEqual(dirty, [True])
            # All states share one icon; colour and priority tell them apart.
            fg._e5c07b, fg._98c379 = "<amber>", "<green>"
            window.user_vars["pinote_pr"] = "passing"
            other.user_vars["pinote_pr"] = "pending"
            self.assertEqual(module.draw_title(data), "<amber>\U000f02a2 ")
            other.user_vars.clear()
            self.assertEqual(module.draw_title(data), "<green>\U000f02a2 ")
            # Grey without a current status or when closed; any coloured state outranks it.
            fg._5c6370 = "<grey>"
            fg._c678dd = "<purple>"
            window.user_vars["pinote_pr"] = "merged"
            for state in ("unknown", "closed"):
                other.user_vars["pinote_pr"] = state
                self.assertEqual(module.draw_title(data), "<purple>\U000f02a2 ")
                del window.user_vars["pinote_pr"]
                self.assertEqual(module.draw_title(data), "<grey>\U000f02a2 ")
                window.user_vars["pinote_pr"] = "merged"


if __name__ == "__main__":
    unittest.main()
