# Python rewrite workspace

This is a dependency-free Python engine prototype kept separate from the native build while replacements are tested. The original native source tree remains unchanged.

## Implemented prototype systems

- Standard-library-only 3D vector and matrix math
- RGB framebuffer with depth testing and alpha blending
- CPU triangle rasterizer with homogeneous frustum clipping
- Perspective-correct UV interpolation for textured triangles
- Texture sampling (nearest and bilinear) and PPM / uncompressed BMP loading
- Multiplicative tint/lighting and an approximate depth-based fog option
- Voxel chunk storage, visible-face extraction, sparse world/chunk manager
- Deterministic rolling terrain prototype (not claimed to match the original generator)
- Basic AABB collision and axis-separated movement
- Unit tests for math, framebuffer, clipping, textures, voxels, world and collision

## Run tests

Run these commands from this directory:

```sh
python3 -m unittest discover -s tests -v
```

## Remaining phases

This is **not a finished game or faithful MCPE 0.6.1 port**. The renderer is a general software prototype and lighting/fog are approximate. Next phases include chunk mesh generation and integration, camera/input/game loop, player controller, blocks/items, persistence, entities, UI, audio, and platform packaging. Validate against source code the project is authorized to adapt or lawful behavioral references before replacing native counterparts. Do not remove native files until replacements are tested.
