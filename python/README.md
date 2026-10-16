# Python rewrite workspace

This directory is the start of an independently implemented Python client/engine. It is intentionally separate from the original native build until individual Python systems have tests and are ready to replace their counterparts.

## Current prototype systems

- Standard-library-only 3D vector and matrix math
- RGB framebuffer and depth buffer
- CPU triangle rasterizer (with clipping and texture features still incomplete)
- Voxel chunk storage and visible-face extraction
- Sparse world/chunk manager with negative world-coordinate support
- Deterministic rolling terrain prototype
- Unit tests for math, framebuffer, renderer, voxel storage, world coordinates, and terrain

## Run the tests

Run these commands from this `python` directory. Do not run a test file directly from `tests/`, because Python then may not include this parent directory on its import path.

```sh
python3 -m unittest discover -s tests -v
```

If you need to run one test file only:

```sh
PYTHONPATH=. python3 -m unittest discover -s tests -p "test_voxel.py" -v
PYTHONPATH=. python3 -m unittest discover -s tests -p "test_world.py" -v
```

The renderer and terrain are prototypes, not completed MCPE 0.6.1 implementations. Follow-up work includes proper clipping, texture sampling, perspective-correct interpolation, lighting/fog, chunk meshing and batching, gameplay physics, assets, UI, audio, persistence, and reference-based validation. Terrain generation is deliberately original and is not claimed to reproduce the original game's algorithm.
