# minemap

Brady's annotated Minecraft (Bedrock, iPhone) world map. Static site on GitHub Pages — no backend.

## Layout
- `index.html` — touch pan/zoom viewer. Tap = coords + direction from Home; Pins sheet has "Go to X,Z"; Grid = 512-block map frames.
- `img/world.png` — stitched world, 4 blocks/px. Level-3 tiles fill in under missing level-2s; level-4 maps (`img/tiles/l4_*.png`, 16 blocks/px, listed in `data/world.json` → `level4` with their frame origin in blocks) fill anything still empty. Image origin is (x0,z0) in world.json; the 8×4 level-2 wall sits at z −1088 inside it.
- `data/world.json` — world image placement (`x0`,`z0`, blocks per px) and which screenshot sits in which frame.
- `data/nether.json` — Nether pins `{name,type,x,y,z,notes}` in NETHER coordinates; the viewer's Nether toggle draws them at ×8 on the Overworld map and adds Nether coords to the tap readout.
- `data/pins.json` — points of interest: `{name,type,x,y,z,notes,photos[]}`; photos live in `img/poi/<slug>/` (≤1600px JPEG) and show as a strip in the pin sheet with a swipeable lightbox. One pin per place — several screenshots of the same village go on the one pin. Each pin has a `biome` field (Brady's rule — always record the biome) shown as a tag; `notes` is one or two plain sentences. Pin names: `Thing (qualifier)` when there are several of a kind, e.g. `Sulfur springs (pool)`. Types: home, village, portal, stronghold, cave, outpost, mansion, ruins, temple, monument, spawner, mine, loot, danger, cliff, mountain, mob, landmark, biome.
- `img/tiles/` — cleaned 128×128 map tiles cropped from screenshots.
- `img/wall.png` — the map wall photographed and warped flat (tools/wallfill.py); fills pixels the screenshot HUD covered.
- `img/relief.png` + `img/topo.png` (tools/topo.py) — Terrain toggle. The map's own slope shading (each pixel lit/darkened vs the pixel north of it) exaggerated on open ground, plus red = rough/steep open ground, green hatch = tree canopy. A true height field was attempted (integrating the shading north→south, calibrated against pin Y values) and does NOT work on these angled/JPEG tiles — correlation with pin heights ≈ 0 — so no elevations are shown. Flat, nearest-neighbour map screenshots would make a real DEM possible.
- `img/biomes.png` + `data/biomes.json` — best-guess biome layer from map colours (tools/biomes.py), with the key the viewer shows.
- `tools/` — run from repo root:
  - `place.py <wall_photo> <tile_screenshot>...` — rectifies tiles into `img/tiles/rect_IMG_<n>.png` and prints each one's grid (fx,fy) by matching against known tiles in a photo of the map wall. Add results to `data/assign.json`.
  - `readcoords.py` — reads the `Position: x, y, z` HUD line off a screenshot by template-matching the pixel font (OCR fails on it); used to match POI screenshots to pins.
  - `wallfill.py <wall_photo>...` — rebuild `img/wall.png` (run when new wall photos or tiles arrive).
  - `biomes.py` — rebuild the biome layer after compose.
  - `compose.py` — assembles `img/world.png` from `img/tiles/` + `data/assign.json` + `data/world.json` (level-3 list).
  - `crop.py`, `rectify.py` — helpers (border detection, perspective-rectify to 128×128). `sift.py`, `refine.py` — older one-offs.
- Viewer toggles: Frames (map-frame grid per level with coverage, coordinate chips, pinned headers), Biomes (overlay + key; tap readout names the biome), Slime (Bedrock slime chunks — seed-independent, computed in JS: `seed=(chunkX*0x1f1f1f1f)^chunkZ`, MT19937 first output % 10 == 0).

## Coordinate facts (Bedrock, verified)
- Maps are grid-aligned: a map of size S (128·2^level) covers `S·k − 64 … S·k + S − 65` on both axes. Level-4 (S=2048) frames therefore start at −4160, −2112, −64 …
- Map wall = 8×4 level-2 maps, top-left frame starts at (x −4160, z −1088). Frame (fx,fy) top-left = (−4160 + 512·fx, −1088 + 512·fy).
- Home: round house at (−2428, 63, −449).

## Map frames and naming
A map at level L is 128·2^L blocks square and sits on a fixed grid: frame k covers `S·k − 64 … S·k + S − 65` (S = 512 / 1024 / 2048 for L2 / L3 / L4). Names are relative to the frame that contains Home *at that level*: `L2 H`, `L2 S1E1`, `L3 N1`, `L4 W1`. The level prefix matters because `L2 S1E1` and `L3 S1E1` are different squares.
- Home's frames: L2 x −2624…−2113, z −576…−65 (wall grid 3,1) · L3 x −3136…−2113, z −1088…−65 · L4 x −4160…−2113, z −2112…−65.
- Viewer: the **Frames** button cycles L2 → L3 → L4. Green = mapped at that level (or finer), orange = only a coarser map here, grey = nothing. Tap a frame for its bounds, centre, what to name it and how to make it. `tools/frames.py` rebuilds `data/frames.json` from `data/source.npy` (written by compose.py: 2/3/4 = map level per pixel, 9 = wall-photo fill).
- To make a map for a frame: stand anywhere inside it, craft an empty map (locks to the frame), zoom it L times, fly it, then screenshot it held flat.

## Workflow
Brady uploads screenshots in a Claude session → `place.py` (tiles) / read coords off POI shots → edit `data/pins.json` → `compose.py` → `biomes.py` → push to `main` → Pages redeploys.
Pushing needs the Claude GitHub App installed on bradyrw (done 2026-10-09); a PAT alone is no longer enough from the cloud sandbox.
