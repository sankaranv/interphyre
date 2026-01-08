"""
Extra environment behavior tests for verbose output and rendering hooks.
"""

import pytest

from interphyre.levels import load_level
from interphyre.environment import PhyreEnv


class DummyRenderer:
    def __init__(self):
        self.render_called = False
        self.close_called = False

    def render(self, engine):
        self.render_called = True

    def close(self):
        self.close_called = True


@pytest.mark.fast
def test_simulate_verbose_output(capsys):
    level = load_level("two_body_problem", seed=42)
    env = PhyreEnv(level=level)
    env.simulate(steps=2, verbose=True)
    captured = capsys.readouterr()
    assert "Step 1/2" in captured.out
    env.close()


@pytest.mark.fast
def test_render_and_close_hooks():
    level = load_level("two_body_problem", seed=42)
    env = PhyreEnv(level=level)
    dummy = DummyRenderer()
    env.renderer = dummy

    env.render()
    env.close()

    assert dummy.render_called is True
    assert dummy.close_called is True
