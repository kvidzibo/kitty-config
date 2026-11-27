# Agent rules

## Tab bar icons

- Prefer the largest icon available. Kitty draws a Nerd Font private-use icon
  across two cells only when a space follows it and `symbol_map` in
  `kitty/kitty.conf` maps its codepoint to `Hack Nerd Font` (not the `Mono`
  family). Other symbols, such as `✓` or Braille dots, stay one cell wide.
- For a new or changed icon: compare the candidate glyphs' sizes in
  `Hack Nerd Font`, pick the largest suitable one, add its codepoint to
  `symbol_map` and check the result in a running Kitty.
