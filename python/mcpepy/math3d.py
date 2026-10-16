"""Small dependency-free 3D math primitives.

Matrices use row-major storage and multiply column vectors. Keep this convention
consistent throughout the Python renderer.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Iterable, Tuple


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vec3":
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "Vec3":
        return self * scalar

    def __truediv__(self, scalar: float) -> "Vec3":
        if scalar == 0:
            raise ZeroDivisionError("cannot divide a vector by zero")
        return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def dot(self, other: "Vec3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vec3") -> "Vec3":
        return Vec3(self.y * other.z - self.z * other.y,
                    self.z * other.x - self.x * other.z,
                    self.x * other.y - self.y * other.x)

    def length(self) -> float:
        return math.sqrt(self.dot(self))

    def normalized(self) -> "Vec3":
        length = self.length()
        return self if length <= 1e-15 else self / length

    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass(frozen=True)
class Mat4:
    """4x4 row-major matrix represented by exactly 16 values."""
    values: Tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.values) != 16:
            raise ValueError("Mat4 requires exactly 16 values")

    @staticmethod
    def identity() -> "Mat4":
        return Mat4((1, 0, 0, 0,
                     0, 1, 0, 0,
                     0, 0, 1, 0,
                     0, 0, 0, 1))

    @staticmethod
    def translation(x: float, y: float, z: float) -> "Mat4":
        return Mat4((1, 0, 0, x,
                     0, 1, 0, y,
                     0, 0, 1, z,
                     0, 0, 0, 1))

    @staticmethod
    def scale(x: float, y: float, z: float) -> "Mat4":
        return Mat4((x, 0, 0, 0,
                     0, y, 0, 0,
                     0, 0, z, 0,
                     0, 0, 0, 1))

    @staticmethod
    def perspective(fov_y_degrees: float, aspect: float,
                    near: float, far: float) -> "Mat4":
        if not 0.0 < fov_y_degrees < 180.0:
            raise ValueError("field of view must be between 0 and 180 degrees")
        if aspect <= 0 or near <= 0 or far <= near:
            raise ValueError("expected aspect > 0 and 0 < near < far")
        f = 1.0 / math.tan(math.radians(fov_y_degrees) / 2.0)
        nf = 1.0 / (near - far)
        return Mat4((f / aspect, 0, 0, 0,
                     0, f, 0, 0,
                     0, 0, (far + near) * nf, 2 * far * near * nf,
                     0, 0, -1, 0))

    @staticmethod
    def look_at(eye: Vec3, target: Vec3, up: Vec3) -> "Mat4":
        forward = (target - eye).normalized()
        if forward.length() <= 1e-15:
            raise ValueError("eye and target must differ")
        side = forward.cross(up).normalized()
        if side.length() <= 1e-15:
            raise ValueError("up vector must not be parallel to view direction")
        actual_up = side.cross(forward)
        return Mat4((side.x, side.y, side.z, -side.dot(eye),
                     actual_up.x, actual_up.y, actual_up.z, -actual_up.dot(eye),
                     -forward.x, -forward.y, -forward.z, forward.dot(eye),
                     0, 0, 0, 1))

    def transform4(self, value: Iterable[float]) -> Tuple[float, float, float, float]:
        x, y, z, w = tuple(value)
        m = self.values
        return (m[0]*x + m[1]*y + m[2]*z + m[3]*w,
                m[4]*x + m[5]*y + m[6]*z + m[7]*w,
                m[8]*x + m[9]*y + m[10]*z + m[11]*w,
                m[12]*x + m[13]*y + m[14]*z + m[15]*w)

    def __matmul__(self, other: "Mat4") -> "Mat4":
        a, b = self.values, other.values
        out = []
        for row in range(4):
            for col in range(4):
                out.append(sum(a[row * 4 + k] * b[k * 4 + col]
                               for k in range(4)))
        return Mat4(tuple(out))
