"""Ask for a name when a click on Kitty's tab bar opens a new tab."""
from kitty.tabs import TabManager


def _prompt_for_title(boss, tab):
    window = tab.active_window
    if window is None:
        return
    tab_id = tab.id

    def set_title(title):
        tab = boss.tab_for_id(tab_id)
        if tab is not None:
            tab.set_title(title.strip())

    boss.get_line(
        "Enter a name for the new tab.",
        set_title,
        window=window,
        prompt="Tab name: ",
        window_title="Name new tab",
    )


def on_load(boss, data):
    # Kitty 0.51 hard-codes new_tab() for tab-bar double-clicks and the "+" button.
    original = TabManager.handle_tab_bar_mouse
    if getattr(original, "prompts_for_title", False):
        return

    def handle_tab_bar_mouse(self, *args, **kwargs):
        before = {tab.id for tab in self.tabs}
        original(self, *args, **kwargs)
        added = [tab for tab in self.tabs if tab.id not in before]
        if added:
            _prompt_for_title(boss, added[-1])

    handle_tab_bar_mouse.prompts_for_title = True
    TabManager.handle_tab_bar_mouse = handle_tab_bar_mouse
