# Python rewrite workspace

This is a dependency-free Python engine prototype kept separate from the native build while replacements are tested. The original native source tree remains unchanged.

## Implemented prototype systems

- 3D vector/matrix math; RGB framebuffer with depth testing and alpha blending
- CPU triangle rasterizer with homogeneous frustum clipping and perspective-correct texture coordinates
- Texture sampling (nearest and bilinear) and PPM / uncompressed BMP loading
- Multiplicative tint/lighting and approximate depth-based fog
- Voxel chunk storage, world-coordinate manager, visible-face mesh generation and renderer bridge
- Deterministic rolling terrain prototype (not claimed to match the original generator)
- Basic AABB collision and axis-separated movement
- Automated unit tests for these systems

## Run tests

```sh
python3 -m unittest discover -s tests -v
```

## Remaining phases

This is **not a finished game or faithful MCPE 0.6.1 port**. The renderer is a general software prototype, and its lighting/fog are approximate. Next phases include camera/input/game loop, player controller, block/item rules, persistence, entities, UI, audio, and platform packaging. Validate against source code the project is authorized to adapt or lawful behavioral references before replacing native counterparts. Do not remove native files until replacements are tested.
