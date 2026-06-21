"""Tests for the new intervention API: set, add, remove, impulse, force, branch."""

import math

import pytest

from interphyre import InterphyreEnv, SimulationConfig
from interphyre.interventions.state import StateSnapshot
from interphyre.interventions.triggers import at_step
from interphyre.level import Level
from interphyre.objects import Ball, Bar, Basket


def _make_level(success_condition=None):
    objects = {
        "red_ball": Ball(x=0.0, y=2.0, radius=0.5, color="red", dynamic=True),
        "blue_ball": Ball(x=2.0, y=2.0, radius=0.5, color="blue", dynamic=True),
        "platform": Bar(x=0.0, y=-3.0, length=8.0, angle=0.0, thickness=0.2, dynamic=False),
    }
    return Level(
        name="api_test_level",
        objects=objects,
        action_objects=[],
        success_condition=success_condition or (lambda engine: False),
        metadata={},
    )


def _make_env(success_condition=None):
    config = SimulationConfig(fps=60, time_step=1 / 60, enable_profiling=False)
    env = InterphyreEnv(_make_level(success_condition), config=config)
    return env


def _snapshot(env):
    return StateSnapshot.capture(env.engine, metadata={"step_index": env.step_count})


# ── env.set: structural ──


def test_set_radius():
    env = _make_env()
    env.set("red_ball", radius=0.3)
    body = env.engine.bodies["red_ball"]
    assert abs(body.fixtures[0].shape.radius - 0.3) < 1e-6
    env.close()


def test_set_multiple_structural():
    env = _make_env()
    env.set("red_ball", radius=0.3, restitution=0.9)
    obj = env._level.objects["red_ball"]
    assert abs(obj.radius - 0.3) < 1e-6
    assert abs(obj.restitution - 0.9) < 1e-6
    env.close()


def test_set_preserves_name():
    env = _make_env()
    env.set("red_ball", radius=0.3)
    assert "red_ball" in env.engine.bodies
    assert "red_ball" in env._level.objects
    env.close()


def test_set_preserves_velocity():
    env = _make_env()
    env.step_physics(10)
    body = env.engine.bodies["red_ball"]
    vel_before = (body.linearVelocity.x, body.linearVelocity.y)
    env.set("red_ball", radius=0.3)
    body_after = env.engine.bodies["red_ball"]
    vel_after = (body_after.linearVelocity.x, body_after.linearVelocity.y)
    assert abs(vel_after[0] - vel_before[0]) < 1e-5
    assert abs(vel_after[1] - vel_before[1]) < 1e-5
    env.close()


def test_set_bar_length():
    objects = {
        "bar": Bar(x=0.0, y=0.0, length=4.0, angle=0.0, thickness=0.2, dynamic=False),
    }
    level = Level(name="bar_test", objects=objects, action_objects=[],
                  success_condition=lambda e: False, metadata={})
    config = SimulationConfig(fps=60, time_step=1 / 60, enable_profiling=False)
    env = InterphyreEnv(level, config=config)
    env.set("bar", length=2.0)
    obj = env._level.objects["bar"]
    assert abs(obj.length - 2.0) < 1e-6
    env.close()


def test_set_basket_height():
    objects = {
        "basket": Basket(x=0.0, y=0.0, scale=1.0, dynamic=False),
    }
    level = Level(name="basket_test", objects=objects, action_objects=[],
                  success_condition=lambda e: False, metadata={})
    config = SimulationConfig(fps=60, time_step=1 / 60, enable_profiling=False)
    env = InterphyreEnv(level, config=config)
    original_height = env._level.objects["basket"].height
    env.set("basket", height=original_height * 1.5)
    assert abs(env._level.objects["basket"].height - original_height * 1.5) < 1e-6
    env.close()


# ── env.set: kinematic ──


def test_set_velocity():
    env = _make_env()
    env.set("red_ball", velocity=(3.0, -1.0))
    body = env.engine.bodies["red_ball"]
    assert abs(body.linearVelocity.x - 3.0) < 1e-6
    assert abs(body.linearVelocity.y - (-1.0)) < 1e-6
    env.close()


def test_set_angular_velocity():
    env = _make_env()
    env.set("red_ball", angular_velocity=2.5)
    body = env.engine.bodies["red_ball"]
    assert abs(body.angularVelocity - 2.5) < 1e-6
    env.close()


def test_set_velocity_and_angular_velocity_replaces_freeze():
    env = _make_env()
    env.step_physics(20)
    env.set("red_ball", velocity=(0.0, 0.0), angular_velocity=0.0)
    body = env.engine.bodies["red_ball"]
    assert abs(body.linearVelocity.x) < 1e-6
    assert abs(body.linearVelocity.y) < 1e-6
    assert abs(body.angularVelocity) < 1e-6
    env.close()


def test_set_position():
    env = _make_env()
    env.set("red_ball", x=1.5, y=-1.0)
    body = env.engine.bodies["red_ball"]
    assert abs(body.position.x - 1.5) < 1e-5
    assert abs(body.position.y - (-1.0)) < 1e-5
    env.close()


