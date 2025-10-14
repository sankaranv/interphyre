# Trigonometric Analysis for Bar Class Refactoring

## Overview
This document analyzes all trigonometric calculations currently used in level design to identify patterns and design enhanced Bar class methods to eliminate them.

## Current Trigonometric Patterns

### 1. **Length Calculations from Angles**
**Pattern**: Calculate bar length needed to reach a specific distance at an angle
```python
# Examples:
ramp_length = ramp_offset / np.cos(np.radians(ramp_angle))
funnel_length = wall_distance / np.cos(np.radians(funnel_angle))
right_ramp_length = right_space * right_ramp_split / np.cos(np.radians(right_ramp_angle))
```

**Files**: `flagpole_sitta.py`, `the_funnel.py`, `the_fulcrum.py`, `pass_the_parcel.py`

### 2. **Position Calculations from Center + Angle + Length**
**Pattern**: Calculate bar center position from endpoints or constraints
```python
# Examples:
ramp_x = cannon_end_x + (ramp_length / 2 - 0.05) * np.cos(np.radians(ramp_angle))
ramp_y = cannon_end_y + (ramp_length / 2 - 0.05) * np.sin(np.radians(ramp_angle))
purple_wall_x = corner_point_x + np.cos(np.radians(purple_wall_angle)) * purple_wall_length / 2
purple_wall_y = corner_point_y + np.sin(np.radians(purple_wall_angle)) * purple_wall_length / 2
```

**Files**: `dive_bomb.py`, `wedge_issue.py`, `off_the_rails.py`

### 3. **Endpoint Calculations**
**Pattern**: Calculate bar endpoints from center position, angle, and length
```python
# Examples:
ramp_edge_x = right_ramp_x + (right_ramp_length / 2) * np.cos(np.radians(right_ramp_angle))
ramp_edge_y = right_ramp_y + (right_ramp_length / 2) * np.sin(np.radians(right_ramp_angle))
cannon_end_x = cannon_bottom.x + (cannon_length / 2) * np.cos(np.radians(cannon_angle))
cannon_end_y = cannon_bottom.y + (cannon_length / 2) * np.sin(np.radians(cannon_angle))
```

**Files**: `the_fulcrum.py`, `dive_bomb.py`

### 4. **Wall Intersection Calculations**
**Pattern**: Calculate where angled bars intersect with walls
```python
# Examples:
left_edge_y = -5 + np.abs(-5 - corner_point_x) * np.tan(np.radians(black_wall_angle))
basket_x = min((5 - basket_y) / np.tan(np.radians(black_wall_angle)) + 0.5, -4.25)
```

**Files**: `off_the_rails.py`

### 5. **Leg/Support Calculations**
**Pattern**: Calculate support structure positions using angles
```python
# Examples:
left_leg_bottom_x = left_leg_top_x - table_height / np.tan(angle_rad)
right_leg_bottom_x = right_leg_top_x + table_height / np.tan(angle_rad)
```

**Files**: `end_of_line.py`

### 6. **Offset Calculations**
**Pattern**: Calculate position offsets along angled directions
```python
# Examples:
green_ball_x_offset = 2 * green_ball_radius * np.cos(np.radians(black_wall_angle))
green_ball_y_offset = 2 * green_ball_radius * np.sin(np.radians(black_wall_angle))
```

**Files**: `off_the_rails.py`

## Proposed Enhanced Bar Class Methods

### 1. **Endpoint-Based Creation**
```python
@classmethod
def from_endpoints(cls, x1, y1, x2, y2, thickness=0.2, **kwargs):
    """Create bar connecting two points"""
    return cls(x1=x1, y1=y1, x2=x2, y2=y2, thickness=thickness, **kwargs)

@classmethod  
def from_point_and_angle(cls, x, y, angle, length, thickness=0.2, **kwargs):
    """Create bar from center point, angle, and length"""
    return cls(x=x, y=y, angle=angle, length=length, thickness=thickness, **kwargs)
```

### 2. **Wall-Touching Methods**
```python
@classmethod
def touching_wall(cls, wall_side, angle, offset=0, thickness=0.2, **kwargs):
    """Create bar that touches a specific wall at given angle"""
    # wall_side: 'left', 'right', 'top', 'bottom'
    # Calculate position and length to touch wall
    
@classmethod
def from_wall_to_point(cls, wall_side, target_x, target_y, angle, thickness=0.2, **kwargs):
    """Create bar from wall to specific point at angle"""
```

### 3. **Ramp/Inclined Surface Helpers**
```python
@classmethod
def ramp_from_corner(cls, corner_x, corner_y, angle, length, thickness=0.2, **kwargs):
    """Create ramp starting from corner point"""
    
@classmethod
def ramp_to_wall(cls, start_x, start_y, angle, wall_side, thickness=0.2, **kwargs):
    """Create ramp from point to wall at angle"""
```

### 4. **Geometric Constraint Methods**
```python
@classmethod
def connecting_points(cls, p1_x, p1_y, p2_x, p2_y, thickness=0.2, **kwargs):
    """Create bar connecting two points"""
    
@classmethod
def aligned_with(cls, other_bar, gap=0, thickness=0.2, **kwargs):
    """Create bar aligned with another bar with gap"""
```

### 5. **Support Structure Methods**
```python
@classmethod
def support_leg(cls, top_x, top_y, bottom_x, bottom_y, thickness=0.2, **kwargs):
    """Create support leg from top to bottom points"""
    
@classmethod
def angled_support(cls, base_x, base_y, angle, height, thickness=0.2, **kwargs):
    """Create angled support from base point"""
```

## Level Complexity Analysis

### **Simple Cases** (1-3 trig calculations):
- `staircase.py` - Basic positioning
- `cliffhanger.py` - Simple vertical bars
- `flagpole_sitta.py` - One ramp calculation

### **Medium Cases** (4-8 trig calculations):
- `the_funnel.py` - Funnel length calculation
- `wedge_issue.py` - Platform positioning
- `pass_the_parcel.py` - Ramp positioning

### **Complex Cases** (9+ trig calculations):
- `the_fulcrum.py` - Multiple ramps and beams
- `off_the_rails.py` - Wall intersections and offsets
- `dive_bomb.py` - Cannon positioning and extensions
- `end_of_line.py` - Table leg calculations

## Verification Strategy

For each level refactoring:

1. **Extract current calculations** - Identify all trig operations
2. **Calculate equivalent values** - Use old methods to get expected results
3. **Create new Bar objects** - Use enhanced methods
4. **Compare properties** - Verify x, y, angle, length, endpoints match
5. **Show comparison** - Display before/after values for user confirmation
6. **Proceed only after approval** - Wait for explicit user confirmation

## Implementation Priority

1. **Phase 1**: Implement core Bar class enhancements
2. **Phase 2**: Start with simple levels (staircase, cliffhanger)
3. **Phase 3**: Progress to medium complexity (funnel, wedge_issue)
4. **Phase 4**: Handle complex levels (fulcrum, off_the_rails, dive_bomb)
5. **Phase 5**: Clean up verification code and update documentation

## Benefits of Refactoring

✅ **Eliminate trigonometry** - No more `np.cos()`, `np.sin()`, `np.tan()` in level design
✅ **Intuitive positioning** - Clear, descriptive method names
✅ **Reduced errors** - Less manual calculation means fewer mistakes
✅ **Better maintainability** - Easier to understand and modify levels
✅ **Consistent patterns** - Standardized approaches across all levels
