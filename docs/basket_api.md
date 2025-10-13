# Basket API Reference

## Overview

The `Basket` class creates U-shaped containers (baskets/jars) with configurable dimensions. The refactored API makes it easy to specify exact basket dimensions without trigonometry, while maintaining backwards compatibility with the old `scale` parameter.

## Quick Start

```python
from interphyre.objects import Basket

# Method 1: Explicit dimensions (recommended)
basket = Basket(
    x=0, y=-3,
    bottom_width=2.0,
    top_width=2.5,
    height=3.0,
    color="gray",
    dynamic=False
)

# Method 2: Using scale (backwards compatible)
basket = Basket(
    x=0, y=-3,
    scale=1.5,
    color="gray",
    dynamic=False
)

# Method 3: Using flare ratio (convenience)
basket = Basket.from_width_and_flare(
    x=0, y=-3,
    bottom_width=2.0,
    flare_ratio=1.2,  # top is 20% wider
    height=3.0,
    color="gray",
    dynamic=False
)
```

## Parameters

### Geometry (Primary)

- **`bottom_width`** (float, optional): Interior width at the bottom of the basket
- **`top_width`** (float, optional): Interior width at the top of the basket
- **`height`** (float, optional): Interior height of the basket

If not specified, these default to reasonable values (2.0, 2.2, 3.0 respectively).

### Convenience Sizing

- **`scale`** (float, optional): Convenience parameter that sets all dimensions proportionally
  - When provided, uses default proportions: bottom_width = 1.083 × scale, height = 1.67 × scale
  - Maintains backwards compatibility with older code

### Wall Dimensions

- **`wall_thickness`** (float, default=0.15): Thickness of the side walls
- **`floor_thickness`** (float, default=None): Thickness of the floor
  - If `None`, automatically matches `wall_thickness` for consistent appearance

### Positioning

- **`x`** (float, required): X-coordinate of the anchor point
- **`y`** (float, required): Y-coordinate of the anchor point
- **`anchor`** (str, default="bottom_center"): Where (x, y) refers to
  - Options: `"bottom_center"`, `"center"`, `"top_center"`, `"bottom_left"`, `"bottom_right"`, `"top_left"`, `"top_right"`
- **`angle`** (float, default=0.0): Rotation angle in degrees

### Physics

- **`dynamic`** (bool, default=True): Whether the basket can move
- **`friction`** (float, default=0.5): Surface friction
- **`restitution`** (float, default=0.5): Bounciness

### Anti-Tunneling Options

- **`double_walls`** (bool, default=False): Create double-layer walls to prevent fast objects from passing through
- **`segmented_walls`** (bool, default=False): Split walls into segments for better collision detection (planned feature)

### Success Detection

- **`enable_sensor`** (bool, default=True): Create an interior sensor fixture for reliable containment detection
- **`sensor_margin`** (float, default=0.05): Gap between sensor and inner walls
- **`sensor_height_ratio`** (float, default=0.3): Sensor covers lower 30% of interior height

## Geometry Details

### Flare

The "flare" is how much the basket widens from bottom to top:

```
    /‾‾‾‾‾‾‾‾‾‾‾\     ← top_width (wider)
   /            \
  |              |
  |              |     ← flared walls
   \            /
    |__________|       ← bottom_width (narrower)
```

- `flare_ratio = top_width / bottom_width`
- `flare_ratio = 1.0` → straight walls
- `flare_ratio > 1.0` → outward flare (typical basket)
- `flare_ratio < 1.0` → inward taper (funnel shape)

### Anchor Points

The `anchor` parameter determines what `(x, y)` refers to:

```
top_left ●━━━━━━━━━━━━━● top_right
         ┃  top_center ┃
         ┃      ●      ┃
         ┃             ┃
         ┃   center ●  ┃
         ┃             ┃
         ┃ ┌─────────┐ ┃
btm_left ● │  btm_ctr │ ● btm_right
           │    ●     │
           └──────────┘
```

**Default**: `bottom_center` - most intuitive for placing baskets on surfaces.

## Convenience Methods

### `Basket.from_width_and_flare()`

Create a basket using bottom width and a flare ratio:

```python
basket = Basket.from_width_and_flare(
    x=0, y=-3,
    bottom_width=2.0,
    flare_ratio=1.3,    # top is 30% wider
    height=3.0,
    **kwargs            # other parameters
)
```

Equivalent to:
```python
basket = Basket(
    x=0, y=-3,
    bottom_width=2.0,
    top_width=2.6,      # 2.0 * 1.3
    height=3.0,
    **kwargs
)
```

## Properties

### Read-Only Dimensions

- **`interior_bottom_width`**: Interior width at bottom
- **`interior_top_width`**: Interior width at top
- **`interior_height`**: Interior height
- **`total_width`**: Total width including walls (at bottom)
- **`total_height`**: Total height including floor

### Methods

- **`get_anchor_offset()`**: Returns `(dx, dy)` offset from bottom-center to the anchor point

## Success Detection

### Using the Sensor (Recommended)

When `enable_sensor=True` (default), a sensor fixture is created inside the basket. Use it for reliable success detection:

