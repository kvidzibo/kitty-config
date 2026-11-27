from typing import List

from kittens.tui.handler import result_handler
from kitty.boss import Boss
from kitty.fast_data_types import get_options
from kitty.tab_bar import is_vertical_edge


def main(args: List[str]) -> None:
    pass


def tab_directions() -> tuple[str, str]:
    """Directions that map to previous/next tab, following the tab bar axis."""
    if is_vertical_edge(get_options().tab_bar_edge):
        return 'top', 'bottom'
    return 'left', 'right'


@result_handler(no_ui=True)
def handle_result(args: List[str], answer: str, target_window_id: int, boss: Boss) -> None:
    if len(args) != 2:
        return
    direction = args[1]
    if direction not in ('left', 'right', 'top', 'bottom'):
        return
    tab = boss.active_tab
    if tab is None:
        return
    previous, following = tab_directions()
    if tab.neighboring_group_id(direction) is not None:
        tab.move_window(direction)
    elif direction == previous:
        boss.move_tab_backward()
    elif direction == following:
        boss.move_tab_forward()
