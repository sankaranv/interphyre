# interphyre
interphyre is an implementation of the PHYRE simulator with user-editable levels and interventions for causal inference research.

## Features currently implemented

- Gym interface with arbitrary number of action objects
- Build environment from JSON file
- Success detection: collision between target and action objects
- Box2D primitives: Basket, Ball, Bar
- Pygame rendering
- Randomized level generation from starter config

## TODO

- Convert or rebuild all PHYRE levels as JSON
- Assigning starting state
- Load physics parameters (e.g. gravity, restitution, friction) from config
- Check for valid environment (e.g. intersections between objects)
- Filter out invalid actions (e.g. intersections between objects)
- Interventions: adding, nulling, and moving objects, changing between static and dynamic, changing color
- Mid-trajectory interventions (requires validity checks)

- GUI level editor
