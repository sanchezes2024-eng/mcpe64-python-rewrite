# Python rewrite workspace

This directory is the start of an independently implemented Python client/engine. It is intentionally separate from the original native build until individual Python systems have tests and are ready to replace their counterparts.

## Current part: renderer primitives

- Standard-library-only 3D math
- RGB framebuffer and depth buffer
- Homogeneous transform and perspective projection
- CPU triangle rasterizer with depth testing
- Unit tests

Run tests from this directory:

```sh
python -m unittest discover -s tests -v
```

The renderer is a foundation, not a completed MCPE 0.6.1 renderer. The next stages must implement clipping, texture sampling, perspective-correct interpolation, original-era fog/blending/lighting semantics, chunk batching, and reference-based tests. A software renderer is portable but not expected to match GPU performance.
