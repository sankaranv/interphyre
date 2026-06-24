"""
Shared pytest fixtures for interphyre tests.
"""

import sys

import pytest

from interphyre import InterphyreEnv, SimulationConfig

# Bundle validation tests replay solutions generated on Linux (GCC/glibc).
# Apple Clang/libm produces subtly different float results that cause Box2D
# physics to diverge over long simulations, producing spurious failures on
# macOS that do not indicate real regressions.  The authoritative gate runs
# in Docker (scripts/bundle_validate.sh) or on the Linux cluster.
skip_on_macos = pytest.mark.skipif(
    sys.platform == "darwin",
    reason="bundle generated on Linux; float divergence under Apple Clang causes spurious failures",
)


@pytest.fixture
def default_config():
    """Default simulation configuration for tests."""
    return SimulationConfig(
        fps=60,
        time_step=1 / 60,
        enable_profiling=False,
    )


@pytest.fixture
def intervention_config():
    """Simulation config with interventions enabled."""
    return SimulationConfig(
        fps=60,
        time_step=1 / 60,
        enable_profiling=False,
    )


@pytest.fixture
def simple_env(default_config):
    """Pre-initialized environment for the two_body_problem level."""
    env = InterphyreEnv("two_body_problem", seed=42, config=default_config)
    yield env
    env.close()


@pytest.fixture
def intervention_env(intervention_config):
    """Environment with interventions enabled."""
    env = InterphyreEnv("two_body_problem", seed=42, config=intervention_config)
    yield env
    env.close()
