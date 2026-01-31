#!/usr/bin/env python3
"""Snapshot a level to visualize current state before making changes."""

import cv2
import numpy as np
import pygame
from interphyre.environment import PhyreEnv
from interphyre.config import SimulationConfig


def snapshot_level(level_name: str, seed: int, output_path: str):
    """Generate and save a snapshot of a level."""
    import os

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
            raise ValueError("Image format not supported")
    elif isinstance(obs, np.ndarray) and len(obs.shape) == 3:
        image_array = cv2.cvtColor(obs, cv2.COLOR_RGB2BGR)
    else:
        raise ValueError("Observation format not supported")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the image
    cv2.imwrite(output_path, image_array)
    print(f"Saved snapshot to {output_path}")
    print(f"Level: {level_name}, Seed: {seed}")
    print(f"Image size: {image_array.shape}")

    env.close()


if __name__ == "__main__":
    # Snapshot dive_bomb at a few different seeds
    for seed in [0, 42, 123]:
        snapshot_level(
            "dive_bomb",
            seed=seed,
            output_path=f"/tmp/interphyre/divebomb_fixed_seed{seed}.png"
        )
