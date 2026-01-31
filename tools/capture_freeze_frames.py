import argparse
import os
import sys
import cv2
import numpy as np
import pygame
import importlib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interphyre.environment import PhyreEnv
from interphyre.config import SimulationConfig
from interphyre.levels import load_level


def get_all_levels():
    """Get all available level names."""
    levels_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "interphyre", "levels"
    )
    level_files = [
        f for f in os.listdir(levels_dir) if f.endswith(".py") and f != "__init__.py"
    ]
    return [f[:-3] for f in level_files]


def capture_freeze_frame(level_name: str, output_dir: str, seed: int) -> bool:
    """Capture a freeze frame for a single level at 600x600."""
    try:
        level_module_name = f"interphyre.levels.{level_name}"
        if level_module_name in sys.modules:
            importlib.reload(sys.modules[level_module_name])

        config = SimulationConfig(max_steps=1000)
        env = PhyreEnv(
            level_name=level_name,
            seed=seed,
            config=config,
            observation_type="image",
            action_type="continuous",
            render_mode=None,
        )

        obs, info = env.reset()

        if isinstance(obs, dict) and "image" in obs:
            image = obs["image"]
            if hasattr(image, "get_buffer"):
                image_array = pygame.surfarray.array3d(image)
                image_array = np.transpose(image_array, (1, 0, 2))
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            else:
                return False
        elif isinstance(obs, np.ndarray) and len(obs.shape) == 3:
            image_array = cv2.cvtColor(obs, cv2.COLOR_RGB2BGR)
        else:
            return False

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{level_name}.png")
        success = cv2.imwrite(output_path, image_array)

        env.close()
        return success

    except Exception as e:
        print(f"Error capturing {level_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate freeze frames for all levels"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for level generation"
    )
    parser.add_argument(
        "--output-dir", default="docs/levels", help="Output directory for images"
    )
    args = parser.parse_args()

    levels = get_all_levels()
    print(f"Capturing {len(levels)} freeze frames (seed={args.seed})...")

    successful = 0
    failed = 0

    for level_name in levels:
        if capture_freeze_frame(level_name, args.output_dir, args.seed):
            successful += 1
        else:
            failed += 1

    print(f"Completed: {successful} successful, {failed} failed")
    print(f"Images saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
