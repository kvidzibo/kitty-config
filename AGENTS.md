# Agent rules

## Tab bar icons

- Prefer the largest icon available. Kitty draws a private-use (Nerd Font) icon
  across two cells only when a space follows it and its glyph is wider than one
  cell. The `Mono` family squeezes every icon into one cell, so `symbol_map` in
  `kitty/kitty.conf` maps tab icons to `Hack Nerd Font`. Other symbols, such as
  `✓` or Braille dots, stay one cell wide.
- For a new or changed icon: compare the candidate glyphs' sizes in
  `Hack Nerd Font`, pick the largest suitable one, add its codepoint to
  `symbol_map` and check the result in a running Kitty.
