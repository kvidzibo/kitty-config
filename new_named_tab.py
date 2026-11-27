from kitty.boss import Boss
from kittens.tui.handler import result_handler


def main(args: list[str]) -> None:
    pass


@result_handler(no_ui=True)
def handle_result(
    args: list[str], _answer: str, target_window_id: int, boss: Boss
) -> None:
    source_window = boss.window_id_map.get(target_window_id)
    if source_window is None:
        return

    command = ["launch", "--type=tab"]
    if len(args) > 1 and args[1] == "current":
        command.append("--cwd=oldest")
    new_window_id = boss.call_remote_control(source_window, tuple(command))
    if new_window_id is None:
        return

    try:
        new_window = boss.window_id_map.get(int(str(new_window_id)))
    except ValueError:
        return
    if new_window is None:
        return

    tab = new_window.tabref()
    if tab is None:
        return
    tab_id = tab.id

    def set_title(title: str) -> None:
        tab = boss.tab_for_id(tab_id)
        if tab is not None:
            tab.set_title(title.strip())

    boss.get_line(
        "Enter a name for the new tab.",
        set_title,
        window=new_window,
        prompt="Tab name: ",
        window_title="Name new tab",
    )
