# minemap

Brady's annotated Minecraft (Bedrock, iPhone) world map. Static site on GitHub Pages — no backend.

## Layout
- `index.html` — touch pan/zoom viewer. Tap = coords + direction from Home; Pins sheet has "Go to X,Z"; Grid = 512-block map frames.
- `img/world.png` — stitched world, 4 blocks/px (level-2 resolution). Level-3 tiles fill in under missing level-2s.
- `data/world.json` — world image placement (`x0`,`z0`, blocks per px) and which screenshot sits in which frame.
- `data/pins.json` — points of interest: `{name,type,x,y,z,notes}`. Types: home, village, portal, stronghold, cave, outpost, mansion, ruins, temple, monument, spawner, mine, loot, danger, cliff, mountain, mob, landmark, biome.
- `img/tiles/` — cleaned 128×128 map tiles cropped from screenshots.
- `tools/` — crop.py (find the map in a screenshot), sift.py (locate a tile on the map-wall photo), compose.py (assemble world.png).

## Coordinate facts (Bedrock, verified)
- Maps are grid-aligned: a map of size S (128·2^level) covers `S·k − 64 … S·k + S − 65` on both axes.
- Map wall = 8×4 level-2 maps, top-left frame starts at (x −4160, z −1088). Frame (fx,fy) top-left = (−4160 + 512·fx, −1088 + 512·fy).
- Home: round house at (−2428, 63, −449).

## Workflow
Brady uploads screenshots in a Claude session → Claude places maps / reads coords off POI shots → edits `data/pins.json`, regenerates `world.png` → push to `main` → Pages redeploys.
