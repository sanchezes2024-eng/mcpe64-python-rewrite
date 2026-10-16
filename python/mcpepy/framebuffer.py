"""Dependency-free RGB framebuffer with a floating-point depth buffer."""
from __future__ import annotations
from typing import Iterable, Tuple


class Framebuffer:
    def __init__(self, width: int, height: int, clear_color=(100, 160, 220)):
        if width < 1 or height < 1:
            raise ValueError("framebuffer dimensions must be positive")
        self.width, self.height = int(width), int(height)
        self.color = bytearray(self.width * self.height * 3)
        self.depth = [float("inf")] * (self.width * self.height)
        self.clear(clear_color)

    def clear(self, color=(100, 160, 220)) -> None:
        r, g, b = self._rgb(color)
        self.color[:] = bytes((r, g, b)) * (self.width * self.height)
        self.depth[:] = [float("inf")] * (self.width * self.height)

    @staticmethod
    def _rgb(color: Iterable[int]) -> Tuple[int, int, int]:
        values = tuple(color)
        if len(values) != 3:
            raise ValueError("color must have three channels")
        return tuple(max(0, min(255, int(c))) for c in values)

    def put_pixel(self, x: int, y: int, depth: float, color) -> bool:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        index = y * self.width + x
        if depth >= self.depth[index]:
            return False
        self.depth[index] = depth
        offset = index * 3
        self.color[offset:offset + 3] = bytes(self._rgb(color))
        return True

    def to_ppm(self) -> bytes:
        """Return a binary PPM image, useful for tests and debugging."""
        header = f"P6\n{self.width} {self.height}\n255\n".encode("ascii")
        return header + bytes(self.color)
