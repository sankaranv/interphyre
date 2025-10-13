# Basket Refactor Summary

## What Changed?

The `Basket` class has been refactored to be more intuitive and feature-rich while maintaining backwards compatibility.

### Key Improvements

1. **✅ Explicit Dimensions**: Specify `bottom_width`, `top_width`, and `height` directly
2. **✅ No Trigonometry**: No more `np.tan()`, `np.sin()`, etc. in level code
3. **✅ Anchor-Based Positioning**: Clear, predictable placement using anchor points
4. **✅ Consistent Appearance**: Unified thickness across floor and walls
5. **✅ Built-In Sensors**: Reliable success detection without tunneling issues
6. **✅ Anti-Tunneling Options**: `double_walls` parameter for extra collision safety
7. **✅ Backwards Compatible**: Old `scale` parameter still works

## What Still Works?

All existing code using `scale` continues to work unchanged:

```python
# This still works exactly as before
basket = Basket(x=0, y=0, scale=1.5, color="gray")
```

## New Recommended Usage

### Basic Usage

```python
# Before: Using scale (still works, but less intuitive)
basket_scale = 1.2
basket = Basket(
    x=0,
    y=-3,
    scale=basket_scale,
    color="gray"
)

# After: Explicit dimensions (recommended)
basket = Basket(
    x=0,
    y=-3,
    bottom_width=2.0,
    top_width=2.4,
    height=2.5,
    color="gray"
)

# Or use the convenience method
basket = Basket.from_width_and_flare(
    x=0,
    y=-3,
    bottom_width=2.0,
    flare_ratio=1.2,  # top is 20% wider than bottom
    height=2.5,
    color="gray"
)
```

### Positioning Examples

```python
# Place basket ON the ground (bottom touching)
ground_y = -4.9
basket = Basket(
    x=0,
    y=ground_y,  # y refers to bottom by default
    bottom_width=2.0,
    top_width=2.4,
    height=2.5,
    anchor="bottom_center",  # default
    color="gray"
)

# Hang basket from ceiling (top touching)
ceiling_y = 4.5
basket = Basket(
    x=0,
    y=ceiling_y,  # y refers to top
    bottom_width=2.0,
    top_width=2.4,
    height=2.5,
    angle=180,           # flip upside down
    anchor="top_center",
    color="gray"
)
```

## Migrating Levels

### Example: Before and After

**Before (with trigonometry):**

```python
import numpy as np

basket_scale = rng.uniform(0.8, 1.5)
basket_height = 1.67 * basket_scale
basket_width = 1.083 * basket_scale + 2 * basket_height * np.tan(np.radians(5))

basket_x = rng.uniform(-4.5 + basket_scale, 4.5 - basket_scale)
basket_y = ground.y + basket_scale + rng.uniform(0, 1)

basket = Basket(
    x=basket_x,
    y=basket_y,
    scale=basket_scale,
    color="gray"
)
```

**After (no trigonometry):**

```python
# Define basket dimensions directly
bottom_width = rng.uniform(1.5, 2.5)
top_width = bottom_width * rng.uniform(1.1, 1.3)  # 10-30% flare
height = bottom_width * rng.uniform(1.2, 1.8)     # aspect ratio

# Calculate placement bounds
basket_x = rng.uniform(-4.5 + top_width/2, 4.5 - top_width/2)
basket_y = ground.y + height * rng.uniform(0, 0.5)

basket = Basket(
    x=basket_x,
    y=basket_y,
    bottom_width=bottom_width,
    top_width=top_width,
    height=height,
    anchor="bottom_center",
    color="gray"
)

# Or even simpler
basket = Basket.from_width_and_flare(
    x=basket_x,
    y=basket_y,
    bottom_width=rng.uniform(1.5, 2.5),
    flare_ratio=rng.uniform(1.1, 1.3),
    color="gray"
)
```

### Success Detection Migration

**Before (contact-based, tunneling issues):**

```python
def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "basket", success_time)
```

**After (sensor-based, reliable):**

```python
def success_condition(engine):
    # More reliable, no tunneling
    return engine.is_in_basket_sensor("basket", "green_ball")
```

## Testing

Comprehensive tests confirm:

- ✅ Backwards compatibility (scale parameter)
- ✅ Explicit dimensions work correctly
- ✅ Flare ratio convenience method
- ✅ Anchor positioning
- ✅ Thickness consistency
- ✅ Sensor creation and detection
- ✅ Double walls for anti-tunneling
- ✅ Visual appearance across sizes

Run tests:

```bash
# Feature tests
python tools/test_basket_features.py

# Visual comparison
python tools/basket_visual_demo.py

# Test a specific level
python tools/demo.py --level basket_case --seed 42
```

## Current Status

### Completed ✅

1. New API design with explicit dimensions
2. Backwards-compatible `scale` parameter
3. Anchor-based positioning system
4. Geometry builder without trigonometry
5. Interior sensor fixtures
6. Anti-tunneling double walls
7. Consistent thickness (floor matches walls)
8. Comprehensive test suite
9. Visual demos and verification
10. Complete documentation

### Already Using Sensors ✅

- `staircase.py` - already uses `is_in_basket_sensor()`

### Using Basket (Scale-Based) ✅

These levels use baskets with the old `scale` parameter and still work:

- `basket_case.py`
- `catapult.py`
- `falling_into_place.py`
- `the_fulcrum.py`
- `off_the_rails.py`
- `pass_the_parcel.py`
- `tipping_point.py`
- `just_a_nudge.py`

### Optional Future Work

- Migrate existing levels to use explicit dimensions (not required, optional improvement)
- Add helper functions for common basket configurations
- Performance optimization if needed

## Questions?

See the [full API documentation](docs/basket_api.md) for detailed examples and reference.

## Breaking Changes

**None!** All existing code continues to work.

## Git Branch

This refactor is on branch: `refactor/basket-design`

When ready to merge, ensure:
1. All tests pass
2. Existing levels still work
3. Documentation is reviewed
4. No regressions in physics behavior

