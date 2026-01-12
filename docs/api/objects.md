# Objects

Objects live under `interphyre/objects` and are converted into Box2D bodies by helper functions.

## PhyreObject

Base class for all physics objects. Provides shared physical properties like `friction`, `restitution`, and `density`.

## Ball

Circular object with `radius`. Use `create_ball(world, ball, name, use_ccd=False)` to create a Box2D body.

## Bar

Rectangular bar with flexible initialization patterns (center, endpoints, or bounds). Use `create_bar(world, bar, name, use_ccd=False)`.

## Basket

U-shaped container with configurable dimensions and anchor point. Use `create_basket(world, basket, name, use_ccd=False)`.

## Walls

`create_walls(world, wall_thickness, room_width, room_height)` builds static boundary walls and returns `(left, right, top, bottom)`.
