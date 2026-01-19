#!/usr/bin/env python3
"""
Demo: event-driven replanning with action placement using the new PhyreEnv API.

This demo pauses the simulation on an event trigger, then adds a new object
and continues. It demonstrates the new unified intervention API.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from interphyre import PhyreEnv
from interphyre.interventions import on_contact, on_success
from interphyre.objects import Ball


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

    # Create environment with new unified API
    env = PhyreEnv(level_name, seed=seed, enable_interventions=True)

    # Set up renderer
    renderer = None
    if render or record_format:
        renderer = create_renderer(
            record_format=record_format,
            output_dir=output_dir,
            level_name=level_name,
            seed=seed,
            fps=env.config.fps,
        )
        env.renderer = renderer

    try:
        # Render initial state
        env.render()

        # Place initial action object
        env.place_action((action_x, action_y, action_radius))
        print(
            "[Agent] Placed initial red ball:",
            (action_x, action_y, action_radius),
        )

        # Wait for trigger
        trigger = on_contact("green_ball", "black_platform")
        print("[Agent] Waiting for trigger:", trigger)
        snapshot, step = env.run_until(trigger, max_steps=max_steps)

        if not snapshot:
            print("[Agent] Trigger did not fire within max steps.")
            return

        print(f"[Agent] Trigger fired at step {step}.")

        # Restore state and add new object using intervention context
        env.restore(snapshot)

        with env.intervention_context() as ctx:
            ctx.add_object(
                "red_ball_2",
                Ball(x=add_x, y=add_y, radius=add_radius, color="red", dynamic=True),
            )
            ctx.apply_impulse("red_ball_2", impulse=(5.0, 0.0))

        print(
            "[Agent] Added red ball with impulse:",
            (add_x, add_y, add_radius),
        )

        # Continue simulation until success or timeout
        remaining = max(max_steps - step, 0)
        if remaining > 0:
            obs, reward, term, trunc, info = env.step_until(
                on_success(), max_steps=remaining
            )
            print(f"[Agent] Final result: {'Success' if info['success'] else 'Failure'}")
        else:
            print(f"[Agent] Final result: {'Success' if env.success else 'Failure'}")

    finally:
        env.close()
        if renderer:
            renderer.close()


if __name__ == "__main__":
    main()