def test_set_position_and_structural():
    env = _make_env()
    env.set("red_ball", radius=0.3, x=2.5)
    body = env.engine.bodies["red_ball"]
    assert abs(body.position.x - 2.5) < 1e-5
    assert abs(body.fixtures[0].shape.radius - 0.3) < 1e-6
    env.close()


def test_set_dynamic_to_static():
    env = _make_env()
    env.set("red_ball", dynamic=False)
    body = env.engine.bodies["red_ball"]
    # Box2D body type: 0=static, 1=kinematic, 2=dynamic
    assert body.type == 0
    assert not env._level.objects["red_ball"].dynamic
    env.close()


def test_set_static_velocity_ignored():
    env = _make_env()
    env.set("platform", velocity=(5.0, 0.0))
    body = env.engine.bodies["platform"]
    # Static bodies: velocity set should be silently ignored.
    assert abs(body.linearVelocity.x) < 1e-6
    env.close()


# ── env.set: validation ──


def test_set_invalid_attr_raises():
    env = _make_env()
    with pytest.raises(AttributeError):
        env.set("red_ball", nonexistent_attribute=99)
    env.close()


def test_set_invalid_value_raises():
    env = _make_env()
    with pytest.raises(ValueError):
        env.set("red_ball", radius=-1.0)
    env.close()


def test_set_unknown_object_raises():
    env = _make_env()
    with pytest.raises(ValueError):
        env.set("ghost", radius=0.5)
    env.close()


# ── env.set: restore interaction ──


def test_set_then_restore_reverts():
    env = _make_env()
    snap = _snapshot(env)
    env.set("red_ball", radius=0.3)
    assert abs(env._level.objects["red_ball"].radius - 0.3) < 1e-6
    env.restore(snap)
    assert abs(env._level.objects["red_ball"].radius - 0.5) < 1e-6
    env.close()


# ── add / remove ──


def test_add_remove_renamed():
    env = _make_env()
    new_ball = Ball(x=-1.0, y=1.0, radius=0.3, color="green", dynamic=True)
    env.add("extra_ball", new_ball)
    assert "extra_ball" in env.engine.bodies
    assert "extra_ball" in env._level.objects
    env.remove("extra_ball")
    assert "extra_ball" not in env.engine.bodies
    assert "extra_ball" not in env._level.objects
    env.close()


# ── impulse / force ──


def test_impulse_force_renamed():
    env = _make_env()
    body = env.engine.bodies["red_ball"]
    vel_before_x = body.linearVelocity.x

    env.impulse("red_ball", (10.0, 0.0))
    assert body.linearVelocity.x > vel_before_x

    env.force("red_ball", (0.0, 5.0))
    # force is applied at next step; just check no error
    env.step_physics(1)
    env.close()


# ── branch ──


def test_branch_nondestructive():
    env = _make_env()
    snap = _snapshot(env)
    original_radius = env._level.objects["red_ball"].radius

    with env.branch(snap):
        env.set("red_ball", radius=0.2)
        env.step_physics(10)
        assert abs(env._level.objects["red_ball"].radius - 0.2) < 1e-6

    # After branch: back to original
    assert abs(env._level.objects["red_ball"].radius - original_radius) < 1e-6
    env.close()


def test_branch_exception_restores_and_propagates():
    env = _make_env()
    snap = _snapshot(env)
    original_radius = env._level.objects["red_ball"].radius

    with pytest.raises(RuntimeError):
        with env.branch(snap):
            env.set("red_ball", radius=0.2)
            raise RuntimeError("intentional")

    assert abs(env._level.objects["red_ball"].radius - original_radius) < 1e-6
    env.close()


def test_branch_loop():
    env = _make_env()
    snap = _snapshot(env)

    radii = [0.1, 0.2, 0.3, 0.4]
    results = []
    for r in radii:
        with env.branch(snap):
            env.set("red_ball", radius=r)
            results.append(env._level.objects["red_ball"].radius)

    for r, result in zip(radii, results):
        assert abs(result - r) < 1e-6
    env.close()


def test_branch_nested():
    env = _make_env()
    snap = _snapshot(env)
    original_radius = env._level.objects["red_ball"].radius

    with env.branch(snap):
        env.set("red_ball", radius=0.2)
        inner_snap = _snapshot(env)
        with env.branch(inner_snap):
            env.set("red_ball", radius=0.1)
            assert abs(env._level.objects["red_ball"].radius - 0.1) < 1e-6
        # After inner branch: back to inner_snap state (radius=0.2)
        assert abs(env._level.objects["red_ball"].radius - 0.2) < 1e-6

    # After outer branch: back to original
    assert abs(env._level.objects["red_ball"].radius - original_radius) < 1e-6
    env.close()


# ── API surface ──


def test_no_intervention_context():
    env = _make_env()
    assert not hasattr(env, "intervention_context")
    env.close()


def test_set_outside_branch_is_destructive():
    env = _make_env()
    env.set("red_ball", radius=0.2)
    # No branch, no restore: change persists
    assert abs(env._level.objects["red_ball"].radius - 0.2) < 1e-6
    env.close()
