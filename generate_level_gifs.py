#!/usr/bin/env python3
"""
Generate GIF previews for all levels by finding valid solutions.

For each level:
1. Try seed 42 with random actions
2. Find a non-trivial solution (red ball must interact with scene)
3. Record as GIF and save to docs/levels/
4. If no solution found, skip (user will handle manually)
"""

import json
import numpy as np
from pathlib import Path
from interphyre import InterphyreEnv
from interphyre.levels import list_levels
from interphyre.render.video import VideoRecorder


def is_trivial_solution(action, level_name, env):
    """
    Check if solution is trivial (red ball doesn't meaningfully interact).

    A solution is trivial if:
    - Ball radius is very small (< 0.15)
    - Ball is placed far from scene center (|x| > 4 or y > 4 or y < -4)
    """
    x, y, radius = action

    # Tiny ball
    if radius < 0.15:
        return True

    # Far from action (outside typical interaction zone)
    if abs(x) > 4.5 or y > 4.5 or y < -4.5:
        return True

    return False


def find_solution(level_name, seed=42, max_attempts=1000):
    """
    Find a non-trivial solution for a level.

    Returns:
        tuple: (action, success) or (None, False) if no solution found
    """
    print(f"\n{level_name}:")
    print(f"  Searching for solution (seed={seed}, max_attempts={max_attempts})...")

    env = InterphyreEnv(level_name, seed=seed)
    np.random.seed(seed)

    for attempt in range(max_attempts):
        # Sample random action
        action = env.action_space.sample()

        # Run simulation
        env.reset()
        obs, reward, terminated, truncated, info = env.step(action)

        if info['success']:
            # Check if solution is non-trivial
            if is_trivial_solution(action, level_name, env):
                if attempt < 5:
                    # If trivial on first few tries, likely easy level
                    # Continue searching for better solution
                    continue
                else:
                    # Accept it if we've tried enough
                    print(f"  ✓ Solution found (attempt {attempt + 1}): {action}")
                    env.close()
                    return tuple(action), True
            else:
                print(f"  ✓ Solution found (attempt {attempt + 1}): {action}")
                env.close()
                return tuple(action), True

        # Progress indicator
        if (attempt + 1) % 100 == 0:
            print(f"    Tried {attempt + 1} attempts...")

    env.close()
    print(f"  ✗ No solution found in {max_attempts} attempts")
    return None, False


def record_solution_gif(level_name, seed, action, output_path):
    """
    Record a solution as a GIF.

    Args:
        level_name: Name of the level
        seed: Random seed
        action: Action tuple (x, y, radius)
        output_path: Path to save GIF
    """
    print(f"  Recording GIF to {output_path}...")

    # Create recorder
    recorder = VideoRecorder(
        width=600,
        height=600,
        ppm=60,
        video_format="gif",
        fps=60,
        output_path=str(output_path)
    )

    # Create environment and set custom renderer
    env = InterphyreEnv(level_name, seed=seed)
    env.renderer = recorder

    env.reset()
    obs, reward, terminated, truncated, info = env.step(action)

    # Close recorder to save GIF
    recorder.close()
    env.close()

    print(f"  ✓ GIF saved")


def main():
    """Generate GIFs for all levels."""
    levels = list_levels()
    docs_dir = Path("docs/levels")
    docs_dir.mkdir(exist_ok=True)

    solutions = {}
    failed_levels = []

    print(f"Generating GIFs for {len(levels)} levels...")
    print("=" * 60)

    for level_name in levels:
        # Try to find solution
        action, success = find_solution(level_name, seed=42, max_attempts=1000)

        if success:
            # Record as GIF
            output_path = docs_dir / f"{level_name}.gif"
            record_solution_gif(level_name, 42, action, output_path)

            solutions[level_name] = {
                "seed": 42,
                "action": list(action),
                "output": str(output_path)
            }
        else:
            failed_levels.append(level_name)

    # Save solutions to file for reference
    with open("level_gif_solutions.json", "w") as f:
        json.dump(solutions, f, indent=2)

    # Summary
    print("\n" + "=" * 60)
    print(f"\nSummary:")
    print(f"  ✓ Generated: {len(solutions)} GIFs")
    print(f"  ✗ Failed: {len(failed_levels)} levels")

    if failed_levels:
        print(f"\nLevels needing manual solutions:")
        for level in failed_levels:
            print(f"  - {level}")

    print(f"\nSolutions saved to: level_gif_solutions.json")


if __name__ == "__main__":
    main()
