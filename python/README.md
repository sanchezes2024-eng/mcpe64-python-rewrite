# Python rewrite workspace

This is a dependency-free Python engine prototype kept separate from the native build while replacements are tested. The original native source tree remains unchanged.

## Implemented prototype systems

- 3D vector/matrix math; RGB framebuffer with depth testing and alpha blending
- CPU triangle rasterizer with homogeneous frustum clipping and perspective-correct texture coordinates
- Texture sampling (nearest and bilinear) and PPM / uncompressed BMP loading
- Multiplicative tint/lighting and approximate depth-based fog
- Voxel chunks, world-coordinate manager, terrain prototype, exposed-face mesh generation and renderer bridge
- First-person camera, simulation step loop, keyboard movement, gravity, jumping and block collision
- Optional Tkinter demo that displays the software-rendered world
- Automated unit tests for the engine prototype

## Run tests

```sh
python3 -m unittest discover -s tests -v
```

## Run the interactive demo

```sh
python3 -m mcpepy.demo
```

Requires a Python build with Tkinter available. Controls: W/A/S/D move, Space jump, Shift sprint, arrow keys look, Esc quit. This is an early prototype, not the original game.

## Remaining phases

This is **not a finished game or faithful MCPE 0.6.1 port**. The next phases include stable input abstraction, better player physics and world boundaries, block interaction, persistence, entities, UI, audio, asset pipeline, performance work, and platform packaging. Validate against source code the project is authorized to adapt or lawful behavioral references before replacing native counterparts. Do not remove native files until replacements are tested.
