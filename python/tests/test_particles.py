"""Unit tests for particle lifetimes and deterministic block debris."""
import unittest

from mcpepy.particles import ParticleEngine


class ParticleEngineTests(unittest.TestCase):
    def test_block_break_emits_requested_count(self):
        engine = ParticleEngine(seed=12)
        engine.emit_block_break(1, 2, 3, 2, count=7)
        self.assertEqual(len(engine.particles), 7)
        self.assertTrue(all(p.color == engine.BLOCK_COLORS[2] for p in engine.particles))

    def test_particles_expire(self):
        engine = ParticleEngine(seed=1)
        engine.emit_block_break(0, 0, 0, 1, count=3)
        for particle in engine.particles:
            particle.lifetime = 0.01
        engine.update(0.02)
        self.assertEqual(engine.particles, [])

    def test_seed_makes_particle_spawn_repeatable(self):
        a = ParticleEngine(seed=44)
        b = ParticleEngine(seed=44)
        a.emit_block_break(4, 5, 6, 3)
        b.emit_block_break(4, 5, 6, 3)
        self.assertEqual(a.particles, b.particles)

    def test_clear_removes_all_particles(self):
        engine = ParticleEngine(seed=2)
        engine.emit_block_break(0, 0, 0, 1)
        engine.clear()
        self.assertEqual(engine.particles, [])


if __name__ == "__main__":
    unittest.main()
