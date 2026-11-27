"""Shift-click image, Markdown, and diff links into a reusable preview-only Kitty OS window."""
from kittens.tui.handler import result_handler
from kitty.fast_data_types import add_timer
from kitty.launch import launch, parse_launch_args
from kitty.open_actions import actions_for_url


IMAGE_CLASS = "kitty-image-preview"
VIEWERS = ("kitty-image-overlay.sh", "kitty-text-preview.sh")


def main(args: list[str]) -> None:
    pass


@result_handler(no_ui=True)
def handle_result(args, _answer, target_window_id, boss) -> None:
    window = boss.window_id_map.get(target_window_id)
    if window is None:
        return
    original = boss.open_url

    def open_url(url, program=None, cwd=None):
        def open_link(_timer_id):
            if target_window_id not in boss.window_id_map:
                return
            actions = list(actions_for_url(url)) if program is None else []
            opts, command = (parse_launch_args(actions[0].args)
                             if len(actions) == 1 and actions[0].func == "launch" else (None, []))
            if not command or command[0] not in VIEWERS:
                if actions:
                    boss.dispatch_action(actions.pop(0), window_for_dispatch=window)
                    if actions:
                        boss.drain_actions(actions, window_for_dispatch=window)
                else:
                    original(url, program, cwd)
                return

            target = next((
                manager.active_tab for manager in boss.os_window_map.values()
                if manager.wm_class == IMAGE_CLASS and manager.active_tab is not None
                and all(w.user_vars.get("kitty_image_preview") == "1" for tab in manager for w in tab)
            ), None)
            opts.type = "tab" if target is not None else "os-window"
            opts.source_window = f"id:{target_window_id}"
            opts.os_window_class = opts.os_window_name = IMAGE_CLASS
            opts.var.append("kitty_image_preview=1")
            preview = launch(boss, opts, command, target_tab=target)
            if preview is not None:
                boss.set_active_window(preview, switch_os_window_if_needed=True)

        # Native click dispatch retains window/tab pointers; defer all launches.
        add_timer(open_link, 0, False)

    # Capture the URL after Kitty's native hyperlink and remote-file checks.
    boss.open_url = open_url
    try:
        window.mouse_handle_click("link")
    finally:
        boss.open_url = original
