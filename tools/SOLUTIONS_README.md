# Interphyre Solutions System

This document describes the cleaned-up solutions system for Interphyre.

## Overview

The codebase has been cleaned up and organized into a comprehensive solutions system with four main components:

1. **Solution Generator** (`generate_solutions.py`) - Generates solutions for levels and seeds
2. **Solutions File** (`solutions.json`) - Stores all generated solutions
3. **Test Runner** (`test_solutions.py`) - Tests solutions without rendering (CI/CD friendly)
4. **Visualization Tool** (`demo.py`) - Visualizes solutions with pygame rendering

## Files

### Core Files

- `generate_solutions.py` - Solution generator with level-specific algorithms
- `test_solutions.py` - Test runner for CI/CD (no pygame)
- `demo.py` - Visualization tool (refactored from original demo)
- `solutions.json` - Solutions database

### Cleaned Up

- Removed excess debug files (`debug_catapult.py`, `debug_contact.py`)
- Removed temporary solution files
- Removed redundant visualization scripts
- Consolidated visualization into `demo.py`

## Usage

### 1. Generate Solutions

```bash
# Generate solutions for first 5 levels with 10 seeds each
python generate_solutions.py --levels basket_case catapult cliffhanger dive_bomb down_to_earth --seeds 42 123 456 789 999 111 222 333 444 555 --output solutions.json --max-trials 500 --verbose

# Generate solutions for all levels (default: first 5)
python generate_solutions.py --output solutions.json

# List all available levels
python generate_solutions.py --list-levels
```

### 2. Test Solutions

```bash
# Test all solutions without rendering (CI/CD friendly)
python test_solutions.py --solutions solutions.json --verbose

# Test with limited number of tests
python test_solutions.py --solutions solutions.json --max-tests 10

# Save detailed results
python test_solutions.py --solutions solutions.json --output test_results.json
```

### 3. Visualize Solutions

```bash
# Visualize all solutions from file
python demo.py --mode solutions --solutions solutions.json --pause 2.0

# Visualize a single solution
python demo.py --mode single --level basket_case --seed 42 --pause 1.0

# Original random demo mode
python demo.py --mode random --task basket_case --max-trials 10
```

## Solution Generation

The solution generator includes specialized algorithms for different levels:

- **basket_case**: Targets basket rim with grid search
- **catapult**: Targets gray bar end with size/position search
- **cliffhanger**: Targets green bar top with grid search
- **dive_bomb**: Generic search around cannon area
- **Generic**: Relative positioning to action objects

Each algorithm uses a configurable `max_trials` parameter to limit search time.

## Current Status

- **34/50 solutions found** (68% success rate)
- **22/34 solutions pass tests** (64.7% test success rate)
- **Level performance**:
  - basket_case: 10/10 (100%)
  - catapult: 1/10 (10%) - needs improvement
  - cliffhanger: 6/8 (75%)
  - dive_bomb: 4/5 (80%)
  - down_to_earth: 1/1 (100%)

## Next Steps

1. **Improve catapult solutions** - Current algorithm needs refinement
2. **Add more levels** - Extend to all 26 levels
3. **Optimize search algorithms** - Better heuristics for difficult levels
4. **Add solution validation** - Ensure solutions are robust across different seeds

## File Structure

```
interphyre/
├── generate_solutions.py    # Solution generator
├── test_solutions.py        # Test runner (no pygame)
├── demo.py                  # Visualization tool
├── solutions.json           # Solutions database
├── SOLUTIONS_README.md      # This file
└── interphyre/             # Core library
    ├── levels/             # Level definitions
    ├── environment.py      # Gym environment
    ├── engine.py           # Physics engine
    └── ...
```

The codebase is now clean, organized, and ready for further development! 