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


## Optional Panda3D renderer and UI migration layer

Install the optional desktop backend from the `python/` directory:

```sh
python3 -m pip install -r requirements-panda3d.txt
python3 -m mcpepy.panda_demo
```

The new `mcpepy.panda3d_bridge` converts the Python world's exposed block faces
into a batched Panda3D scene-graph geometry and uses Panda3D's camera, lighting,
and fog. It adapts the existing Python game loop to Panda3D's task/input system.
The coordinate bridge converts the prototype's Y-up world to Panda3D's Z-up
coordinates. The existing software renderer and Tkinter demo remain available.

The `mcpepy.panda3d_ui` module maps reusable UI primitives (labels, buttons,
entries, checkboxes, sliders, images, and screen transitions) to DirectGUI and
starts an initial main-menu / world-selection / create-world / options flow using
the repository's GUI assets where possible.

**Migration status:** this is a first integration layer, not a complete
translation of the original MCPE 0.6.1 render engine or every native screen.
The original terrain atlas's block/face UV mapping, animated textures, GUI
nine-patch/sprite-sheet behavior, inventory/container screens, touch controls,
font metrics, audio, persistence, multiplayer screens, and native-specific
screen behavior still require separate implementation and visual testing.
Native C/C++/Objective-C files are unchanged. The Python layer is a clean-room
adapter; it does not mechanically translate proprietary implementation code.
