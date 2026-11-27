# kitty-config

Personal [Kitty](https://sw.kovidgoyal.net/kitty/) setup: configuration, session
persistence, named tabs, split navigation, link previews and an agent status
indicator in the tab bar.

Linux only. Verified on Kitty 0.51.1; some features patch Kitty internals and
may break on other versions.

## Contents

- `kitty/kitty.conf`, `kitty/tabs-left.conf`, `kitty/tabs-top.conf` — configuration
- `kitty/open-actions.conf` — previews for clicked file links
- `persist_kitty_session` — launcher that saves and restores the tab layout
- `kitty_persist.desktop` — application menu entry for the launcher
- `new_named_tab.py`, `detach_named_tab.py`, `focus_or_tab.py`, `move_or_tab.py` — kittens
- `kitty_tab_spinner.py` — working/ready indicator, installed as `tab_bar.py`
- `fonts/KittyTabPie.ttf` — extra icons for that indicator; `fonts/build_tab_pie.py` rebuilds it
- `kitty/session_watcher.py`, `kitty/new_tab_title_watcher.py` — watchers loaded by the launcher
- `scripts/` — preview helpers, link kittens, tab scrolling, Thunar helper

## Requirements

- Kitty 0.51+ with `kitty` and `kitten` on `PATH`
- [Hack Nerd Font](https://www.nerdfonts.com/): the `Hack Nerd Font Mono` family (terminal font) and
  `Hack Nerd Font` (larger tab status icons)
- `fontconfig` (`fc-cache`) to install the bundled tab icon font
- Previews: `glow`, `less` (with `--header`), ImageMagick (`magick`); `rsvg-convert` for SVG
- Tab scrolling (X11 only): `xinput`, `xdotool`, `xwininfo`, `stdbuf`

## Install

Clone anywhere, then link the files into `~/.config/kitty`. The commands replace
existing files with the same names, so back up your own `kitty.conf`,
`open-actions.conf` and `tab_bar.py` first. Move an existing
`~/.config/kitty/scripts` directory aside; the link fails rather than nest inside it.

```bash
cd kitty-config
mkdir -p ~/.config/kitty ~/.local/bin ~/.local/share/applications ~/.local/share/fonts
ln -sfn "$PWD/kitty/"{kitty,tabs-left,tabs-top,open-actions}.conf ~/.config/kitty/
ln -sfn "$PWD/"{new_named_tab,detach_named_tab,focus_or_tab,move_or_tab}.py ~/.config/kitty/
ln -sfnT "$PWD/kitty_tab_spinner.py" ~/.config/kitty/tab_bar.py
ln -sfnT "$PWD/scripts" ~/.config/kitty/scripts
ln -sfn "$PWD/persist_kitty_session" ~/.local/bin/
ln -sfn "$PWD/kitty_persist.desktop" ~/.local/share/applications/
ln -sfn "$PWD/fonts/KittyTabPie.ttf" ~/.local/share/fonts/
fc-cache -f ~/.local/share/fonts
```

Restart Kitty after installing the font. Without it, half of the working
indicator's frames show as missing-glyph boxes.

Start Kitty with `~/.local/bin/persist_kitty_session` instead of `kitty` (the
bare name works when `~/.local/bin` is on `PATH`), or pick **Kitty (persist)**
in an application launcher; that entry needs `~/.local/bin` on `PATH`. The watchers and the
session saver load only through this launcher, so Kitty instances started any
other way never overwrite the saved layout. Run one launcher instance at a time:
every instance saves to the same file, and the last save wins.

Kitty reloads `kitty.conf` automatically; **Ctrl+Shift+F5** reloads it manually.
Restart Kitty through the launcher after changing a watcher or
`allow_remote_control`; a reload does not apply either.

## Sessions

The layout is saved to `~/.config/kitty/main.session` and restored on startup.
That file is local state and is not tracked here. On first start it does not
exist; Kitty logs a warning and opens one tab.

- Saved: tabs, split layouts and working directories.
- Not saved: commands and launch environment overrides (which can contain
  credentials). Restored panes open the default shell.
- Layout, tab, pane, focus and command-completion events trigger a save after
  0.3 seconds. A save also runs every five minutes and on Kitty's **Quit** action.
- Directory updates on command completion need Kitty shell integration.
- Closing the last pane keeps the last nonempty snapshot. Crashes and forced
  kills cannot trigger a final save.

## Keys

| Key | Action |
|---|---|
| **Alt+R** / **Alt+D** | Split right / down, in the directory of the active pane's oldest foreground process |
| **Alt+T** | New named tab in that same directory |
| **Ctrl+Shift+T** | New named tab in Kitty's default directory |
| **Ctrl+Alt+T** | Move the focused pane to a new named tab |
| **Ctrl+Alt+W** | Move the tab to a new OS window |
| **Ctrl+Alt+R**, **Alt+Shift+R** | Rename the tab |
| **Alt+arrows/HJKL** | Focus the neighbouring pane; at the edge, switch tab |
| **Ctrl+Alt+arrows** | Move the pane; at the edge, move the tab |
| **Alt+I** | Pick an image path on screen and preview it in an overlay |
| **Shift+Enter** | Send ESC+CR (newline instead of submit in agent CLIs) |

New tabs ask for a name; an empty name keeps Kitty's default title. Detaching
a pane suggests its directory name. Tabs opened by double-clicking empty tab-bar space
or the **+** button ask for a name too.

Tab switching and moving at the edge follow the tab bar axis: up/down for side
bars, left/right for top and bottom bars.

## Tab bar position

`kitty.conf` includes `tabs-left.conf` (sidebar) or `tabs-top.conf`. Change the
`include` line and restart Kitty to switch. In the sidebar, `tab_title_max_length`
also sets its width. Left and right tab bars need Kitty 0.48+; two-line titles
need a newer release (verified on 0.51.1).

## Links and previews

Clicked file links open in a purple, read-only preview tab named after the file,
with the full source path pinned at the top.

| Link | Preview |
|---|---|
| `.md` | Formatted Markdown (Glow + `less`); **q** closes |
| `.diff`, `.patch`, `.ansi` | `less -R`; **q** closes |
| Other plain text, files named `admin-password` | `less`; **q** closes |
| Images | Zoom with scroll or **+/−**, pan with drag or arrows, **0** fits; **q**, **Esc** or right-click closes |
| `.html`, `.htm` | Default browser |

For a coloured diff, link the output of
`git diff --color=always BASE HEAD > /tmp/review.diff.ansi`.

| Click | Result |
|---|---|
| **Alt+click** | Open and focus the preview tab |
| **Ctrl+click** (also with Alt or Shift) | Open the tab in the background |
| **Shift+click** (also with Alt) | Open in a separate preview-only window, reused for later previews |
| **Middle-click** | Paste the selection, even when an application captures the mouse |

`kitty.conf` adds `~/.config/kitty/scripts` to `exe_search_path`, so launch
commands find the preview helpers by name.

## Agent status indicator

Each tab title has a fixed-width prefix:

- An amber pie that fills clockwise, then empties clockwise, while an agent
  works: a pane reports indeterminate progress (OSC 9;4) or shows Codex's
  working title.
- A green check when it stops, until you visit the tab. Ready means the agent
  stopped, not that it succeeded.
- With a [Pinote](https://github.com/kvidzibo/pinote) task that has a pull
  request (`pinote_pr` user variable): a git icon, red for failing checks or
  conflicts, amber for pending, green for passing, purple for merged, grey
  for closed or while there is no current status.

Completion bells mark the pane for attention. For Codex CLI, set under `[tui]`
in `~/.codex/config.toml`:

```toml
terminal_title = ["app-name", "spinner", "status", "project"]
notifications = ["approval-requested", "agent-turn-complete"]
notification_method = "bel"
notification_condition = "always"
```

Unread indicators are kept in memory and reset when Kitty reloads.

## Mouse-wheel tab switching (X11)

`scripts/kitty-tab-scroll.py` switches tabs when the pointer is over the tab
bar: wheel up for the previous tab, wheel down for the next, wrapping at either
end. It observes input without grabbing it, so scrolling elsewhere is unchanged.
Smooth touchpad scrolling is not guaranteed.

```bash
kitty +launch ~/.config/kitty/scripts/kitty-tab-scroll.py   # Ctrl+C stops it
```

For i3 startup, link the snippet and restart i3 in place (`i3-msg restart`; a
config reload does not run it). Your i3 config must load the
directory with `include ~/.config/i3/config.d/*.conf`; otherwise copy the
snippet's `exec_always` line into it. One observer runs per user and display, so
repeated restarts do not start duplicates.

```bash
mkdir -p ~/.config/i3/config.d
ln -sfn "$PWD/kitty/tab-scroll.i3.conf" ~/.config/i3/config.d/kitty-tab-scroll.conf
```

## Thunar: Open Terminal Here

Set the custom action command in `~/.config/Thunar/uca.xml` to the absolute path
of the helper, keeping the directory condition and `*` pattern. Keep the quotes
if the path contains spaces:

```text
"/path/to/kitty-config/scripts/thunar-kitty-tab.sh" %f
```

It opens and focuses a new Kitty tab in the chosen folder, titled with the
folder name, in the Kitty instance on the same X11 display. With no reachable
instance there it opens one new Kitty window without restoring saved tabs. A set
`KITTY_LISTEN_ON` names the instance instead; if that one is unreachable, the
helper fails. Restart Thunar if the menu still runs the old
command.

## Remote control

`kitty.conf` sets `allow_remote_control socket-only` and `listen_on unix:@mykitty`; Kitty
appends its process ID, giving `unix:@mykitty-<pid>`. The session saver, tab
scrolling and Thunar helper rely on this socket name.

Requests are accepted only through that socket. Programs that merely write to a
Kitty window, such as ones on a remote host over SSH, cannot control Kitty;
local processes that can reach the socket can read and control every pane. A
running Kitty keeps its previous policy until it is quit and restarted. See
Kitty's [remote control documentation](https://sw.kovidgoyal.net/kitty/remote-control/).

## Tests

```bash
uv venv .venv  # once
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
bash tests/kitty-image-overlay.bash
```

The tests mock Kitty's Python modules; one test also runs `kitty +runpy`.

## License

[MIT](LICENSE). `fonts/KittyTabPie.ttf` holds mirrored circle-slice glyphs from
[Material Design Icons](https://github.com/Templarian/MaterialDesign)
(Apache-2.0), taken from Hack Nerd Font.
