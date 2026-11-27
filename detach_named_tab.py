import os

from kitty.boss import Boss
from kittens.tui.handler import result_handler


def main(args: list[str]) -> None:
    pass


@result_handler(no_ui=True)
def handle_result(
    args: list[str], _answer: str, target_window_id: int, boss: Boss
) -> None:
    window = boss.window_id_map.get(target_window_id)
    if window is None:
        return

    cwd = window.cwd_of_child
    suggested_name = (os.path.basename(os.path.normpath(cwd)) or os.path.sep) if cwd else ""
    boss.call_remote_control(window, ("detach-window", "--self", "--target-tab=new"))

    tab = window.tabref()
    if tab is None:
        return
    tab_id = tab.id

    def set_title(title: str) -> None:
        tab = boss.tab_for_id(tab_id)
        if tab is not None:
            tab.set_title(title.strip())

    boss.get_line(
        "Enter a name for the detached pane's tab.",
        set_title,
        window=window,
        initial_value=suggested_name,
        prompt="Tab name: ",
        window_title="Name detached tab",
    )
