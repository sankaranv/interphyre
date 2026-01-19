#!/usr/bin/env python3
"""
Demo: event-driven replanning with action placement only.

This demo pauses the simulation on an event trigger, then places the action
object (red ball) and continues. It does not modify green/blue or other objects.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from interphyre.engine import Box2DEngine
from interphyre.config import SimulationConfig
from interphyre.interventions import on_contact, on_success, run_until
from interphyre.levels import load_level
from interphyre.objects import Ball, create_ball


def create_renderer(
    record_format: str | None,
    output_dir: str,
    level_name: str,
    seed: int,
    fps: int,
):
    if record_format:
        from tools.video_recorder import VideoRecorder, generate_video_filename

        output_path = generate_video_filename(
            level_name,
            seed=seed,
            output_dir=output_dir,
            video_format=record_format,
            label="action_replan",
        )
        renderer = VideoRecorder(
            width=600, height=600, ppm=60, video_format=record_format, fps=fps
        )
        renderer.set_output_path(output_path)
        return renderer

    from interphyre.render.pygame import PygameRenderer

    return PygameRenderer(width=600, height=600, ppm=60)


def main() -> None:
    level_name = "catapult"
    seed = 0
    max_steps = 500
    action_x, action_y, action_radius = -0.25, 2.5, 1.0
    add_x, add_y, add_radius = -2.0, -3.0, 0.4
    render = True
    record_format = None  # "gif" or "mp4"
    output_dir = "outputs"

    level = load_level(level_name, seed=seed)
    config = SimulationConfig(enable_interventions=True)
    engine = Box2DEngine(level, config)

    renderer = None
    render_fn = None
    if render or record_format:
        renderer = create_renderer(
            record_format=record_format,
            output_dir=output_dir,
            level_name=level_name,
            seed=seed,
            fps=config.fps,
        )
        render_fn = renderer.render

    try:
        if render_fn:
            render_fn(engine)

        engine.place_action_objects([(action_x, action_y, action_radius)])
        print(
            "[Agent] Placed initial red ball:",
            (action_x, action_y, action_radius),
        )

        trigger = on_contact("green_ball", "black_platform")
        print("[Agent] Waiting for trigger:", trigger)
        snapshot, step = run_until(
            engine, trigger, max_steps=max_steps, render=render_fn
        )

        if not snapshot:
            print("[Agent] Trigger did not fire within max steps.")
            return

        print(f"[Agent] Trigger fired at step {step}.")
        snapshot.restore(engine)
        new_name = "red_ball_2"
        if new_name in engine.bodies:
            new_name = f"red_ball_2_{step}"
        new_ball = Ball(
            x=add_x,
            y=add_y,
            radius=add_radius,
            color="red",
            dynamic=True,
        )
        engine.level.objects[new_name] = new_ball
        engine.bodies[new_name] = create_ball(
            engine.world,
            new_ball,
            new_name,
            use_ccd=engine.config.continuous_collision_detection,
        )
        from Box2D import b2Vec2

        engine.bodies[new_name].ApplyLinearImpulse(
            b2Vec2(5.0, 0.0), engine.bodies[new_name].worldCenter, True
        )
        print(
            "[Agent] Added red ball:",
            (add_x, add_y, add_radius),
        )

        remaining = max(max_steps - step, 0)
        if remaining > 0:
            run_until(
                engine,
                on_success(),
                start_step=step,
                max_steps=remaining,
                render=render_fn,
            )

        success = engine.level.success_condition(engine)
        print(f"[Agent] Final result: {'Success' if success else 'Failure'}")
    finally:
        if renderer:
            renderer.close()


if __name__ == "__main__":
    main()
