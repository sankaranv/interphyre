# Interphyre Test Suite

Comprehensive test suite for the Interphyre physics simulator with 100% coverage of critical modules.

## Quick Start

```bash
# Run fast unit tests (for PRs and development)
pytest -m fast

# Run all tests including slow comprehensive tests
pytest

# Run specific test file
pytest tests/test_renderers.py -v

# Run with coverage
pytest --cov=interphyre --cov-report=term-missing
```

## Test Organization

### Core Functionality Tests (181 tests)

High-quality tests with 95-100% coverage of core simulator components.

#### Rendering System (57 tests)
**File**: `test_renderers.py`
- **Coverage**: 100% (OpenCV and Pygame renderers)
- **Tests**: Coordinate transforms, color mapping, rendering pipelines, mocking
- **Key Features**: No GUI required (fully mocked Pygame)

#### Object System (58 tests)
**File**: `test_objects.py`
- **Coverage**: 95-100% (Ball, Bar, Basket, Walls)
- **Tests**: Factory methods, property synchronization, physics creation
- **Key Features**: All 8 Bar factory methods, 8 Basket anchor types

#### Experiments & Interventions (37 tests)
**File**: `test_experiments.py`
- **Coverage**: 100% (causal inference, counterfactuals)
- **Tests**: FactualCounterfactualPair, ExperimentResults, ablation studies
- **Key Features**: Deterministic seeding, causal effect calculation

#### State Serialization (29 tests)
**File**: `test_serialization.py`
- **Coverage**: 98% (Box2D world/body serialization)
- **Tests**: Snapshot capture/restore, determinism, round-trip validation
- **Key Features**: Immutable snapshots, contact preservation

### Engine & Environment Tests (58 tests)

#### Engine (28 tests)
**File**: `test_engine.py`
- Core Box2D engine functionality
- Physics stepping, collision detection, success conditions

#### Environment (28 tests)
**File**: `test_environment_additional.py`
- Discrete/continuous actions, action spaces
- Invalid configurations, rendering hooks
- Verbose output, simulation control
- **Note**: Merged `test_environment_misc.py` (2 tests) into this file

#### Environment Validation (4 tests)
**File**: `test_environment_validation.py`
- Input validation and error handling

### Quality & Validation Tests (73 tests)

#### Solution Validation (55 tests)
**File**: `test_solution_validation.py`
- **Purpose**: Regression testing for level solutions
- **Data Files**: `solutions/successes.json`, `solutions/failures.json`
- **Note**: Currently uses placeholder solutions - populate with actual working/failing solutions
- **Usage**: Ensures level changes don't break expected outcomes

#### API Quality (13 tests)
**File**: `test_api_quality.py`
- API consistency and contract validation
- Function signatures, return types

#### Determinism (4 tests)
**File**: `test_determinism.py`
- Physics reproducibility with same seeds
- Critical for research and debugging

#### Edge Cases (5 tests)
**File**: `test_edge_cases.py`
- Boundary conditions and corner cases

### Performance Tests (16 tests)

#### Fast Performance (11 tests)
**File**: `test_performance.py`
- **Marker**: `@pytest.mark.fast`
- Config system, profiling, contact tracking
- Runs in CI on every PR

#### Comprehensive Benchmarks (5 tests)
**File**: `test_benchmark_performance.py`
- **Marker**: `@pytest.mark.comprehensive`
- Real-world scenarios, memory tracking, CPU profiling
- Uses psutil for system metrics
- Runs in nightly/comprehensive CI only

### Level Testing (3 tests)

#### All Levels Smoke Tests
**File**: `test_all_levels.py`
- **Marker**: `@pytest.mark.comprehensive`
- Tests all 25+ levels for loading/simulation
- Metadata consistency validation
- Useful for catching level-specific bugs

### Utility Files

#### Configuration
- **`conftest.py`**: Shared fixtures (simple_env, intervention_config, etc.)
- **`pytest.ini`**: Test markers and configuration
- **`__init__.py`**: Package initialization

#### Documentation
- **`README.md`** (this file): Test suite overview
- **`DEPRECATED_FILES.md`**: Archived test files and rationale
- **`_archive/README.md`**: Details on archived directories

#### Data Files
- **`solutions/successes.json`**: Expected successful solutions (6 levels, 52 cases)
- **`solutions/failures.json`**: Expected failing solutions (populate as needed)

## Test Markers

Tests are organized using pytest markers for selective execution:

