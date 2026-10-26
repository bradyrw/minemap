# minemap

Brady's annotated Minecraft (Bedrock, iPhone) world map. Static site on GitHub Pages — no backend.

## Layout
- `index.html` — touch pan/zoom viewer. Tap = coords + direction from Home; Pins sheet has "Go to X,Z"; Grid = 512-block map frames.
- `img/world.png` — stitched world, 4 blocks/px. Level-3 tiles fill in under missing level-2s; level-4 maps (`img/tiles/l4_*.png`, 16 blocks/px, listed in `data/world.json` → `level4` with their frame origin in blocks) fill anything still empty. Image origin is (x0,z0) in world.json; the 8×4 level-2 wall sits at z −1088 inside it.
- `data/world.json` — world image placement (`x0`,`z0`, blocks per px) and which screenshot sits in which frame.
- `data/nether.json` — Nether pins `{name,type,x,y,z,notes}` in NETHER coordinates; the viewer's Nether toggle draws them at ×8 on the Overworld map and adds Nether coords to the tap readout.
- `data/pins.json` — points of interest: `{name,type,x,y,z,notes,photos[]}`; photos live in `img/poi/<slug>/` (≤1600px JPEG) and show as a strip in the pin sheet with a swipeable lightbox. One pin per place — several screenshots of the same village go on the one pin. Convention: `notes` starts with the biome (Brady's rule — always note the biome). Types: home, village, portal, stronghold, cave, outpost, mansion, ruins, temple, monument, spawner, mine, loot, danger, cliff, mountain, mob, landmark, biome.
- `img/tiles/` — cleaned 128×128 map tiles cropped from screenshots.
- `img/wall.png` — the map wall photographed and warped flat (tools/wallfill.py); fills pixels the screenshot HUD covered.
- `img/biomes.png` + `data/biomes.json` — best-guess biome layer from map colours (tools/biomes.py), with the key the viewer shows.
- `tools/` — run from repo root:
  - `place.py <wall_photo> <tile_screenshot>...` — rectifies tiles into `img/tiles/rect_IMG_<n>.png` and prints each one's grid (fx,fy) by matching against known tiles in a photo of the map wall. Add results to `data/assign.json`.
  - `readcoords.py` — reads the `Position: x, y, z` HUD line off a screenshot by template-matching the pixel font (OCR fails on it); used to match POI screenshots to pins.
  - `wallfill.py <wall_photo>...` — rebuild `img/wall.png` (run when new wall photos or tiles arrive).
  - `biomes.py` — rebuild the biome layer after compose.
  - `compose.py` — assembles `img/world.png` from `img/tiles/` + `data/assign.json` + `data/world.json` (level-3 list).
  - `crop.py`, `rectify.py` — helpers (border detection, perspective-rectify to 128×128). `sift.py`, `refine.py` — older one-offs.
- Viewer toggles: Grid (512-block map frames, with pinned header row/column), Biomes (overlay + key; tap readout names the biome), Slime (Bedrock slime chunks — seed-independent, computed in JS: `seed=(chunkX*0x1f1f1f1f)^chunkZ`, MT19937 first output % 10 == 0).

## Coordinate facts (Bedrock, verified)
- Maps are grid-aligned: a map of size S (128·2^level) covers `S·k − 64 … S·k + S − 65` on both axes. Level-4 (S=2048) frames therefore start at −4160, −2112, −64 …
- Map wall = 8×4 level-2 maps, top-left frame starts at (x −4160, z −1088). Frame (fx,fy) top-left = (−4160 + 512·fx, −1088 + 512·fy).
- Home: round house at (−2428, 63, −449).

## Workflow
Brady uploads screenshots in a Claude session → `place.py` (tiles) / read coords off POI shots → edit `data/pins.json` → `compose.py` → `biomes.py` → push to `main` → Pages redeploys.
Pushing needs the Claude GitHub App installed on bradyrw (done 2026-10-09); a PAT alone is no longer enough from the cloud sandbox.
