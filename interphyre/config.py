from dataclasses import dataclass
from typing import Tuple, Optional
import time


@dataclass
class SimulationConfig:
    """Configuration for Box2D simulation parameters."""

    # Time and physics settings
    fps: int = 60
    time_step: float = 1 / 60
    velocity_iters: int = 6
    position_iters: int = 2

    # Physics world settings
    gravity: Tuple[float, float] = (0, -10)
    do_sleep: bool = True
    continuous_collision_detection: bool = False

    # Contact tracking settings
    track_all_contacts: bool = True  # For research/logging
    track_relevant_contacts_only: bool = False  # For performance

    # Performance monitoring
    enable_profiling: bool = False
    log_step_times: bool = False

    # Stationary world detection
    stationary_tolerance: float = 0.0001
    default_success_time: float = 2.0

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.time_step <= 0:
            raise ValueError("time_step must be positive")
        if self.velocity_iters < 1:
            raise ValueError("velocity_iters must be at least 1")
        if self.position_iters < 1:
            raise ValueError("position_iters must be at least 1")
        if self.fps <= 0:
            raise ValueError("fps must be positive")


class PerformanceProfiler:
    """Simple performance profiler for timing simulation steps."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.step_times = []
        self.render_times = []
        self.contact_update_times = []
        self.current_step_start = None

    def start_step(self):
        """Start timing a simulation step."""
        if self.enabled:
            self.current_step_start = time.perf_counter()

    def end_step(self):
        """End timing a simulation step."""
        if self.enabled and self.current_step_start is not None:
            step_time = time.perf_counter() - self.current_step_start
            self.step_times.append(step_time)
            self.current_step_start = None

    def time_render(self, func):
        """Decorator to time render calls."""
        if not self.enabled:
            return func

        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            render_time = time.perf_counter() - start
            self.render_times.append(render_time)
            return result

        return wrapper

    def time_contact_update(self, func):
        """Decorator to time contact update calls."""
        if not self.enabled:
            return func

        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            contact_time = time.perf_counter() - start
            self.contact_update_times.append(contact_time)
            return result

        return wrapper

    def get_stats(self):
        """Get performance statistics."""
        if not self.enabled:
            return {}

        stats = {}
        if self.step_times:
            stats["step_times"] = {
                "mean": sum(self.step_times) / len(self.step_times),
                "max": max(self.step_times),
                "min": min(self.step_times),
                "count": len(self.step_times),
            }
        if self.render_times:
            stats["render_times"] = {
                "mean": sum(self.render_times) / len(self.render_times),
                "max": max(self.render_times),
                "min": min(self.render_times),
                "count": len(self.render_times),
            }
        if self.contact_update_times:
            stats["contact_update_times"] = {
                "mean": sum(self.contact_update_times) / len(self.contact_update_times),
                "max": max(self.contact_update_times),
                "min": min(self.contact_update_times),
                "count": len(self.contact_update_times),
            }
        return stats

    def reset(self):
        """Reset all timing data."""
        self.step_times.clear()
        self.render_times.clear()
        self.contact_update_times.clear()