```python
@pytest.mark.fast              # Fast unit tests (~0.5s total)
@pytest.mark.comprehensive     # Slow comprehensive tests (~5-10s total)
@pytest.mark.intervention      # Tests requiring intervention features
```

### Running Tests by Marker

```bash
# Fast tests only (CI on every PR)
pytest -m fast                    # 259 tests, ~0.6s

# Comprehensive tests only
pytest -m comprehensive           # 32 tests, ~5s

# Fast + Comprehensive (nightly CI)
pytest -m "fast or comprehensive" # 291 tests

# Intervention tests
pytest -m intervention            # Subset of fast tests
```

## Test Metrics

### Current Status (as of 2026-01-09)

| Category | Tests | Status |
|----------|-------|--------|
| **Total Tests** | 431 | ✅ 376 passing |
| **Fast Tests** | 259 | ✅ All passing |
| **Comprehensive Tests** | 32 | ✅ All passing |
| **Solution Validation** | 55 | ⚠️ Placeholder data |
| **Execution Time (fast)** | ~0.6s | ✅ Fast |
| **Execution Time (all)** | ~5s | ✅ Reasonable |

### Coverage

| Module | Coverage | Tests |
|--------|----------|-------|
| **interphyre.render** | 100% | 57 |
| **interphyre.objects** | 95-100% | 58 |
| **interphyre.interventions.experiments** | 100% | 37 |
| **interphyre.interventions.serialization** | 98% | 29 |
| **Overall (tested modules)** | 80%+ | 431 |

## Archived Files

The `_archive/` directory contains deprecated test files:

- **`interventions_old/`**: Old intervention tests (replaced by test_experiments.py and test_serialization.py)
- **`test_levels/`**: Solution generation scripts (not pytest tests)
- **`data/`**: Old solution data format

See `_archive/README.md` for full details.

## CI/CD Integration

### Recommended Pipeline

```yaml
# Pull Request Checks (Fast)
pr-check:
  script:
    - pytest -m fast --cov=interphyre --cov-report=term-missing
  time: ~30-60 seconds

# Nightly Comprehensive Tests
nightly:
  script:
    - pytest -m "fast or comprehensive" --cov=interphyre
  time: ~5-10 minutes

# Release Tests (Full Suite)
release:
  script:
    - pytest --cov=interphyre --cov-report=html
  time: ~10-15 minutes
```

## Adding New Tests

### Guidelines

1. **Use appropriate markers**:
   ```python
   @pytest.mark.fast  # For unit tests <0.1s each
   @pytest.mark.comprehensive  # For slow/integration tests
   ```

2. **Follow naming conventions**:
   - Test files: `test_<module>.py`
   - Test functions: `test_<feature>_<scenario>()`
   - Be descriptive but concise

3. **Use existing fixtures** (see `conftest.py`):
   - `simple_env`: Basic two-body environment
   - `intervention_env`: Environment with interventions enabled
   - `intervention_config`: SimulationConfig with interventions

4. **Organize by feature**, not by speed:
   ```python
   # ============================================================================
   # Feature Category Tests (N tests)
   # ============================================================================

   @pytest.mark.fast
   def test_feature_basic():
       """Test basic functionality."""
       pass
   ```

5. **Keep tests focused**: One concept per test

6. **Use descriptive assertions**:
   ```python
   assert result == expected, f"Expected {expected}, got {result}"
   ```

## Troubleshooting

### Tests are slow
- Run only fast tests: `pytest -m fast`
- Run specific file: `pytest tests/test_renderers.py`
- Use `-x` to stop at first failure

### Import errors
- Ensure you're in the project root
- Check that `interphyre` is installed: `pip install -e .`

### Pygame tests fail
- Pygame tests are fully mocked - no GUI required
- If issues persist, check `test_renderers.py` mock_pygame fixture

### Solution validation tests fail
- `solutions/successes.json` and `solutions/failures.json` contain placeholder data
- Populate with actual working/failing solutions
- Or skip: `pytest --ignore=tests/test_solution_validation.py`

## Contributing

When adding new functionality:

1. Write tests first (TDD)
2. Aim for 95%+ coverage on new code
3. Run fast tests before committing: `pytest -m fast`
4. Update this README if adding new test categories

## Questions?

- Check `DEPRECATED_FILES.md` for archived test rationale
- Check `_archive/README.md` for details on archived code
- See pytest docs: https://docs.pytest.org/