```python
def success_condition(engine):
    # Check if ball is in the basket sensor
    return engine.is_in_basket_sensor("basket", "green_ball")
```

### Using Contact Detection (Legacy)

You can still use wall contact detection, but it's less reliable due to tunneling:

```python
def success_condition(engine):
    success_time = engine.config.default_success_time
    return engine.is_in_contact_for_duration("green_ball", "basket", success_time)
```

## Examples

### Example 1: Simple Basket on Ground

```python
from interphyre.objects import Basket, Ball, Bar
from interphyre.render import MIN_X, MAX_X, MIN_Y

# Ground
ground = Bar(left=MIN_X, right=MAX_X, y=MIN_Y + 0.1, color="black", dynamic=False)

# Basket sitting on ground
basket = Basket(
    x=0,
    y=ground.y + 0.1,  # Just above ground
    bottom_width=2.0,
    top_width=2.4,
    height=2.5,
    anchor="bottom_center",
    color="gray",
    dynamic=False
)

# Ball to catch
ball = Ball(x=0, y=3, radius=0.3, color="green", dynamic=True)
```

### Example 2: Upside-Down Basket (Cover/Trap)

```python
# Upside-down basket at top
basket = Basket(
    x=0,
    y=4,
    bottom_width=2.0,
    top_width=2.4,
    height=2.0,
    angle=180,          # Flip upside down
    anchor="top_center", # Position by top
    color="blue",
    dynamic=True
)
```

### Example 3: Anti-Tunneling for Fast Objects

```python
# Basket with double walls to catch fast-moving small balls
basket = Basket(
    x=0,
    y=-3,
    bottom_width=1.5,
    top_width=2.0,
    height=2.5,
    double_walls=True,   # Prevent tunneling
    enable_sensor=True,   # Reliable detection
    color="gray",
    dynamic=False
)

# Small fast ball
ball = Ball(x=0, y=5, radius=0.2, color="red", dynamic=True)

def success_condition(engine):
    # Use sensor for reliable detection
    return engine.is_in_basket_sensor("basket", "ball")
```

### Example 4: Varying Basket Sizes

```python
# Small basket
small_basket = Basket.from_width_and_flare(
    x=-4, y=-3,
    bottom_width=1.0,
    flare_ratio=1.2,
    height=1.5,
    color="blue"
)

# Medium basket
medium_basket = Basket(x=0, y=-3, scale=1.0, color="gray")

# Large basket
large_basket = Basket.from_width_and_flare(
    x=4, y=-3,
    bottom_width=2.5,
    flare_ratio=1.3,
    height=3.5,
    color="purple"
)
```

## Migration Guide

### From Old Scale-Based API

**Old code (still works!):**
```python
basket = Basket(x=0, y=0, scale=1.5, color="gray")
```

**New equivalent with explicit dimensions:**
```python
basket = Basket(
    x=0, y=0,
    bottom_width=1.625,  # 1.083 * 1.5
    top_width=2.031,     # 1.083 * 1.5 * 1.25
    height=2.505,        # 1.67 * 1.5
    color="gray"
)
```

**Or use the convenience method:**
```python
basket = Basket.from_width_and_flare(
    x=0, y=0,
    bottom_width=1.625,
    flare_ratio=1.25,
    height=2.505,
    color="gray"
)
```

### Updating Success Conditions

**Old (contact-based):**
```python
def success_condition(engine):
    return engine.is_in_contact_for_duration("ball", "basket", 0.5)
```

**New (sensor-based, more reliable):**
```python
def success_condition(engine):
    return engine.is_in_basket_sensor("basket", "ball")
```

## Benefits of the Refactor

✅ **No Trigonometry Required**: Specify dimensions directly, no need for `np.tan()`, `np.sin()`, etc.

✅ **Intuitive Placement**: Anchor-based positioning makes it clear where the basket will appear

✅ **Consistent Appearance**: Uniform thickness across all parts, predictable sizing

✅ **Reliable Success Detection**: Built-in sensor fixtures prevent tunneling issues

✅ **Backwards Compatible**: Old `scale`-based code continues to work

✅ **Flexible**: Easy to create baskets of any size and shape

## Troubleshooting

### Basket looks wrong visually

- Check that `floor_thickness` matches `wall_thickness` for consistent appearance
- Verify `anchor` is set correctly for your positioning needs

### Ball tunneling through basket walls

- Set `double_walls=True` to add an inner wall layer
- Ensure `wall_thickness` is adequate (>= 0.15 recommended)
- Use smaller time steps if objects are very fast

### Success detection not working

- Use `engine.is_in_basket_sensor()` instead of contact detection
- Ensure `enable_sensor=True` (default)
- Check that the basket and ball names match exactly

### Basket too small/large for balls

- Calculate appropriate dimensions:
  - `bottom_width` should be at least `3 * ball_radius`
  - `height` should be at least `2 * ball_radius`

## See Also

- [Objects API Reference](./objects.md)
- [Level Creation Guide](./level_creation.md)
- [Physics Engine Documentation](./engine.md)

