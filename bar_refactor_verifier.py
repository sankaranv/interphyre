"""
Verification system for Bar class refactoring.

This module provides tools to verify that refactored Bar objects produce
identical results to the original trigonometric calculations.
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional
from interphyre.objects import Bar


class BarRefactorVerifier:
    """Verifies that refactored Bar objects match original calculations."""

    def __init__(self, tolerance: float = 1e-10):
        """
        Initialize verifier with specified tolerance for floating-point comparisons.

        Args:
            tolerance: Maximum allowed difference for floating-point comparisons
        """
        self.tolerance = tolerance
        self.verification_results: Dict[str, Dict[str, Any]] = {}

    def verify_bar_creation(
        self,
        old_calculation_func,
        new_bar_creation_func,
        level_name: str,
        bar_name: str,
    ) -> Dict[str, Any]:
        """
        Verify that new bar creation matches old calculation.

        Args:
            old_calculation_func: Function that returns the original Bar object
            new_bar_creation_func: Function that returns the new Bar object
            level_name: Name of the level being verified
            bar_name: Name of the specific bar being verified

        Returns:
            Dictionary containing verification results
        """
        try:
            # Run old calculation
            old_bar = old_calculation_func()

            # Create new bar
            new_bar = new_bar_creation_func()

            # Compare properties
            comparison = self._compare_bars(old_bar, new_bar)

            # Store results
            key = f"{level_name}_{bar_name}"
            self.verification_results[key] = comparison

            return comparison

        except Exception as e:
            error_result = {
                "properties_match": False,
                "error": str(e),
                "old_values": {},
                "new_values": {},
                "differences": {},
            }
            key = f"{level_name}_{bar_name}"
            self.verification_results[key] = error_result
            return error_result

    def _compare_bars(self, old_bar: Bar, new_bar: Bar) -> Dict[str, Any]:
        """
        Compare two Bar objects and return detailed comparison.

        Args:
            old_bar: Original Bar object
            new_bar: New Bar object

        Returns:
            Dictionary containing comparison results
        """
        comparison = {
            "properties_match": True,
            "differences": {},
            "old_values": {},
            "new_values": {},
            "error": None,
        }

        # Properties to compare
        properties = ["x", "y", "angle", "length", "thickness", "x1", "y1", "x2", "y2"]

        for prop in properties:
            try:
                old_val = getattr(old_bar, prop)
                new_val = getattr(new_bar, prop)

                # Handle floating point comparison
                if isinstance(old_val, (int, float)) and isinstance(
                    new_val, (int, float)
                ):
                    diff = abs(old_val - new_val)
                    comparison["old_values"][prop] = old_val
                    comparison["new_values"][prop] = new_val

                    if diff > self.tolerance:
                        comparison["properties_match"] = False
                        comparison["differences"][prop] = {
                            "old": old_val,
                            "new": new_val,
                            "difference": diff,
                        }
                else:
                    # Non-numeric comparison
                    comparison["old_values"][prop] = old_val
                    comparison["new_values"][prop] = new_val

                    if old_val != new_val:
                        comparison["properties_match"] = False
                        comparison["differences"][prop] = {
                            "old": old_val,
                            "new": new_val,
                            "difference": "non-numeric",
                        }

            except AttributeError as e:
                comparison["properties_match"] = False
                comparison["error"] = f"Attribute error comparing {prop}: {e}"

        return comparison

    def print_verification_report(self, level_name: str) -> None:
        """
        Print detailed verification report for a level.

        Args:
            level_name: Name of the level to report on
        """
        print(f"\n{'='*60}")
        print(f"VERIFICATION REPORT FOR {level_name.upper()}")
        print(f"{'='*60}")

        level_results = {
            k: v
            for k, v in self.verification_results.items()
            if k.startswith(level_name)
        }

        if not level_results:
            print(f"No verification results found for {level_name}")
            return

        all_match = True
        for bar_name, result in level_results.items():
            bar_display_name = bar_name.replace(f"{level_name}_", "")
            print(f"\n--- {bar_display_name} ---")

            if result.get("error"):
                print(f"❌ ERROR: {result['error']}")
                all_match = False
            elif result["properties_match"]:
                print("✅ ALL PROPERTIES MATCH")
            else:
                print("❌ PROPERTIES DO NOT MATCH")
                all_match = False
                for prop, diff in result["differences"].items():
                    if isinstance(diff["difference"], (int, float)):
                        print(
                            f"  {prop}: {diff['old']} vs {diff['new']} (diff: {diff['difference']:.2e})"
                        )
                    else:
                        print(
                            f"  {prop}: {diff['old']} vs {diff['new']} ({diff['difference']})"
                        )

            # Show values for debugging
            print(f"Old values: {result['old_values']}")
            print(f"New values: {result['new_values']}")

        print(f"\n{'='*60}")
        if all_match:
            print(f"✅ ALL BARS IN {level_name.upper()} MATCH PERFECTLY")
        else:
            print(f"❌ SOME BARS IN {level_name.upper()} DO NOT MATCH")
        print(f"{'='*60}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all verification results.

        Returns:
            Dictionary containing summary statistics
        """
        total_bars = len(self.verification_results)
        matching_bars = sum(
            1
            for result in self.verification_results.values()
            if result["properties_match"]
        )
        error_bars = sum(
            1 for result in self.verification_results.values() if result.get("error")
        )

        return {
            "total_bars": total_bars,
            "matching_bars": matching_bars,
            "error_bars": error_bars,
            "success_rate": matching_bars / total_bars if total_bars > 0 else 0,
        }


def test_verification_system():
    """Test the verification system with existing Bar class."""
    print("Testing verification system with existing Bar class...")

    verifier = BarRefactorVerifier()

    # Test 1: Simple bar creation
    def old_simple_bar():
        return Bar(x=0, y=0, length=2, angle=0, thickness=0.2)

    def new_simple_bar():
        return Bar(x=0, y=0, length=2, angle=0, thickness=0.2)

    result1 = verifier.verify_bar_creation(
        old_simple_bar, new_simple_bar, "test", "simple_bar"
    )

    # Test 2: Bar with endpoints
    def old_endpoint_bar():
        return Bar(x1=0, y1=0, x2=2, y2=0, thickness=0.2)

    def new_endpoint_bar():
        return Bar(x1=0, y1=0, x2=2, y2=0, thickness=0.2)

    result2 = verifier.verify_bar_creation(
        old_endpoint_bar, new_endpoint_bar, "test", "endpoint_bar"
    )

    # Test 3: Bar with angle
    def old_angled_bar():
        return Bar(x=1, y=1, length=2, angle=45, thickness=0.2)

    def new_angled_bar():
        return Bar(x=1, y=1, length=2, angle=45, thickness=0.2)

    result3 = verifier.verify_bar_creation(
        old_angled_bar, new_angled_bar, "test", "angled_bar"
    )

    # Print results
    verifier.print_verification_report("test")

    # Print summary
    summary = verifier.get_summary()
    print(f"\nVerification Summary:")
    print(f"Total bars: {summary['total_bars']}")
    print(f"Matching bars: {summary['matching_bars']}")
    print(f"Error bars: {summary['error_bars']}")
    print(f"Success rate: {summary['success_rate']:.1%}")

    return verifier


if __name__ == "__main__":
    test_verification_system()
