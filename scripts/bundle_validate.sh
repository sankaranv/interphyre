#!/usr/bin/env bash
# Run bundle validation inside a Linux container.
#
# Box2D physics is not identical between macOS (Apple Clang + libm) and Linux
# (GCC + glibc). Bundles were generated on Linux x86_64, so validation must
# run on the same platform to get consistent float results. This script wraps
# pytest in an official Python 3.11 Linux image, which is identical to the
# cluster environment. CI (GitHub Actions Linux runners) can run the tests
# directly without this script.
#
# Usage:
#   ./scripts/bundle_validate.sh                          # all 25 levels
#   ./scripts/bundle_validate.sh -k test_catapult        # single level
#   ./scripts/bundle_validate.sh -k "catapult or seesaw" # multiple levels
set -euo pipefail

EXTRA_ARGS=("$@")

docker run --rm \
    -v "$(pwd)":/app \
    -w /app \
    python:3.11-slim \
    bash -c "pip install -e '.[dev]' -q && python -m pytest tests/test_bundle_solutions.py -m bundle_validation ${EXTRA_ARGS[*]+"${EXTRA_ARGS[*]}"}"
