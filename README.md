# phyre2
PHYRE2 is an implementation of the PHYRE simulator with user-editable levels and interventions for causal inference research.

## Features currently implemented

- Gym interface with arbitrary number of action objects
- Build environment from JSON file
- Success detection: collision between target and action objects
- Box2D primitives: Basket, Ball, Platform
- Pygame rendering

## TODO

- Load physics parameters (e.g. gravity, restitution, friction) from config
- Check for valid environment (e.g. intersections between objects)
- Filter out invalid actions (e.g. intersections between objects)
- GUI level editor
- Implement all interventions: adding, nulling, and moving objects, changing between static and dynamic, changing color
- Mid-trajectory interventions
- Randomized level generation from starter config (requires validity checks)
- Convert or rebuild all PHYRE levels as JSON
