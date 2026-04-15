#!/bin/bash
# Exhaustive sweep on the 6 small impossible seeds across keyhole, the_funnel,
# pass_the_parcel. For each seed: (1) 10000-attempt oracle run, (2) full 2D
# grid sweep to confirm genuine impossibility or find a solution.

set -euo pipefail
PROJECT=/work/pi_jensen_umass_edu/svaidyanatha_umass_edu/interphyre
OUTDIR=/scratch4/workspace/svaidyanatha_umass_edu-phyre/small_impossible_audit
mkdir -p "$OUTDIR"
mkdir -p /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs

sbatch \
    --job-name="small_imp_audit" \
    --partition=cpu-preempt \
    --account=pi_jensen_umass_edu \
    --cpus-per-task=8 \
    --mem=16G \
    --time=02:00:00 \
    --output="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/small_imp_audit_%j.out" \
    --error="/scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/small_imp_audit_%j.err" \
    --wrap="
        . $PROJECT/.venv/bin/activate
        cd $PROJECT
        python -u -c \"
import numpy as np
from interphyre.config import SimulationConfig
from interphyre.validation.oracles import get_solver, _run_attempt, Box2DEngine
from interphyre.levels import load_level

config = SimulationConfig()

TARGETS = {
    'keyhole':        [4873, 7322, 7445, 8360],
    'the_funnel':     [3324],
    'pass_the_parcel':[4846],
}

def oracle_sweep(level_name, seed, n_attempts=10000, oracle_steps=500):
    '''High-attempt oracle run.'''
    level = load_level(level_name, seed=seed)
    solver = get_solver(level_name)
    rng = np.random.default_rng(seed * 999983 + 7)
    sol = solver(level, config, n_attempts=n_attempts, oracle_steps=oracle_steps, rng=rng)
    return sol

def grid_sweep_keyhole(seed, n_x=60, n_y=80, oracle_steps=600):
    '''Grid sweep for keyhole: vary x offset and y placement.'''
    level = load_level('keyhole', seed=seed)
    engine = Box2DEngine(level=level, config=config)
    gb = level.objects['green_ball']
    rb = level.objects['red_ball']
    radius = rb.radius
    push_sign = -float(np.sign(gb.x))
    max_x_offset = min(0.6, abs(gb.x) - 0.2)
    max_x_offset = max(0.05, max_x_offset)
    xs = [gb.x - push_sign * off for off in np.linspace(0.02, max_x_offset, n_x)]
    ys = np.linspace(-4.3, gb.y - 0.1, n_y)
    for x in xs:
        for y in ys:
            x_c = float(np.clip(x, -4.5, 4.5))
            y_c = float(np.clip(y, -4.5, 4.5))
            if _run_attempt(engine, level, [(x_c, y_c, radius)], oracle_steps):
                return (x_c, y_c, radius)
    return None

def grid_sweep_funnel(seed, n_x=50, n_y=50, oracle_steps=500):
    '''Grid sweep for the_funnel: full board.'''
    level = load_level('the_funnel', seed=seed)
    engine = Box2DEngine(level=level, config=config)
    rb = level.objects['red_ball']
    radius = rb.radius
    for x in np.linspace(-4.5, 4.5, n_x):
        for y in np.linspace(-4.5, 4.5, n_y):
            if _run_attempt(engine, level, [(float(x), float(y), radius)], oracle_steps):
                return (float(x), float(y), radius)
    return None

def grid_sweep_parcel(seed, n_x=60, n_y=100, oracle_steps=500):
    '''Grid sweep for pass_the_parcel: fine y grid near basket rim.'''
    level = load_level('pass_the_parcel', seed=seed)
    engine = Box2DEngine(level=level, config=config)
    tb = level.objects['top_basket']
    rb = level.objects['red_ball']
    radius = rb.radius
    xs = np.linspace(float(np.clip(tb.x - 2.0, -4.5, 4.5)),
                     float(np.clip(tb.x + 3.0, -4.5, 4.5)), n_x)
    # Fine grid near rim: tb.y+0.0 to tb.y+2.0 (wider than oracle to catch edge cases)
    ys = np.linspace(float(np.clip(tb.y, -4.5, 4.5)),
                     float(np.clip(tb.y + 2.0, -4.5, 4.5)), n_y)
    for x in xs:
        for y in ys:
            if _run_attempt(engine, level, [(float(x), float(y), radius)], oracle_steps):
                return (float(x), float(y), radius)
    return None

results = {}

for level_name, seeds in TARGETS.items():
    print(f'\\n=== {level_name} ===')
    for seed in seeds:
        print(f'  Seed {seed}: running 10k-attempt oracle...', flush=True)
        sol = oracle_sweep(level_name, seed)
        if sol is not None:
            print(f'    FOUND by oracle: {sol}')
            results[f'{level_name}:{seed}'] = ('oracle', sol)
            continue

        print(f'    Oracle miss — running grid sweep...', flush=True)
        if level_name == 'keyhole':
            sol = grid_sweep_keyhole(seed)
        elif level_name == 'the_funnel':
            sol = grid_sweep_funnel(seed)
        else:
            sol = grid_sweep_parcel(seed)

        if sol is not None:
            print(f'    FOUND by grid: {sol}')
            results[f'{level_name}:{seed}'] = ('grid', sol)
        else:
            print(f'    GENUINELY IMPOSSIBLE — no solution found in exhaustive sweep')
            results[f'{level_name}:{seed}'] = ('impossible', None)

print('\\n=== SUMMARY ===')
for key, (method, sol) in results.items():
    status = f'FOUND ({method}): {sol}' if sol else 'GENUINELY IMPOSSIBLE'
    print(f'  {key}: {status}')

found = sum(1 for m, s in results.values() if s is not None)
impossible = sum(1 for m, s in results.values() if s is None)
print(f'\\nFound: {found}, Genuinely impossible: {impossible}')
\"
    "

echo "Submitted small impossible seed audit. Monitor: squeue -u \$USER"
echo "Log: /scratch4/workspace/svaidyanatha_umass_edu-phyre/logs/small_imp_audit_*.out"
