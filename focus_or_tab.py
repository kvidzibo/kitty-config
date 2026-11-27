from typing import List
from kitty.boss import Boss
from kittens.tui.handler import result_handler
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
    tm = boss.active_tab_manager
    tab = boss.active_tab
    if tm is None or tab is None:
        return
    neighbor = tab.neighboring_group_id(direction)
    if neighbor is not None:
        tab.windows.set_active_group(neighbor)
        return
    # Only directions along the tab bar wrap to tabs at the edge.
    previous, following = tab_directions()
    if direction not in (previous, following) or len(tm.tabs) <= 1:
        return
    if direction == previous:
        boss.previous_tab()
    else:
        boss.next_tab()
