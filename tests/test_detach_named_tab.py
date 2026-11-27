import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch


def load_kitten():
    boss_module = ModuleType("kitty.boss")
    boss_module.Boss = object
    handler_module = ModuleType("kittens.tui.handler")
    handler_module.result_handler = lambda **kwargs: lambda handler: handler
    spec = importlib.util.spec_from_file_location(
        "detach_named_tab", Path(__file__).resolve().parents[1] / "detach_named_tab.py"
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        sys.modules,
        {"kitty.boss": boss_module, "kittens.tui.handler": handler_module},
    ):
        spec.loader.exec_module(module)
    return module


kitten = load_kitten()


class DetachNamedTabTests(unittest.TestCase):
    def setUp(self):
        self.source_tab = Mock(id=1)
        self.new_tab = Mock(id=2)
        self.window = Mock(id=28, cwd_of_child="/work/my project")
        self.window.tabref.return_value = self.source_tab
        self.boss = Mock(window_id_map={28: self.window})
        self.boss.tab_for_id.return_value = self.new_tab

        def detach(*args):
            self.window.tabref.return_value = self.new_tab

        self.boss.call_remote_control.side_effect = detach

    def run_kitten(self):
        kitten.handle_result(["detach_named_tab.py"], "", 28, self.boss)

    def test_detaches_target_before_prompting_with_cwd_basename(self):
        self.run_kitten()
        self.boss.call_remote_control.assert_called_once_with(
            self.window, ("detach-window", "--self", "--target-tab=new")
        )
        self.assertEqual(
            [call[0] for call in self.boss.mock_calls],
            ["call_remote_control", "get_line"],
        )
        prompt = self.boss.get_line.call_args
        self.assertIs(prompt.kwargs["window"], self.window)
        self.assertEqual(prompt.kwargs["initial_value"], "my project")
        self.assertEqual(prompt.kwargs["prompt"], "Tab name: ")
        self.boss.call_remote_control.assert_called_once()

    def test_suggestion_handles_root_trailing_slash_and_unknown_cwd(self):
        for cwd, expected in [
            ("/", "/"),
            ("/work/project/", "project"),
            ("/work/日本語", "日本語"),
            (None, ""),
            ("", ""),
        ]:
            with self.subTest(cwd=cwd):
                self.window.cwd_of_child = cwd
                self.run_kitten()
                self.assertEqual(
                    self.boss.get_line.call_args.kwargs["initial_value"], expected
                )

    def test_accepted_title_targets_new_tab_even_after_focus_changes(self):
        self.run_kitten()
        callback = self.boss.get_line.call_args.args[1]
        self.window.tabref.return_value = self.source_tab
        callback("  Custom name  ")
        self.boss.tab_for_id.assert_called_once_with(2)
        self.new_tab.set_title.assert_called_once_with("Custom name")
        self.source_tab.set_title.assert_not_called()

    def test_cancelling_keeps_detached_tab_with_automatic_title(self):
        self.run_kitten()
        self.boss.get_line.call_args.args[1]("")
        self.new_tab.set_title.assert_called_once_with("")
        self.boss.call_remote_control.assert_called_once()

    def test_closed_target_tab_is_ignored_on_submit(self):
        self.run_kitten()
        self.boss.tab_for_id.return_value = None
        self.boss.get_line.call_args.args[1]("name")
        self.new_tab.set_title.assert_not_called()

    def test_missing_source_window_is_ignored(self):
        self.boss.window_id_map.clear()
        self.run_kitten()
        self.boss.call_remote_control.assert_not_called()
        self.boss.get_line.assert_not_called()

    def test_disappearing_tab_does_not_open_prompt(self):
        self.boss.call_remote_control.side_effect = lambda *args: setattr(
            self.window.tabref, "return_value", None
        )
        self.run_kitten()
        self.boss.get_line.assert_not_called()


if __name__ == "__main__":
    unittest.main()
