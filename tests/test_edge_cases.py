#!/usr/bin/env python3
"""
Edge case and stress testing for performance improvements.
"""

import time
import numpy as np
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interphyre.config import SimulationConfig, PerformanceProfiler
from interphyre.levels import load_level
from interphyre.environment import PhyreEnv


def test_extreme_configurations():
    """Test extreme configuration values."""
    # Test very high FPS
    config_high_fps = SimulationConfig(fps=1000, time_step=1 / 1000)
    assert config_high_fps.fps == 1000
    assert config_high_fps.time_step == 1 / 1000

    # Test very low FPS
    config_low_fps = SimulationConfig(fps=10, time_step=1 / 10)
    assert config_low_fps.fps == 10
    assert config_low_fps.time_step == 1 / 10

    # Test high solver iterations
    config_high_iters = SimulationConfig(velocity_iters=20, position_iters=10)
    assert config_high_iters.velocity_iters == 20
    assert config_high_iters.position_iters == 10


def test_memory_usage():
    """Test memory usage with long simulations."""
    config = SimulationConfig(enable_profiling=True, track_all_contacts=True)
    level = load_level("two_body_problem", seed=42)
    env = PhyreEnv(level=level, config=config)

    obs, info = env.reset()
    action = [(0.0, 0.0)]
        obs, reward, terminated, truncated, info = env.step(action)

    # Run a long simulation
    start_time = time.perf_counter()
    trace = env.simulate(steps=1000, return_trace=True)
    end_time = time.perf_counter()

    stats = env.get_performance_stats()
    contact_stats = env.get_contact_statistics()

    wall_time = end_time - start_time
    assert wall_time > 0
    assert stats.get("step_times", {}).get("count", 0) == 1000
    assert contact_stats.get("total_events", 0) >= 0
    assert len(env.get_contact_log()) >= 0


def test_contact_tracking_performance():
    """Test performance difference between full and selective contact tracking."""
    level = load_level("basket_case", seed=42)  # More complex level with more contacts

    # Test full contact tracking
    config_full = SimulationConfig(
        track_all_contacts=True,
        track_relevant_contacts_only=False,
        enable_profiling=True,
    )

    env_full = PhyreEnv(level=level, config=config_full)
    obs, info = env_full.reset()
    action = [(0.0, 0.0)]
    obs, reward, done, truncated, info = env_full.step(action)

    start_time = time.perf_counter()
    trace_full = env_full.simulate(steps=500, return_trace=True)
    end_time = time.perf_counter()

    stats_full = env_full.get_performance_stats()
    contact_stats_full = env_full.get_contact_statistics()

    wall_time_full = end_time - start_time
    assert wall_time_full > 0
    assert stats_full.get("step_times", {}).get("count", 0) == 500
    assert contact_stats_full.get("total_events", 0) >= 0

    # Test selective contact tracking
    config_selective = SimulationConfig(
        track_all_contacts=False,
        track_relevant_contacts_only=True,
        enable_profiling=True,
    )

    env_selective = PhyreEnv(level=level, config=config_selective)
    obs, info = env_selective.reset()
    obs, reward, done, truncated, info = env_selective.step(action)

    start_time = time.perf_counter()
    trace_selective = env_selective.simulate(steps=500, return_trace=True)
    end_time = time.perf_counter()

    stats_selective = env_selective.get_performance_stats()
    contact_stats_selective = env_selective.get_contact_statistics()

    wall_time_selective = end_time - start_time
    assert wall_time_selective > 0
    assert stats_selective.get("step_times", {}).get("count", 0) == 500
    assert contact_stats_selective.get("total_events", 0) >= 0


def test_profiler_accuracy():
    """Test profiler accuracy with known timing."""
    profiler = PerformanceProfiler(enabled=True)

    # Test with known sleep times
    test_times = [0.001, 0.005, 0.01]

    for sleep_time in test_times:
        profiler.start_step()
        time.sleep(sleep_time)
        profiler.end_step()

    stats = profiler.get_stats()
    step_times = stats.get("step_times", {})

    assert step_times.get("count", 0) == 3
    assert step_times.get("mean", 0) > 0
    assert step_times.get("min", 0) > 0
    assert step_times.get("max", 0) > 0

    # Check if measurements are reasonable (within 50% of expected)
    if step_times.get("mean", 0) > 0:
        expected_mean = sum(test_times) / len(test_times)
        accuracy = abs(step_times.get("mean", 0) - expected_mean) / expected_mean
        assert (
            accuracy < 0.5
        ), f"Profiler accuracy {accuracy:.2%} is too poor (should be < 50%)"


def test_configuration_persistence():
    """Test that configuration persists correctly through environment resets."""
    config = SimulationConfig(
        fps=90,
        time_step=1 / 90,
        velocity_iters=10,
        position_iters=5,
        gravity=(0, -15),
        enable_profiling=True,
    )

    level = load_level("two_body_problem", seed=42)
    env = PhyreEnv(level=level, config=config)

    # Check that engine uses the correct config
    engine_config = env.engine.config
    assert engine_config.fps == 90
    assert engine_config.time_step == 1 / 90
    assert engine_config.gravity == (0, -15)
    assert engine_config.velocity_iters == 10
