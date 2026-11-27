"""Open a clicked link without switching to a newly opened Kitty tab."""
from kittens.tui.handler import result_handler
from kitty.fast_data_types import add_timer
from kitty.open_actions import actions_for_url


def main(args: list[str]) -> None:
    pass


@result_handler(no_ui=True)
def handle_result(args, _answer, target_window_id, boss) -> None:
    window = boss.window_id_map.get(target_window_id)
    if window is None:
        return
    original = boss.open_url

    def open_url(url, program=None, cwd=None):
        def open_background(_timer_id):
            if target_window_id not in boss.window_id_map:
                return
            tab = window.tabref()
            actions = list(actions_for_url(url)) if program is None else []
            if actions:
                boss.dispatch_action(actions.pop(0), window_for_dispatch=window)
                if actions:
                    boss.drain_actions(actions, window_for_dispatch=window)
            else:
                original(url, program, cwd)
            # Keep overlays focused, but restore the source after opening a tab.
            if tab is not None and boss.active_tab is not tab:
                boss.set_active_window(window, for_keep_focus=True)

        # Capture the URL now; launch after native mouse dispatch has finished.
        add_timer(open_background, 0, False)

    boss.open_url = open_url
    try:
        window.mouse_handle_click("link")
    finally:
        boss.open_url = original
