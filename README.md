# interphyre
interphyre is an implementation of the PHYRE simulator with user-editable levels and interventions for causal inference research.

## Features currently implemented

- Gym interface with arbitrary number of action objects
- Build environment from JSON file
- Success detection: collision between target and action objects
- Box2D primitives: Basket, Ball, Bar
- Pygame rendering
- Randomized level generation from starter config
- **Solutions system** - Generate, test, and visualize solutions for levels

## Quick Start

Usage
-----

To generate solutions:

    python tools/generate_solutions.py [options]

To visualize solutions:

    python tools/demo.py --mode solutions [--level LEVEL]

To test solutions (CI-friendly, no rendering):

    python tests/test_solutions.py [options]

## Project Structure

```
interphyre/
├── interphyre/              # Core library
│   ├── levels/             # Level definitions
│   ├── environment.py      # Gym environment
│   ├── engine.py           # Physics engine
│   └── ...
├── tools/                  # Solution tools
│   ├── generate_solutions.py    # Solution generator
│   ├── test_solutions.py        # Test runner
│   ├── demo.py                  # Visualization tool
│   ├── solutions.json           # Solutions database
│   └── SOLUTIONS_README.md      # Detailed documentation
├── tests/                  # Unit tests
├── generate_solutions.py   # Launcher script
├── test_solutions.py       # Launcher script
├── demo.py                 # Launcher script
└── README.md               # This file
```

## TODO

- Convert or rebuild all PHYRE levels as JSON
- Assigning starting state
- Load physics parameters (e.g. gravity, restitution, friction) from config
- Check for valid environment (e.g. intersections between objects)
- Filter out invalid actions (e.g. intersections between objects)
- Interventions: adding, nulling, and moving objects, changing between static and dynamic, changing color
- Mid-trajectory interventions (requires validity checks)
- GUI level editor

For detailed information about the solutions system, see `tools/SOLUTIONS_README.md`.
