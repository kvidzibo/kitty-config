"""Remote-control kitten: switch tabs only inside the pointed-at tab bar."""

from kittens.tui.handler import result_handler
from kitty.fast_data_types import is_tab_bar_visible, viewport_for_window
from kitty.utils import platform_window_id


def main(args):
    pass


@result_handler(no_ui=True)
def handle_result(args, _answer, _target_window_id, boss):
    xid, x, y, delta = map(int, args[1:])
    for manager in boss.os_window_map.values():
        if platform_window_id(manager.os_window_id) != xid:
            continue
        if not is_tab_bar_visible(manager.os_window_id):
            return
        bounds = viewport_for_window(manager.os_window_id)[1]
        if bounds.left <= x < bounds.right and bounds.top <= y < bounds.bottom:
            manager.next_tab(delta)
        return
